import uuid
from datetime import datetime, date, timedelta
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_tenant_db, get_current_org_id
from app.models.analytics import AnalyticsDaily, AnalyticsByChannel, AnalyticsByLang
from app.models.chatbot import Chatbot
from app.models.persona import Persona
from app.models.conversation import Conversation, Message
from app.schemas.analytics import KPIResponse, VolumeSeriesItem, LanguageMixItem, ChannelPerfItem, InteractionItem

router = APIRouter()

@router.get("/kpi", response_model=KPIResponse)
def get_kpis(
    days: int = Query(30, ge=1),
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    today = date.today()
    start_current = today - timedelta(days=days)
    start_prior = today - timedelta(days=2 * days)

    current_records = db.query(AnalyticsDaily).join(
        Chatbot, Chatbot.id == AnalyticsDaily.chatbot_id
    ).filter(
        Chatbot.org_id == org_id,
        AnalyticsDaily.stat_date >= start_current,
        AnalyticsDaily.stat_date <= today
    ).all()

    prior_records = db.query(AnalyticsDaily).join(
        Chatbot, Chatbot.id == AnalyticsDaily.chatbot_id
    ).filter(
        Chatbot.org_id == org_id,
        AnalyticsDaily.stat_date >= start_prior,
        AnalyticsDaily.stat_date < start_current
    ).all()

    def aggregate_stats(records):
        total_convs = sum(r.total_conversations for r in records)
        total_msgs = sum(r.total_messages for r in records)
        
        # Weighted average response time
        resp_time_numerator = sum(r.avg_response_time * r.total_conversations for r in records if r.avg_response_time is not None)
        convs_with_resp_time = sum(r.total_conversations for r in records if r.avg_response_time is not None)
        avg_resp = (resp_time_numerator / convs_with_resp_time) if convs_with_resp_time > 0 else 0.0
        
        # Weighted average sentiment
        sentiment_numerator = sum(r.avg_sentiment * r.total_conversations for r in records if r.avg_sentiment is not None)
        convs_with_sentiment = sum(r.total_conversations for r in records if r.avg_sentiment is not None)
        avg_sent = (sentiment_numerator / convs_with_sentiment) if convs_with_sentiment > 0 else 0.0
        
        # Workload reduction: proportion of chats NOT escalated
        total_escalated = sum(r.escalated_count for r in records)
        workload_red = ((total_convs - total_escalated) / total_convs * 100.0) if total_convs > 0 else 0.0
        
        return {
            "conversations": total_convs,
            "messages": total_msgs,
            "avg_response_time": avg_resp,
            "avg_sentiment": avg_sent,
            "workload_reduction": workload_red
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
            "change_pct": pct_change(current_stats["conversations"], prior_stats["conversations"])
        },
        "avg_response_time": {
            "value": round(current_stats["avg_response_time"], 2),
            "change_pct": pct_change(current_stats["avg_response_time"], prior_stats["avg_response_time"])
        },
        "satisfaction_score": {
            "value": round(current_stats["avg_sentiment"], 2),
            "change_pct": pct_change(current_stats["avg_sentiment"], prior_stats["avg_sentiment"])
        },
        "workload_reduction": {
            "value": round(current_stats["workload_reduction"], 2),
            "change_pct": pct_change(current_stats["workload_reduction"], prior_stats["workload_reduction"])
        }
    }


@router.get("/volume", response_model=List[VolumeSeriesItem])
def get_volume_chart(
    days: int = Query(30, ge=1),
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    today = date.today()
    start_current = today - timedelta(days=days)

    records = db.query(AnalyticsDaily).join(
        Chatbot, Chatbot.id == AnalyticsDaily.chatbot_id
    ).filter(
        Chatbot.org_id == org_id,
        AnalyticsDaily.stat_date >= start_current,
        AnalyticsDaily.stat_date <= today
    ).order_by(AnalyticsDaily.stat_date.asc()).all()

    volume_by_date = {}
    for r in records:
        d = r.stat_date
        if d not in volume_by_date:
            volume_by_date[d] = {"conversations": 0, "messages": 0}
        volume_by_date[d]["conversations"] += r.total_conversations
        volume_by_date[d]["messages"] += r.total_messages

    volume_series = []
    # Fill in the date range so there are no empty gaps in charts
    for i in range(days + 1):
        d = start_current + timedelta(days=i)
        val = volume_by_date.get(d, {"conversations": 0, "messages": 0})
        volume_series.append({
            "date": d,
            "conversations": val["conversations"],
            "messages": val["messages"]
        })

    return volume_series


@router.get("/languages", response_model=List[LanguageMixItem])
def get_languages(
    days: int = Query(30, ge=1),
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    today = date.today()
    start_current = today - timedelta(days=days)

    lang_records = db.query(AnalyticsByLang).join(
        AnalyticsDaily, AnalyticsDaily.id == AnalyticsByLang.analytics_daily_id
    ).join(
        Chatbot, Chatbot.id == AnalyticsDaily.chatbot_id
    ).filter(
        Chatbot.org_id == org_id,
        AnalyticsDaily.stat_date >= start_current,
        AnalyticsDaily.stat_date <= today
    ).all()

    lang_counts = {}
    for r in lang_records:
        lang_counts[r.language] = lang_counts.get(r.language, 0) + r.count

    language_mix = [
        {"language": lang, "count": count}
        for lang, count in lang_counts.items()
    ]

    if not language_mix:
        language_mix = [
            {"language": "English", "count": 0},
            {"language": "Urdu", "count": 0},
            {"language": "Roman Urdu", "count": 0}
        ]

    return language_mix


@router.get("/channels", response_model=List[ChannelPerfItem])
def get_channels(
    days: int = Query(30, ge=1),
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    today = date.today()
    start_current = today - timedelta(days=days)

    channel_records = db.query(AnalyticsByChannel).join(
        AnalyticsDaily, AnalyticsDaily.id == AnalyticsByChannel.analytics_daily_id
    ).join(
        Chatbot, Chatbot.id == AnalyticsDaily.chatbot_id
    ).filter(
        Chatbot.org_id == org_id,
        AnalyticsDaily.stat_date >= start_current,
        AnalyticsDaily.stat_date <= today
    ).all()

    channel_counts = {}
    for r in channel_records:
        chan = r.channel
        if chan.lower() == "whatsapp":
            chan = "WhatsApp"
        else:
            chan = chan.title()
        channel_counts[chan] = channel_counts.get(chan, 0) + r.count

    channel_perf = [
        {"channel": chan, "count": count}
        for chan, count in channel_counts.items()
    ]

    if not channel_perf:
        channel_perf = [
            {"channel": "Web", "count": 0},
            {"channel": "WhatsApp", "count": 0}
        ]

    return channel_perf


@router.get("/interactions", response_model=List[InteractionItem])
def get_interactions(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    interactions = db.query(
        Conversation.id,
        Conversation.chatbot_id,
        Persona.name.label("chatbot_name"),
        Conversation.status,
        Conversation.started_at
    ).join(
        Chatbot, Chatbot.id == Conversation.chatbot_id
    ).join(
        Persona, Persona.id == Chatbot.persona_id
    ).filter(
        Chatbot.org_id == org_id,
        Conversation.deleted_at == None
    ).order_by(Conversation.started_at.desc()).limit(limit).all()

    from sqlalchemy import func
    interaction_list = []
    for item in interactions:
        msg_count = db.query(func.count(Message.id)).filter(Message.conversation_id == item.id).scalar() or 0
        interaction_list.append({
            "id": item.id,
            "chatbot_id": item.chatbot_id,
            "chatbot_name": item.chatbot_name,
            "status": item.status.value if hasattr(item.status, "value") else str(item.status),
            "total_messages": msg_count,
            "started_at": item.started_at
        })

    return interaction_list
