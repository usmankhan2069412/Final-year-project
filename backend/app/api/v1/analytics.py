import csv
import io
import uuid
from datetime import datetime, date, timedelta
from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_tenant_db, get_current_org_id
from app.models.analytics import AnalyticsDaily, AnalyticsByChannel, AnalyticsByLang
from app.models.chatbot import Chatbot
from app.models.persona import Persona
from app.models.conversation import Conversation, ConversationStatus, Message
from app.schemas.analytics import KPIResponse, VolumeSeriesItem, LanguageMixItem, ChannelPerfItem, InteractionItem
from app.services.report_export import build_simple_pdf

router = APIRouter()


def _format_duration(seconds: Optional[int]) -> str:
    if seconds is None or seconds < 0:
        return "-"
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        hours = minutes // 60
        rem_mins = minutes % 60
        return f"{hours}h {rem_mins}m" if rem_mins else f"{hours}h"
    return f"{minutes}m"


def _parse_status_filter(status: Optional[str]) -> Optional[ConversationStatus]:
    if not status:
        return None

    normalized = status.strip().lower()
    try:
        return ConversationStatus(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid conversation status filter.") from exc


def _get_interactions(
    db: Session,
    org_id: uuid.UUID,
    days: int,
    status: Optional[ConversationStatus] = None,
    chatbot_id: Optional[uuid.UUID] = None,
    limit: Optional[int] = 50,
):
    start_date = datetime.utcnow() - timedelta(days=days)

    msg_agg = (
        db.query(
            Message.conversation_id,
            func.count(Message.id).label("msg_count"),
            func.max(Message.created_at).label("last_msg_at"),
        )
        .group_by(Message.conversation_id)
        .subquery()
    )

    q = (
        db.query(
            Conversation.id,
            Conversation.chatbot_id,
            Persona.name.label("chatbot_name"),
            Conversation.status,
            Conversation.started_at,
            func.coalesce(msg_agg.c.msg_count, 0).label("total_messages"),
            msg_agg.c.last_msg_at,
        )
        .join(Chatbot, Chatbot.id == Conversation.chatbot_id)
        .join(Persona, Persona.id == Chatbot.persona_id)
        .outerjoin(msg_agg, msg_agg.c.conversation_id == Conversation.id)
        .filter(
            Chatbot.org_id == org_id,
            Conversation.deleted_at == None,
            Conversation.started_at >= start_date,
        )
    )

    if status:
        q = q.filter(Conversation.status == status)
    if chatbot_id:
        q = q.filter(Conversation.chatbot_id == chatbot_id)

    q = q.order_by(Conversation.started_at.desc())
    if limit is not None:
        q = q.limit(limit)

    rows = q.all()
    result = []
    for row in rows:
        duration = None
        if row.last_msg_at and row.started_at:
            duration = int((row.last_msg_at - row.started_at).total_seconds())

        result.append({
            "id": row.id,
            "chatbot_id": row.chatbot_id,
            "chatbot_name": row.chatbot_name,
            "status": row.status.value if hasattr(row.status, "value") else str(row.status),
            "total_messages": row.total_messages,
            "started_at": row.started_at,
            "duration_seconds": duration,
            "last_msg_at": row.last_msg_at,
        })

    return result


@router.get("/kpi", response_model=KPIResponse)
def get_kpis(
    days: int = Query(30, ge=1),
    chatbot_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    today = date.today()
    start_current = today - timedelta(days=days)
    start_prior = today - timedelta(days=2 * days)

    def build_query(start, end):
        q = db.query(AnalyticsDaily).join(
            Chatbot, Chatbot.id == AnalyticsDaily.chatbot_id
        ).filter(
            Chatbot.org_id == org_id,
            AnalyticsDaily.stat_date >= start,
            AnalyticsDaily.stat_date <= end,
        )
        if chatbot_id:
            q = q.filter(AnalyticsDaily.chatbot_id == chatbot_id)
        return q.all()

    current_records = build_query(start_current, today)
    prior_records = build_query(start_prior, start_current - timedelta(days=1))

    def aggregate_stats(records):
        total_convs = sum(r.total_conversations for r in records)
        total_msgs = sum(r.total_messages for r in records)
        total_escalated = sum(r.escalated_count for r in records)
        total_resolved = sum(r.resolved_count for r in records)

        resp_time_num = sum(
            r.avg_response_time * r.total_messages
            for r in records if r.avg_response_time is not None
        )
        messages_with_rt = sum(r.total_messages for r in records if r.avg_response_time is not None)
        avg_resp = (resp_time_num / messages_with_rt) if messages_with_rt > 0 else 0.0

        sent_num = sum(
            r.avg_sentiment * r.total_messages
            for r in records if r.avg_sentiment is not None
        )
        messages_with_sent = sum(r.total_messages for r in records if r.avg_sentiment is not None)
        avg_sent = (sent_num / messages_with_sent) if messages_with_sent > 0 else 0.0

        outcome_total = total_resolved + total_escalated
        workload_red = (total_resolved / outcome_total * 100.0) if outcome_total > 0 else 0.0
        escalation_rate = (total_escalated / outcome_total * 100.0) if outcome_total > 0 else 0.0

        return {
            "conversations": total_convs,
            "messages": total_msgs,
            "resolved": total_resolved,
            "avg_response_time": avg_resp,
            "avg_sentiment": avg_sent,
            "workload_reduction": workload_red,
            "escalation_rate": escalation_rate,
        }

    current_stats = aggregate_stats(current_records)
    prior_stats = aggregate_stats(prior_records)

    def pct_change(curr, prior):
        if prior > 0:
            return ((curr - prior) / prior) * 100.0
        return 100.0 if curr > 0 else 0.0

    return {
        "total_conversations": {
            "value": current_stats["conversations"],
            "change_pct": pct_change(current_stats["conversations"], prior_stats["conversations"]),
        },
        "avg_response_time": {
            "value": round(current_stats["avg_response_time"], 2),
            "change_pct": pct_change(current_stats["avg_response_time"], prior_stats["avg_response_time"]),
        },
        "satisfaction_score": {
            "value": round(current_stats["avg_sentiment"], 2),
            "change_pct": pct_change(current_stats["avg_sentiment"], prior_stats["avg_sentiment"]),
        },
        "workload_reduction": {
            "value": round(current_stats["workload_reduction"], 2),
            "change_pct": pct_change(current_stats["workload_reduction"], prior_stats["workload_reduction"]),
        },
        "escalation_rate": {
            "value": round(current_stats["escalation_rate"], 2),
            "change_pct": pct_change(current_stats["escalation_rate"], prior_stats["escalation_rate"]),
        },
    }


@router.get("/volume", response_model=List[VolumeSeriesItem])
def get_volume_chart(
    days: int = Query(30, ge=1),
    chatbot_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    today = date.today()
    start_current = today - timedelta(days=days)

    q = db.query(AnalyticsDaily).join(
        Chatbot, Chatbot.id == AnalyticsDaily.chatbot_id
    ).filter(
        Chatbot.org_id == org_id,
        AnalyticsDaily.stat_date >= start_current,
        AnalyticsDaily.stat_date <= today,
    )
    if chatbot_id:
        q = q.filter(AnalyticsDaily.chatbot_id == chatbot_id)
    records = q.order_by(AnalyticsDaily.stat_date.asc()).all()

    volume_by_date: dict = {}
    for r in records:
        d = r.stat_date
        if d not in volume_by_date:
            volume_by_date[d] = {"conversations": 0, "messages": 0, "resolved_count": 0, "escalated_count": 0}
        volume_by_date[d]["conversations"] += r.total_conversations
        volume_by_date[d]["messages"] += r.total_messages
        volume_by_date[d]["resolved_count"] += r.resolved_count
        volume_by_date[d]["escalated_count"] += r.escalated_count

    volume_series = []
    for i in range(days + 1):
        d = start_current + timedelta(days=i)
        val = volume_by_date.get(d, {"conversations": 0, "messages": 0, "resolved_count": 0, "escalated_count": 0})
        volume_series.append({
            "date": d,
            "conversations": val["conversations"],
            "messages": val["messages"],
            "resolved_count": val["resolved_count"],
            "escalated_count": val["escalated_count"],
        })

    return volume_series


@router.get("/languages", response_model=List[LanguageMixItem])
def get_languages(
    days: int = Query(30, ge=1),
    chatbot_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    today = date.today()
    start_current = today - timedelta(days=days)

    q = db.query(AnalyticsByLang).join(
        AnalyticsDaily, AnalyticsDaily.id == AnalyticsByLang.analytics_daily_id
    ).join(
        Chatbot, Chatbot.id == AnalyticsDaily.chatbot_id
    ).filter(
        Chatbot.org_id == org_id,
        AnalyticsDaily.stat_date >= start_current,
        AnalyticsDaily.stat_date <= today,
    )
    if chatbot_id:
        q = q.filter(AnalyticsDaily.chatbot_id == chatbot_id)
    lang_records = q.all()

    lang_counts: dict = {}
    for r in lang_records:
        lang_counts[r.language] = lang_counts.get(r.language, 0) + r.count

    language_mix = [{"language": lang, "count": count} for lang, count in lang_counts.items()]

    if not language_mix:
        language_mix = [
            {"language": "English", "count": 0},
            {"language": "Urdu", "count": 0},
            {"language": "Roman Urdu", "count": 0},
        ]

    return language_mix


@router.get("/channels", response_model=List[ChannelPerfItem])
def get_channels(
    days: int = Query(30, ge=1),
    chatbot_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    today = date.today()
    start_current = today - timedelta(days=days)

    q = db.query(AnalyticsByChannel).join(
        AnalyticsDaily, AnalyticsDaily.id == AnalyticsByChannel.analytics_daily_id
    ).join(
        Chatbot, Chatbot.id == AnalyticsDaily.chatbot_id
    ).filter(
        Chatbot.org_id == org_id,
        AnalyticsDaily.stat_date >= start_current,
        AnalyticsDaily.stat_date <= today,
    )
    if chatbot_id:
        q = q.filter(AnalyticsDaily.chatbot_id == chatbot_id)
    channel_records = q.all()

    channel_counts: dict = {}
    for r in channel_records:
        chan = "WhatsApp" if r.channel.lower() == "whatsapp" else r.channel.title()
        channel_counts[chan] = channel_counts.get(chan, 0) + r.count

    channel_perf = [{"channel": chan, "count": count} for chan, count in channel_counts.items()]

    if not channel_perf:
        channel_perf = [
            {"channel": "Web", "count": 0},
            {"channel": "WhatsApp", "count": 0},
        ]

    return channel_perf


@router.get("/interactions", response_model=List[InteractionItem])
def get_interactions(
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    chatbot_id: Optional[uuid.UUID] = Query(None),
    days: int = Query(30, ge=1),  # date-range filter now honoured
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    return _get_interactions(
        db,
        org_id,
        days,
        status=_parse_status_filter(status),
        chatbot_id=chatbot_id,
        limit=limit,
    )


@router.get("/export")
def export_report(
    report_type: Literal["analytics", "conversations"] = Query(...),
    format: Literal["csv", "pdf"] = Query("csv"),
    days: int = Query(30, ge=1),
    chatbot_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    export_date = date.today().isoformat()
    parsed_status = _parse_status_filter(status)

    if report_type == "analytics":
        kpis = get_kpis(days=days, chatbot_id=chatbot_id, db=db, org_id=org_id)
        volume = get_volume_chart(days=days, chatbot_id=chatbot_id, db=db, org_id=org_id)
        languages = get_languages(days=days, chatbot_id=chatbot_id, db=db, org_id=org_id)
        channels = get_channels(days=days, chatbot_id=chatbot_id, db=db, org_id=org_id)

        if format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["section", "label", "value", "unit", "change_pct", "detail_1", "detail_2", "detail_3"])

            metric_units = {
                "total_conversations": "",
                "avg_response_time": "s",
                "satisfaction_score": "/5",
                "workload_reduction": "%",
                "escalation_rate": "%",
            }
            metric_labels = {
                "total_conversations": "Total Conversations",
                "avg_response_time": "Bot Latency",
                "satisfaction_score": "Sentiment Score",
                "workload_reduction": "Deflection Rate",
                "escalation_rate": "Escalation Rate",
            }

            for key, metric in kpis.items():
                writer.writerow([
                    "KPI",
                    metric_labels.get(key, key),
                    metric["value"],
                    metric_units.get(key, ""),
                    f"{metric['change_pct']:+.1f}%",
                    "",
                    "",
                    "",
                ])

            for row in volume:
                writer.writerow([
                    "Volume",
                    row["date"].isoformat(),
                    row["conversations"],
                    "conversations",
                    "",
                    f"messages={row['messages']}",
                    f"resolved={row['resolved_count']}",
                    f"escalated={row['escalated_count']}",
                ])

            for row in languages:
                writer.writerow(["Language", row["language"], row["count"], "messages", "", "", "", ""])

            for row in channels:
                writer.writerow(["Channel", row["channel"], row["count"], "messages", "", "", "", ""])

            csv_text = output.getvalue()
            filename = f"analytics-report-{export_date}.csv"
            return Response(
                content=csv_text.encode("utf-8-sig"),
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        sections = [
            (
                "Key Metrics",
                [
                    f"Total Conversations: {int(round(kpis['total_conversations']['value']))} ({kpis['total_conversations']['change_pct']:+.1f}%)",
                    f"Bot Latency: {kpis['avg_response_time']['value']:.2f}s ({kpis['avg_response_time']['change_pct']:+.1f}%)",
                    f"Sentiment Score: {kpis['satisfaction_score']['value']:.2f}/5 ({kpis['satisfaction_score']['change_pct']:+.1f}%)",
                    f"Deflection Rate: {kpis['workload_reduction']['value']:.2f}% ({kpis['workload_reduction']['change_pct']:+.1f}%)",
                    f"Escalation Rate: {kpis['escalation_rate']['value']:.2f}% ({kpis['escalation_rate']['change_pct']:+.1f}%)",
                ],
            ),
            (
                "Resolution Trend",
                [
                    f"{row['date'].isoformat()} | conv {row['conversations']} | msgs {row['messages']} | resolved {row['resolved_count']} | escalated {row['escalated_count']}"
                    for row in volume
                ],
            ),
            (
                "Language Mix",
                [f"{row['language']}: {row['count']}" for row in languages],
            ),
            (
                "Channel Distribution",
                [f"{row['channel']}: {row['count']}" for row in channels],
            ),
        ]
        pdf = build_simple_pdf(
            title="Analytics Report",
            subtitle=f"Last {days} day(s){' - chatbot filtered' if chatbot_id else ''}",
            sections=sections,
        )
        filename = f"analytics-report-{export_date}.pdf"
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    interactions = _get_interactions(
        db,
        org_id,
        days,
        status=parsed_status,
        chatbot_id=chatbot_id,
        limit=None,
    )

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["conversation_id", "chatbot_name", "status", "total_messages", "duration", "started_at"])
        for row in interactions:
            writer.writerow([
                str(row["id"]),
                row["chatbot_name"],
                row["status"],
                row["total_messages"],
                row["duration_seconds"] if row["duration_seconds"] is not None else "",
                row["started_at"].isoformat(),
            ])

        filename = f"conversation-report-{export_date}.csv"
        return Response(
            content=output.getvalue().encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    sections = [
        (
            "Conversations",
            [
                f"#{str(row['id'])[:8].upper()} | {row['chatbot_name']} | {row['status'].title()} | {row['total_messages']} msgs | {_format_duration(row['duration_seconds'])} | {row['started_at'].strftime('%Y-%m-%d %H:%M')}"
                for row in interactions
            ] or ["No conversations matched the selected filters."],
        )
    ]
    pdf = build_simple_pdf(
        title="Conversation Report",
        subtitle=(
            f"Last {days} day(s)"
            + (f" | status: {status}" if status else "")
            + (" | chatbot filtered" if chatbot_id else "")
        ),
        sections=sections,
    )
    filename = f"conversation-report-{export_date}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
