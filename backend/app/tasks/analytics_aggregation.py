import logging
from datetime import datetime, date, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.chatbot import Chatbot
from app.models.conversation import Conversation, Message, ConversationStatus, MessageRole
from app.models.analytics import AnalyticsDaily, AnalyticsByChannel, AnalyticsByLang

logger = logging.getLogger(__name__)

def classify_message_sentiment(text: str) -> float:
    text_lower = text.lower()
    
    positive_kws = [
        "thanks", "thank you", "satisfied", "good", "great", "awesome", "excellent", "helpful", "solved", "amazing", "love",
        "شکریہ", "بہت اچھا", "مطمئن", "جزاک اللہ", "مدد",
        "shukriya", "bohat acha", "bohath acha", "shukria", "mutmain", "sahoolat", "fit", "zabardast"
    ]
    negative_kws = [
        "bad support", "terrible", "worst", "useless", "not helpful", "broken", "failed", "disappointed", "slow", "rubbish", "garbage",
        "خراب", "بکواس", "فضول", "کام نہیں", "نہیں ہوا", "غلط",
        "kharab", "bakwas", "fuzool", "kaam nahi", "bekaar", "tameez nahi"
    ]
    
    pos_count = sum(1 for kw in positive_kws if kw in text_lower)
    neg_count = sum(1 for kw in negative_kws if kw in text_lower)
    
    if pos_count > neg_count:
        return 4.0 if pos_count == 1 else 5.0
    elif neg_count > pos_count:
        return 2.0 if neg_count == 1 else 1.0
    else:
        return 3.0


def detect_message_language(text: str) -> str:
    if any(ord(c) >= 0x0600 and ord(c) <= 0x06FF for c in text):
        return "Urdu"
    text_lower = text.lower()
    roman_urdu_words = ["hai", "kya", "nhi", "haan", "batao", "shukriya", "bohat", "acha", "mein", "hun", "ho", "raha", "kiya", "liye", "bhai", "yaar"]
    words = text_lower.split()
    if any(w in roman_urdu_words for w in words):
        return "Roman Urdu"
    return "English"


def aggregate_daily_metrics(db: Session, target_date: date):
    """
    Run daily aggregation for the target_date across all chatbots.
    """
    chatbots = db.query(Chatbot).filter(Chatbot.deleted_at == None).all()
    
    logger.info(f"Starting analytics aggregation for date {target_date} across {len(chatbots)} chatbots.")
    
    for chatbot in chatbots:
        try:
            # Query conversations started on target_date
            conversations = db.query(Conversation).filter(
                Conversation.chatbot_id == chatbot.id,
                func.date(Conversation.started_at) == target_date,
                Conversation.deleted_at == None
            ).all()
            
            if not conversations:
                # Still write a zero record to ensure continuous time series data
                db.query(AnalyticsDaily).filter(
                    AnalyticsDaily.chatbot_id == chatbot.id,
                    AnalyticsDaily.stat_date == target_date
                ).delete()
                
                daily_record = AnalyticsDaily(
                    chatbot_id=chatbot.id,
                    stat_date=target_date,
                    total_conversations=0,
                    total_messages=0,
                    avg_response_time=None,
                    avg_sentiment=None,
                    escalated_count=0,
                    resolved_count=0
                )
                db.add(daily_record)
                db.commit()
                continue

            total_conversations = len(conversations)
            escalated_count = sum(1 for c in conversations if c.status == ConversationStatus.ESCALATED)
            resolved_count = sum(1 for c in conversations if c.status == ConversationStatus.RESOLVED)
            
            total_messages = 0
            response_times = []
            sentiment_scores = []
            channel_counts = {}
            lang_counts = {}
            
            for conv in conversations:
                messages = db.query(Message).filter(
                    Message.conversation_id == conv.id
                ).order_by(Message.created_at.asc()).all()
                
                total_messages += len(messages)
                
                # Channel performance count
                channel_val = "Web"
                if conv.deployment:
                    channel_val = conv.deployment.channel.value if hasattr(conv.deployment.channel, "value") else str(conv.deployment.channel)
                channel_counts[channel_val] = channel_counts.get(channel_val, 0) + 1
                
                # Language detection (based on first user message)
                first_user_msg = next((m for m in messages if m.role == MessageRole.USER), None)
                lang = "English"
                if first_user_msg:
                    lang = detect_message_language(first_user_msg.content)
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
                
                # Response time and sentiment calculation
                last_user_time = None
                for msg in messages:
                    if msg.role == MessageRole.USER:
                        sentiment_scores.append(classify_message_sentiment(msg.content))
                        if last_user_time is None:
                            last_user_time = msg.created_at
                    elif msg.role == MessageRole.BOT:
                        if last_user_time is not None:
                            diff = (msg.created_at - last_user_time).total_seconds()
                            response_times.append(diff)
                            last_user_time = None

            avg_resp_time = (sum(response_times) / len(response_times)) if response_times else None
            avg_sentiment = (sum(sentiment_scores) / len(sentiment_scores)) if sentiment_scores else None

            # Delete old record for idempotency
            db.query(AnalyticsDaily).filter(
                AnalyticsDaily.chatbot_id == chatbot.id,
                AnalyticsDaily.stat_date == target_date
            ).delete()
            db.flush()

            daily_record = AnalyticsDaily(
                chatbot_id=chatbot.id,
                stat_date=target_date,
                total_conversations=total_conversations,
                total_messages=total_messages,
                avg_response_time=avg_resp_time,
                avg_sentiment=avg_sentiment,
                escalated_count=escalated_count,
                resolved_count=resolved_count
            )
            db.add(daily_record)
            db.flush()

            # Channels
            for chan, count in channel_counts.items():
                db.add(AnalyticsByChannel(
                    analytics_daily_id=daily_record.id,
                    channel=chan,
                    count=count
                ))

            # Languages
            for lang, count in lang_counts.items():
                db.add(AnalyticsByLang(
                    analytics_daily_id=daily_record.id,
                    language=lang,
                    count=count
                ))

            db.commit()
            logger.info(f"Aggregated metrics for chatbot {chatbot.id} on {target_date}: convs={total_conversations}, msgs={total_messages}")
        except Exception as e:
            logger.error(f"Failed to aggregate metrics for chatbot {chatbot.id} on {target_date}: {e}", exc_info=True)
            db.rollback()


def run_nightly_aggregation():
    """
    Main job function executed by APScheduler.
    Aggregates metrics for 'yesterday'.
    """
    db = SessionLocal()
    try:
        yesterday = date.today() - timedelta(days=1)
        aggregate_daily_metrics(db, yesterday)
    finally:
        db.close()
