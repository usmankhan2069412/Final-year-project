import sys
import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.user import User
from app.models.organization import Organization, OrgMember, OrgRole
from app.models.persona import Persona
from app.models.chatbot import Chatbot, ChatbotStatus
from app.models.conversation import Deployment, Channel, Conversation, ConversationStatus, ProcessedEvent, Message as DBMessage
from app.services.deployment import DeploymentService
from app.services.whatsapp import WhatsAppService
from app.schemas.whatsapp import DeploymentCreate

def run_tests():
    db = SessionLocal()
    # Redirect db.commit to db.flush to prevent closing the transaction in tests
    db.commit = db.flush
    
    # Start a transaction
    transaction = db.begin_nested() if db.in_transaction() else db.begin()
    
    try:
        print("--- RUNNING INTEGRATION TESTS FOR WHATSAPP CHANNEL ---")
        
        # 1. Setup Test Tenant Context
        user = User(
            email=f"wa-tester-{uuid.uuid4().hex[:6]}@test.com",
            full_name="WA Tester",
            password_hash="fakehash"
        )
        db.add(user)
        db.flush()
        
        org = Organization(owner_id=user.id, slug=f"wa-org-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        
        member = OrgMember(org_id=org.id, user_id=user.id, role=OrgRole.OWNER)
        db.add(member)
        db.flush()
        
        persona = Persona(org_id=org.id, name="WA Persona", language="en")
        db.add(persona)
        db.flush()
        
        chatbot = Chatbot(org_id=org.id, persona_id=persona.id, status=ChatbotStatus.ACTIVE)
        db.add(chatbot)
        db.flush()
        
        print("Test tenant setup complete.")

        # Set tenant org context in DB session (for RLS simulation if needed)
        db.execute(text("SELECT set_config('app.current_org_id', :org_id, true)"), {"org_id": str(org.id)})

        # 2. Test Deployment CRUD
        print("Testing Deployment CRUD...")
        
        # Create deployment (should fail without phone ID for WhatsApp)
        try:
            DeploymentService.create_deployment(
                db=db, 
                org_id=org.id, 
                data=DeploymentCreate(chatbot_id=chatbot.id, channel=Channel.WHATSAPP)
            )
            assert False, "Should have failed validation without whatsapp_phone_number_id"
        except ValueError as e:
            assert "WhatsApp Phone Number ID is required" in str(e)
            print("  - Validation: success (blocked missing phone number ID)")

        # Create valid deployment
        phone_id = "test-phone-12345"
        dep_in = DeploymentCreate(
            chatbot_id=chatbot.id,
            channel=Channel.WHATSAPP,
            whatsapp_phone_number_id=phone_id,
            whatsapp_business_account_id="waba-5678"
        )
        deployment = DeploymentService.create_deployment(db=db, org_id=org.id, data=dep_in)
        assert deployment.id is not None
        assert deployment.whatsapp_phone_number_id == phone_id
        assert deployment.is_active is False
        print(f"  - Create: success (Deployment ID: {deployment.id})")

        # List deployments
        deps = DeploymentService.get_deployments(db=db, org_id=org.id, chatbot_id=chatbot.id)
        assert len(deps) == 1
        assert deps[0].id == deployment.id
        print("  - List: success")

        # Activate deployment
        deployment = DeploymentService.activate(db=db, org_id=org.id, deployment_id=deployment.id)
        assert deployment.is_active is True
        print("  - Activate: success")

        # Eager lookup by phone number ID
        lookup_dep = DeploymentService.get_by_phone_number_id(db=db, phone_number_id=phone_id)
        assert lookup_dep is not None
        assert lookup_dep.id == deployment.id
        print("  - Lookup: success")

        # Deactivate deployment
        deployment = DeploymentService.deactivate(db=db, org_id=org.id, deployment_id=deployment.id)
        assert deployment.is_active is False
        
        # Lookup should now return None since it is inactive
        lookup_dep = DeploymentService.get_by_phone_number_id(db=db, phone_number_id=phone_id)
        assert lookup_dep is None
        print("  - Deactivate & Lookup: success")

        # Re-activate for webhook tests
        deployment = DeploymentService.activate(db=db, org_id=org.id, deployment_id=deployment.id)

        # 3. Test Webhook Webhook Verification Logic
        print("Testing Webhook Verification...")
        # Mock settings.WHATSAPP_VERIFY_TOKEN
        with patch("app.services.whatsapp.settings.WHATSAPP_VERIFY_TOKEN", "test_verify_token"):
            from app.api.v1.channels import verify_webhook
            # Valid token
            challenge = verify_webhook(hub_mode="subscribe", hub_verify_token="test_verify_token", hub_challenge="12345")
            assert challenge == "12345"
            
            # Invalid token
            from fastapi import HTTPException
            try:
                verify_webhook(hub_mode="subscribe", hub_verify_token="wrong_token", hub_challenge="12345")
                assert False, "Should have raised 403"
            except HTTPException as e:
                assert e.status_code == 403
            print("  - Verification signature: success")

        # 4. Test WhatsApp Session Management (24h timeout window)
        print("Testing Session Management (24h Window)...")
        sender = "923009999999"
        
        # Session 1: Create fresh conversation
        conv1 = WhatsAppService.find_or_create_conversation(db=db, sender_phone=sender, deployment=deployment)
        assert conv1.id is not None
        assert conv1.status == ConversationStatus.ONGOING
        
        # Reuse Session: Immediate next lookup should return the exact same conversation
        conv2 = WhatsAppService.find_or_create_conversation(db=db, sender_phone=sender, deployment=deployment)
        assert conv2.id == conv1.id
        print("  - Session reuse within window: success")

        # Simulate message inside conv1 to update activity
        msg1 = DBMessage(conversation_id=conv1.id, role="user", content="hello", created_at=datetime.utcnow() - timedelta(hours=25))
        db.add(msg1)
        db.flush()

        # Inactivity Check: Since the last message was 25 hours ago, a new request should resolve conv1 and start a new conversation
        conv3 = WhatsAppService.find_or_create_conversation(db=db, sender_phone=sender, deployment=deployment)
        assert conv3.id != conv1.id
        assert conv1.status == ConversationStatus.RESOLVED
        print("  - Session expiration after 24h inactivity: success")

        # 5. Test Webhook Message Parsing & Idempotency
        print("Testing Webhook Parsing & Idempotency...")
        
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "phone_number_id": phone_id
                                },
                                "messages": [
                                    {
                                        "id": "msg-unique-id-999",
                                        "from": sender,
                                        "type": "text",
                                        "text": {
                                            "body": "Hi there Aina"
                                        },
                                        "timestamp": "1678888888"
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        # Parse message
        parsed = WhatsAppService.parse_incoming_message(payload)
        assert parsed is not None
        assert parsed.message_id == "msg-unique-id-999"
        assert parsed.sender_phone == sender
        assert parsed.text == "Hi there Aina"
        print("  - Webhook parsing: success")

        # Process message & verify RAG pipeline calls + outbound mocks
        with patch("app.services.whatsapp.WhatsAppService.send_whatsapp_message") as mock_send:
            with patch("app.services.chat.ChatService.get_rag_response") as mock_rag:
                mock_rag.return_value = {
                    "response": "Hello, how can I help you?",
                    "conversation_id": uuid.uuid4(),
                    "sources": [],
                    "status": ConversationStatus.ONGOING
                }
                
                # First run - should process
                WhatsAppService.process_inbound_message(db, payload)
                assert mock_rag.call_count == 1
                assert mock_send.call_count == 1
                mock_send.assert_called_with(
                    phone_number=sender,
                    text="Hello, how can I help you?",
                    phone_number_id=phone_id
                )
                print("  - Message ingestion & outbound reply: success")

                # Second run - should be skipped due to ProcessedEvent idempotency check
                WhatsAppService.process_inbound_message(db, payload)
                assert mock_rag.call_count == 1  # count stays 1
                assert mock_send.call_count == 1  # count stays 1
                print("  - Webhook event idempotency check: success")

        # Delete deployment
        deleted = DeploymentService.delete_deployment(db=db, org_id=org.id, deployment_id=deployment.id)
        assert deleted is True
        print("  - Delete deployment: success")

        print("\nAll WhatsApp integration tests passed successfully!")

    finally:
        transaction.rollback()
        db.close()
        print("Database transaction rolled back successfully. Database is clean.")

if __name__ == "__main__":
    from sqlalchemy import text
    run_tests()
