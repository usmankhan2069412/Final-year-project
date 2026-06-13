import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import BackgroundTasks

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
        from app.core.messages import get_escalated_wait_message
        if language == "multilingual" and user_message:
            language = detect_message_language(user_message)
        return get_escalated_wait_message(language)

    @staticmethod
    def find_least_busy_agent(db: Session, org_id: uuid.UUID) -> Optional[uuid.UUID]:
        """Find the least-busy agent (OWNER or ADMIN role) in the organization."""
        agent_counts = db.query(
            User.id,
            func.count(Conversation.id)
        ).select_from(User).join(
            OrgMember, OrgMember.user_id == User.id
        ).outerjoin(
            Conversation,
            (Conversation.assigned_agent_id == User.id) &
            (Conversation.status == ConversationStatus.ESCALATED) &
            (Conversation.deleted_at == None)
        ).filter(
            OrgMember.org_id == org_id,
            OrgMember.role.in_([OrgRole.OWNER, OrgRole.ADMIN]),
            User.deleted_at == None
        ).group_by(User.id).all()
        
        agent_escalated_counts = {user_id: count for user_id, count in agent_counts}

        if agent_escalated_counts:
            return min(agent_escalated_counts, key=agent_escalated_counts.get)
        
        # Fallback to org owner
        org = db.query(Organization).filter(Organization.id == org_id).first()
        return org.owner_id if org else None

    @classmethod
    def _record_and_broadcast(
        cls,
        db: Session,
        conversation: Conversation,
        chatbot: Chatbot,
        org_id: uuid.UUID,
        user_message: str,
        response_text: str,
        active_config_id: Optional[uuid.UUID],
        write_user_message: bool,
        is_new_conv: bool = False,
        is_escalation_event: bool = False,
        background_tasks: Optional[BackgroundTasks] = None
    ):
        import asyncio
        from app.services.sse_manager import sse_manager
        
        if write_user_message:
            user_msg = DBMessage(
                id=uuid.uuid4(),
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=user_message,
                config_id=active_config_id,
                created_at=datetime.now(timezone.utc),
            )
            db.add(user_msg)
            user_msg_id = str(user_msg.id)
            user_msg_created_at = user_msg.created_at
        else:
            last_msg = db.query(DBMessage).filter(
                DBMessage.conversation_id == conversation.id,
                DBMessage.role == MessageRole.USER
            ).order_by(DBMessage.created_at.desc()).first()
            if last_msg:
                user_msg_id = str(last_msg.id)
                user_msg_created_at = last_msg.created_at
            else:
                user_msg_id = str(uuid.uuid4())
                user_msg_created_at = datetime.now(timezone.utc)

        bot_msg = DBMessage(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.BOT,
            content=response_text,
            config_id=active_config_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(bot_msg)
        
        increment = 2 if write_user_message else 1
        db.query(Chatbot).filter(Chatbot.id == chatbot.id).update(
            {Chatbot.total_messages: Chatbot.total_messages + increment}
        )
        if is_new_conv:
            db.query(Chatbot).filter(Chatbot.id == chatbot.id).update(
                {Chatbot.total_conversations: Chatbot.total_conversations + 1}
            )
        
        db.commit()

        user_msg_data = {
            "conversation_id": str(conversation.id),
            "message": {
                "id": user_msg_id,
                "role": "user",
                "content": user_message,
                "created_at": user_msg_created_at.isoformat()
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
        
        escalation_event = None
        if is_escalation_event:
            escalation_event = {
                "conversation_id": str(conversation.id),
                "status": ConversationStatus.ESCALATED.value,
                "assigned_agent_id": str(conversation.assigned_agent_id) if conversation.assigned_agent_id else None,
                "chatbot_id": str(chatbot.id)
            }

        if background_tasks:
            background_tasks.add_task(sse_manager.broadcast, f"organization:{org_id}", "message", user_msg_data)
            background_tasks.add_task(sse_manager.broadcast, f"organization:{org_id}", "message", bot_msg_data)
            if escalation_event:
                background_tasks.add_task(sse_manager.broadcast, f"organization:{org_id}", "escalation", escalation_event)
        else:
            def _run_sse():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(sse_manager.broadcast(f"organization:{org_id}", "message", user_msg_data))
                    loop.run_until_complete(sse_manager.broadcast(f"organization:{org_id}", "message", bot_msg_data))
                    if escalation_event:
                        loop.run_until_complete(sse_manager.broadcast(f"organization:{org_id}", "escalation", escalation_event))
                except Exception as e:
                    logger.error(f"SSE broadcast failed in thread: {e}")
                finally:
                    loop.close()

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(sse_manager.broadcast(f"organization:{org_id}", "message", user_msg_data))
                loop.create_task(sse_manager.broadcast(f"organization:{org_id}", "message", bot_msg_data))
                if escalation_event:
                    loop.create_task(sse_manager.broadcast(f"organization:{org_id}", "escalation", escalation_event))
            except RuntimeError:
                import threading
                threading.Thread(target=_run_sse, daemon=True).start()

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
        sources: Optional[list] = None,
        write_user_message: bool = True,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Dict[str, Any]:
        """
        Escalates the conversation: assigns least busy agent, updates status,
        saves message, updates chatbot statistics, and broadcasts SSE events.
        """
        conversation.status = ConversationStatus.ESCALATED
        
        if not conversation.assigned_agent_id:
            conversation.assigned_agent_id = cls.find_least_busy_agent(db, org_id)
            
        db.add(conversation)
        
        cls._record_and_broadcast(
            db=db,
            conversation=conversation,
            chatbot=chatbot,
            org_id=org_id,
            user_message=user_message,
            response_text=response_text,
            active_config_id=active_config_id,
            write_user_message=write_user_message,
            is_new_conv=is_new_conv,
            is_escalation_event=True,
            background_tasks=background_tasks
        )
            
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
        active_config_id: Optional[uuid.UUID] = None,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Dict[str, Any]:
        """Handles messages sent to an already escalated conversation by bypassing standard RAG."""
        response_text = cls.get_escalation_message(language, user_message=user_message)
        
        cls._record_and_broadcast(
            db=db,
            conversation=conversation,
            chatbot=chatbot,
            org_id=org_id,
            user_message=user_message,
            response_text=response_text,
            active_config_id=active_config_id,
            write_user_message=True,
            is_new_conv=False,
            is_escalation_event=False,
            background_tasks=background_tasks
        )
            
        return {
            "response": response_text,
            "conversation_id": conversation.id,
            "sources": [],
            "status": ConversationStatus.ESCALATED
        }
