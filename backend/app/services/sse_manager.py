import logging
from typing import Any
from app.services.pubsub import get_pubsub_backend

logger = logging.getLogger(__name__)

class SSEManager:
    def __init__(self):
        # Delegate to the selected PubSub backend
        self.pubsub = get_pubsub_backend()

    async def subscribe(self, org_id: str):
        return await self.pubsub.subscribe(org_id)

    async def unsubscribe(self, org_id: str, queue):
        await self.pubsub.unsubscribe(org_id, queue)

    async def broadcast(self, org_id: str, event_type: str, data: Any):
        await self.pubsub.publish(org_id, event_type, data)

sse_manager = SSEManager()
