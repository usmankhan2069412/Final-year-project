from typing import Dict
from fastapi import WebSocket
import uuid
import logging

logger = logging.getLogger(__name__)

import asyncio

class ConnectionManager:
    def __init__(self):
        # Maps user_id to their active WebSocket connection
        self.active_connections: Dict[uuid.UUID, WebSocket] = {}
        self.loop = None

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.loop = asyncio.get_running_loop()
        logger.info(f"WebSocket connected for user: {user_id}")

    def disconnect(self, user_id: uuid.UUID):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user: {user_id}")

    async def send_personal_message(self, message: dict, user_id: uuid.UUID):
        """Send a JSON message directly to a specific user's WebSocket connection."""
        websocket = self.active_connections.get(user_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending websocket message to {user_id}: {e}")
                self.disconnect(user_id)

manager = ConnectionManager()
