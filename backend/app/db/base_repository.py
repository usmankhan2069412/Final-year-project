import uuid
from datetime import datetime
from typing import Type, TypeVar, Generic, List, Optional, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[T]:
        stmt = select(self.model).where(self.model.id == id)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at == None)  # noqa: E711
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession) -> List[T]:
        stmt = select(self.model)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at == None)  # noqa: E711
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, obj: T) -> T:
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def delete(self, db: AsyncSession, id: uuid.UUID) -> bool:
        obj = await self.get(db, id)
        if not obj:
            return False

        if hasattr(obj, "deleted_at"):
            obj.deleted_at = datetime.utcnow()
            await db.commit()
        else:
            await db.delete(obj)
            await db.commit()
        return True


class ConversationRepository(BaseRepository):
    def __init__(self):
        from app.models.conversation import Conversation
        super().__init__(Conversation)

    async def get_active_by_chatbot(self, db: AsyncSession, chatbot_id: uuid.UUID) -> List[Any]:
        stmt = select(self.model).where(
            self.model.chatbot_id == chatbot_id,
            self.model.deleted_at == None  # noqa: E711
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class MessageRepository(BaseRepository):
    def __init__(self):
        from app.models.conversation import Message
        super().__init__(Message)

    async def fetch_history(
        self, db: AsyncSession, conversation_id: uuid.UUID, start_date: datetime, end_date: datetime
    ) -> List[Any]:
        if start_date is None or end_date is None:
            raise ValueError(
                "Developer Error: partitioned message queries MUST include 'start_date' and 'end_date' "
                "parameters to enable partition pruning."
            )

        stmt = select(self.model).where(
            self.model.conversation_id == conversation_id,
            self.model.created_at >= start_date,
            self.model.created_at <= end_date
        ).order_by(self.model.created_at.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())
