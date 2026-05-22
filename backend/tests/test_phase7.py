import sys
import os
import uuid
from datetime import datetime, date, timezone, timedelta

# Add current directory to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.user import User
from app.models.organization import Organization, OrgMember, OrgRole
from app.models.persona import Persona
from app.models.chatbot import Chatbot, ChatbotStatus
from app.models.conversation import Conversation, ConversationStatus, Message as DBMessage, MessageRole
from app.models.analytics import AnalyticsDaily, AnalyticsByChannel, AnalyticsByLang
from app.services.chat import ChatService
from app.tasks.analytics_aggregation import aggregate_daily_metrics

def run_tests():
    db = SessionLocal()
    # Redirect db.commit to db.flush to prevent closing the transaction in tests
    db.commit = db.flush
    
    # Start a transaction
    transaction = db.begin_nested() if db.in_transaction() else db.begin()
    try:
        print("--- RUNNING INTEGRATION TESTS FOR PHASE 7: ANALYTICS & ESCALATION ---")
        
        # 1. Create test users (Owner and Admin)
        owner = User(
            email=f"owner-{uuid.uuid4().hex[:6]}@test.com",
            full_name="Owner User",
            password_hash="fakehash"
        )
        admin = User(
            email=f"admin-{uuid.uuid4().hex[:6]}@test.com",
            full_name="Admin User",
            password_hash="fakehash"
        )
        db.add_all([owner, admin])
        db.flush()
        print(f"Created Test Users: Owner ({owner.id}), Admin ({admin.id})")

        # 2. Create test organization
        org = Organization(owner_id=owner.id, slug=f"org-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        print(f"Created Test Organization: {org.slug} ({org.id})")

        # 3. Create organization memberships
        member_owner = OrgMember(org_id=org.id, user_id=owner.id, role=OrgRole.OWNER)
        member_admin = OrgMember(org_id=org.id, user_id=admin.id, role=OrgRole.ADMIN)
        db.add_all([member_owner, member_admin])
        db.flush()
        print("Created organization memberships.")

        # 4. Create Persona and Chatbot
        persona = Persona(
            name="Phase 7 Tester Persona",
            language="english"
        )
        db.add(persona)
        db.flush()

        chatbot = Chatbot(
            org_id=org.id,
            persona_id=persona.id,
            status=ChatbotStatus.ACTIVE
        )
        db.add(chatbot)
        db.flush()
        print(f"Created Persona ({persona.id}) and Chatbot ({chatbot.id})")

        # 5. Test Least-Busy routing
        # Setup conversation 1 escalated to Owner
        conv1 = Conversation(
            chatbot_id=chatbot.id,
            status=ConversationStatus.ESCALATED,
            assigned_agent_id=owner.id
        )
        db.add(conv1)
        db.flush()
        print("Set up Conv 1: Escalated to Owner.")

        # Setup conversation 2 (ongoing, to be escalated)
        conv2 = Conversation(
            chatbot_id=chatbot.id,
            status=ConversationStatus.ONGOING
        )
        db.add(conv2)
        db.flush()
        print("Set up Conv 2: Ongoing.")

        # Call get_rag_response with handoff query for Conv 2
        # Since Owner has 1 escalated chat and Admin has 0, it should route to Admin
        response = ChatService.get_rag_response(
            db=db,
            org_id=org.id,
            chatbot_id=chatbot.id,
            conversation_id=conv2.id,
            user_message="I want to speak with a human support representative"
        )
        
        db.refresh(conv2)
        assert conv2.status == ConversationStatus.ESCALATED, "Conv 2 should be escalated"
        assert conv2.assigned_agent_id == admin.id, f"Conv 2 should be assigned to Admin ({admin.id}) but got ({conv2.assigned_agent_id})"
        print("Success: Least-Busy routing assigned the chat to the less busy agent (Admin).")

        # 6. Test RAG bypass when escalated
        # Send another message, it should bypass standard LLM processing and return support agent response
        bypass_response = ChatService.get_rag_response(
            db=db,
            org_id=org.id,
            chatbot_id=chatbot.id,
            conversation_id=conv2.id,
            user_message="Are you there?"
        )
        
        assert "reviewing your message and will respond shortly" in bypass_response["response"], "Should return standard handoff message"
        assert bypass_response["status"] == ConversationStatus.ESCALATED
        print("Success: RAG logic bypassed correctly during escalation.")

        # 7. Test Auto-Resume Bot after resolution
        # Simulate agent resolving the conversation
        conv2.status = ConversationStatus.RESOLVED
        db.add(conv2)
        db.flush()
        print("Conv 2 status updated to RESOLVED.")

        # Send another message, conversation should go back to ONGOING and agent ID cleared
        resume_response = ChatService.get_rag_response(
            db=db,
            org_id=org.id,
            chatbot_id=chatbot.id,
            conversation_id=conv2.id,
            user_message="Hello, I have another question"
        )
        
        db.refresh(conv2)
        assert conv2.status == ConversationStatus.ONGOING, "Conversation should transition back to ONGOING"
        assert conv2.assigned_agent_id is None, "Assigned agent should be cleared on auto-resume"
        print("Success: Auto-resume reset resolved conversation to ongoing and cleared agent assignment.")

        # 8. Test Daily Analytics Aggregation Job
        # Seed some conversation and messages dated yesterday
        yesterday = date.today() - timedelta(days=1)
        yesterday_dt_user = datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=10)
        yesterday_dt_bot = yesterday_dt_user + timedelta(seconds=12) # 12 second response time
        
        conv_agg = Conversation(
            chatbot_id=chatbot.id,
            status=ConversationStatus.RESOLVED,
            started_at=yesterday_dt_user
        )
        db.add(conv_agg)
        db.flush()

        msg_user = DBMessage(
            conversation_id=conv_agg.id,
            role=MessageRole.USER,
            content="Thanks, shukriya! Bohat satisfied with the good support!",
            created_at=yesterday_dt_user
        )
        msg_bot = DBMessage(
            conversation_id=conv_agg.id,
            role=MessageRole.BOT,
            content="You're welcome!",
            created_at=yesterday_dt_bot
        )
        db.add_all([msg_user, msg_bot])
        db.flush()
        print("Created mock historical conversation and messages for yesterday.")

        # Run aggregation for yesterday
        aggregate_daily_metrics(db, yesterday)
        
        # Query generated stats
        daily_stat = db.query(AnalyticsDaily).filter(
            AnalyticsDaily.chatbot_id == chatbot.id,
            AnalyticsDaily.stat_date == yesterday
        ).first()
        
        assert daily_stat is not None, "Daily stat record should be created"
        assert daily_stat.total_conversations == 1, f"Expected 1 conversation, got {daily_stat.total_conversations}"
        assert daily_stat.total_messages == 2, f"Expected 2 messages, got {daily_stat.total_messages}"
        assert daily_stat.avg_response_time == 12.0, f"Expected avg response time of 12.0s, got {daily_stat.avg_response_time}"
        assert daily_stat.avg_sentiment == 5.0, f"Expected sentiment score of 5.0, got {daily_stat.avg_sentiment}"
        assert daily_stat.resolved_count == 1, f"Expected resolved count 1, got {daily_stat.resolved_count}"
        print("Success: Daily analytics aggregation computed stats, response time, and sentiment correctly.")

        # Query channel performance
        channel_stat = db.query(AnalyticsByChannel).filter(
            AnalyticsByChannel.analytics_daily_id == daily_stat.id
        ).first()
        assert channel_stat is not None
        assert channel_stat.channel == "Web"
        assert channel_stat.count == 1
        print("Success: Aggregation recorded channel performance stats correctly.")

        # Query language performance
        lang_stat = db.query(AnalyticsByLang).filter(
            AnalyticsByLang.analytics_daily_id == daily_stat.id
        ).first()
        assert lang_stat is not None
        assert lang_stat.language == "Roman Urdu", f"Expected language 'Roman Urdu', got '{lang_stat.language}'"
        assert lang_stat.count == 1
        print("Success: Aggregation recorded language performance stats correctly.")

        # 9. Test PubSub Seam (InMemoryPubSubBackend)
        from app.services.pubsub import InMemoryPubSubBackend
        import asyncio
        
        async def run_pubsub_test():
            pubsub = InMemoryPubSubBackend()
            ps_queue = await pubsub.subscribe("test-org-123")
            assert "test-org-123" in pubsub.connections
            assert len(pubsub.connections["test-org-123"]) == 1
            
            await pubsub.publish("test-org-123", "test_event", {"some": "data"})
            payload = ps_queue.get_nowait()
            assert payload["event"] == "test_event"
            assert payload["data"] == {"some": "data"}
            
            await pubsub.unsubscribe("test-org-123", ps_queue)
            assert "test-org-123" not in pubsub.connections
            
        asyncio.run(run_pubsub_test())
        print("Success: PubSub seam and memory backend works correctly.")

        # 10. Test EscalationRouter unit functions
        from app.services.escalation_router import EscalationRouter
        
        # Test standard messages
        msg_en = EscalationRouter.get_escalation_message("english")
        msg_ur = EscalationRouter.get_escalation_message("urdu")
        msg_other = EscalationRouter.get_escalation_message("roman urdu")
        
        assert "reviewing your message" in msg_en
        assert "سپورٹ ایجنٹ" in msg_ur
        assert "Support agent" in msg_other
        
        # Test finding least busy agent
        least_busy = EscalationRouter.find_least_busy_agent(db, org.id)
        assert least_busy == admin.id, f"Expected admin {admin.id} to be least busy, got {least_busy}"
        print("Success: EscalationRouter unit functions behave correctly.")

        print("\nAll Phase 7 Integration Tests Passed Successfully!")

    finally:
        transaction.rollback()
        db.close()
        print("Database transaction rolled back. Database is clean.")

if __name__ == "__main__":
    run_tests()
