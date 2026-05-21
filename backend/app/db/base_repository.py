import uuid
from datetime import datetime
from typing import Type, TypeVar, Generic, List, Optional, Any
from sqlalchemy.orm import Session

T = TypeVar("T")

class BaseRepository(Generic[T]):
    """
    Base Repository class that provides common database CRUD helper operations.
    Enforces soft-delete exclusion if the model has a `deleted_at` field.
    """
    def __init__(self, model: Type[T]):
        self.model = model

    def get(self, db: Session, id: uuid.UUID) -> Optional[T]:
        query = db.query(self.model).filter(self.model.id == id)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at == None)  # noqa: E711
        return query.first()

    def get_all(self, db: Session) -> List[T]:
        query = db.query(self.model)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at == None)  # noqa: E711
        return query.all()

    def create(self, db: Session, obj: T) -> T:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, id: uuid.UUID) -> bool:
        obj = self.get(db, id)
        if not obj:
            return False
        
        if hasattr(obj, "deleted_at"):
            # Soft delete
            obj.deleted_at = datetime.utcnow()
            db.commit()
        else:
            # Hard delete for non-soft-deleted models
            db.delete(obj)
            db.commit()
        return True


class ConversationRepository(BaseRepository):
    def __init__(self):
        from app.models.conversation import Conversation
        super().__init__(Conversation)

    def get_active_by_chatbot(self, db: Session, chatbot_id: uuid.UUID) -> List[Any]:
        """Fetch all active conversations for a chatbot."""
        return db.query(self.model).filter(
            self.model.chatbot_id == chatbot_id,
            self.model.deleted_at == None  # noqa: E711
        ).all()


class MessageRepository(BaseRepository):
    def __init__(self):
        from app.models.conversation import Message
        super().__init__(Message)

    def fetch_history(
        self, db: Session, conversation_id: uuid.UUID, start_date: datetime, end_date: datetime
    ) -> List[Any]:
        """
        Fetch conversation history.
        Enforces date range parameters at runtime to guarantee partition pruning.
        """
        if start_date is None or end_date is None:
            raise ValueError(
                "Developer Error: partitioned message queries MUST include 'start_date' and 'end_date' "
                "parameters to enable partition pruning."
            )
            
        return db.query(self.model).filter(
            self.model.conversation_id == conversation_id,
            self.model.created_at >= start_date,
            self.model.created_at <= end_date
        ).order_by(self.model.created_at.asc()).all()
