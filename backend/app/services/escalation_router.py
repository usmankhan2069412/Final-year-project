import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.language import detect_message_language

from app.models.conversation import Conversation, ConversationStatus, Message as DBMessage, MessageRole
from app.models.organization import OrgMember, OrgRole, Organization
from app.models.user import User
from app.models.chatbot import Chatbot

logger = logging.getLogger(__name__)

class EscalationRouter:
    @staticmethod
    def get_escalation_message(language: Optional[str], user_message: Optional[str] = None) -> str:
        """Get standard handoff message based on persona language."""
        if language == "multilingual" and user_message:
            language = detect_message_language(user_message)
            
        if language == "urdu":
            return "سپورٹ ایجنٹ آپ کے پیغام کا جائزہ لے رہے ہیں اور جلد ہی جواب دیں گے۔"
        elif language == "english":
            return "A support agent is reviewing your message and will respond shortly."
        else:
            return "Support agent aap ke message ka jaiza le rahe hain aur jald hi jawab denge."

    @staticmethod
    def find_least_busy_agent(db: Session, org_id: uuid.UUID) -> Optional[uuid.UUID]:
        """Find the least-busy agent (OWNER or ADMIN role) in the organization."""
        agents = db.query(User).join(
            OrgMember, OrgMember.user_id == User.id
        ).filter(
            OrgMember.org_id == org_id,
            OrgMember.role.in_([OrgRole.OWNER, OrgRole.ADMIN]),
            User.deleted_at == None
        ).all()
        
        agent_escalated_counts = {}
        for agent in agents:
            count = db.query(func.count(Conversation.id)).filter(
                Conversation.assigned_agent_id == agent.id,
                Conversation.status == ConversationStatus.ESCALATED,
                Conversation.deleted_at == None
            ).scalar() or 0
            agent_escalated_counts[agent.id] = count

        if agent_escalated_counts:
            return min(agent_escalated_counts, key=agent_escalated_counts.get)
        
        # Fallback to org owner
        org = db.query(Organization).filter(Organization.id == org_id).first()
        return org.owner_id if org else None

    @classmethod
    def escalate(
        cls,
        db: Session,
        conversation: Conversation,
        chatbot: Chatbot,
        org_id: uuid.UUID,
        user_message: str,
        response_text: str,
        language: Optional[str],
        is_new_conv: bool = False,
        active_config_id: Optional[uuid.UUID] = None,
        sources: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Escalates the conversation: assigns least busy agent, updates status,
        saves message, updates chatbot statistics, and broadcasts SSE events.
        """
        import asyncio
        from app.services.sse_manager import sse_manager
        
        # 1. Update status
        conversation.status = ConversationStatus.ESCALATED
        
        # 2. Assign agent if not already assigned
        if not conversation.assigned_agent_id:
            conversation.assigned_agent_id = cls.find_least_busy_agent(db, org_id)
            
        db.add(conversation)
        
        # 3. Record messages with IDs now so live inbox events can dedupe safely.
        user_msg = DBMessage(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=user_message,
            config_id=active_config_id,
            created_at=datetime.now(timezone.utc),
        )
        bot_msg = DBMessage(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.BOT,
            content=response_text,
            config_id=active_config_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user_msg)
        db.add(bot_msg)
        
        # 4. Update chatbot statistics
        chatbot.total_messages += 2
        if is_new_conv:
            chatbot.total_conversations += 1
        db.add(chatbot)
        
        db.commit()
        
        # 5. Broadcast escalation status event
        escalation_event = {
            "conversation_id": str(conversation.id),
            "status": ConversationStatus.ESCALATED.value,
            "assigned_agent_id": str(conversation.assigned_agent_id) if conversation.assigned_agent_id else None,
            "chatbot_id": str(chatbot.id)
        }
        
        # 6. Broadcast user and bot messages
        user_msg_data = {
            "conversation_id": str(conversation.id),
            "message": {
                "id": str(user_msg.id),
                "role": "user",
                "content": user_message,
                "created_at": user_msg.created_at.isoformat()
            }
        }
        bot_msg_data = {
            "conversation_id": str(conversation.id),
            "message": {
                "id": str(bot_msg.id),
                "role": "bot",
                "content": response_text,
                "created_at": bot_msg.created_at.isoformat()
            }
        }
        
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(sse_manager.broadcast(str(org_id), "escalation", escalation_event))
            loop.create_task(sse_manager.broadcast(str(org_id), "message", user_msg_data))
            loop.create_task(sse_manager.broadcast(str(org_id), "message", bot_msg_data))
        except RuntimeError:
            pass
            
        return {
            "response": response_text,
            "conversation_id": conversation.id,
            "sources": sources or [],
            "status": ConversationStatus.ESCALATED
        }

    @classmethod
    def handle_escalated_message(
        cls,
        db: Session,
        conversation: Conversation,
        chatbot: Chatbot,
        org_id: uuid.UUID,
        user_message: str,
        language: Optional[str],
        active_config_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Handles messages sent to an already escalated conversation by bypassing standard RAG."""
        import asyncio
        from app.services.sse_manager import sse_manager
        
        response_text = cls.get_escalation_message(language, user_message=user_message)
        
        user_msg = DBMessage(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=user_message,
            config_id=active_config_id,
            created_at=datetime.now(timezone.utc),
        )
        bot_msg = DBMessage(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.BOT,
            content=response_text,
            config_id=active_config_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user_msg)
        db.add(bot_msg)
        
        # Update chatbot statistics
        chatbot.total_messages += 2
        db.add(chatbot)
        
        db.commit()
        
        user_msg_data = {
            "conversation_id": str(conversation.id),
            "message": {
                "id": str(user_msg.id),
                "role": "user",
                "content": user_message,
                "created_at": user_msg.created_at.isoformat()
            }
        }
        bot_msg_data = {
            "conversation_id": str(conversation.id),
            "message": {
                "id": str(bot_msg.id),
                "role": "bot",
                "content": response_text,
                "created_at": bot_msg.created_at.isoformat()
            }
        }
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(sse_manager.broadcast(str(org_id), "message", user_msg_data))
            loop.create_task(sse_manager.broadcast(str(org_id), "message", bot_msg_data))
        except RuntimeError:
            pass
            
        return {
            "response": response_text,
            "conversation_id": conversation.id,
            "sources": [],
            "status": ConversationStatus.ESCALATED
        }
