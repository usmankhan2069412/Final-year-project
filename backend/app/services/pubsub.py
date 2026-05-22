import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Set, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class PubSubBackend(ABC):
    @abstractmethod
    async def subscribe(self, channel: str) -> asyncio.Queue:
        """Subscribe to a channel and return an asyncio.Queue."""
        pass

    @abstractmethod
    async def unsubscribe(self, channel: str, queue: asyncio.Queue):
        """Unsubscribe a queue from a channel."""
        pass

    @abstractmethod
    async def publish(self, channel: str, event_type: str, data: Any):
        """Publish an event to a channel."""
        pass


class InMemoryPubSubBackend(PubSubBackend):
    def __init__(self):
        self.connections: Dict[str, Set[asyncio.Queue]] = {}

    async def subscribe(self, channel: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        if channel not in self.connections:
            self.connections[channel] = set()
        self.connections[channel].add(queue)
        logger.info(f"InMemoryPubSub: Subscribed to channel {channel}. Active local: {len(self.connections[channel])}")
        return queue

    async def unsubscribe(self, channel: str, queue: asyncio.Queue):
        if channel in self.connections:
            self.connections[channel].discard(queue)
            if not self.connections[channel]:
                del self.connections[channel]
        logger.info(f"InMemoryPubSub: Unsubscribed from channel {channel}")

    async def publish(self, channel: str, event_type: str, data: Any):
        if channel not in self.connections:
            return
        
        payload = {
            "event": event_type,
            "data": data
        }
        
        bad_queues = set()
        for queue in self.connections[channel]:
            try:
                queue.put_nowait(payload)
            except Exception as e:
                logger.warning(f"InMemoryPubSub: Failed to publish to queue on channel {channel}: {e}")
                bad_queues.add(queue)
                
        for q in bad_queues:
            await self.unsubscribe(channel, q)


class RedisPubSubBackend(PubSubBackend):
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.connections: Dict[str, Set[asyncio.Queue]] = {}
        self.listener_tasks: Dict[str, asyncio.Task] = {}
        self.redis_client = None

    async def _get_redis_client(self):
        if self.redis_client is None:
            import redis.asyncio as aioredis
            self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
        return self.redis_client

    async def subscribe(self, channel: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        if channel not in self.connections:
            self.connections[channel] = set()
        self.connections[channel].add(queue)
        
        # If this is the first subscription for this channel in this process, start the Redis listener
        if len(self.connections[channel]) == 1:
            task = asyncio.create_task(self._listen_to_channel(channel))
            self.listener_tasks[channel] = task
            logger.info(f"RedisPubSub: Started listener for channel {channel}")
            
        logger.info(f"RedisPubSub: Subscribed to channel {channel}. Active local: {len(self.connections[channel])}")
        return queue

    async def unsubscribe(self, channel: str, queue: asyncio.Queue):
        if channel in self.connections:
            self.connections[channel].discard(queue)
            if not self.connections[channel]:
                del self.connections[channel]
                # Stop the listener task since there are no more local subscribers
                task = self.listener_tasks.pop(channel, None)
                if task:
                    task.cancel()
                    logger.info(f"RedisPubSub: Stopped listener for channel {channel}")
        logger.info(f"RedisPubSub: Unsubscribed from channel {channel}")

    async def publish(self, channel: str, event_type: str, data: Any):
        client = await self._get_redis_client()
        payload = {
            "event": event_type,
            "data": data
        }
        await client.publish(channel, json.dumps(payload))
        logger.info(f"RedisPubSub: Published event {event_type} to channel {channel}")

    async def _listen_to_channel(self, channel: str):
        client = await self._get_redis_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        payload = json.loads(message["data"])
                        
                        # Forward to all local queues
                        if channel in self.connections:
                            bad_queues = set()
                            for queue in self.connections[channel]:
                                try:
                                    queue.put_nowait(payload)
                                except Exception as e:
                                    logger.warning(f"RedisPubSub: Failed to deliver locally: {e}")
                                    bad_queues.add(queue)
                            for q in bad_queues:
                                await self.unsubscribe(channel, q)
                    except Exception as e:
                        logger.error(f"RedisPubSub: Error parsing or routing message: {e}")
        except asyncio.CancelledError:
            # Clean up subscription on cancel
            await pubsub.unsubscribe(channel)
            await pubsub.close()
        except Exception as e:
            logger.error(f"RedisPubSub: Connection error in listener for channel {channel}: {e}")
            await asyncio.sleep(1)
            # Recreate task if still needed
            if channel in self.connections and self.connections[channel]:
                self.listener_tasks[channel] = asyncio.create_task(self._listen_to_channel(channel))


_backend: Optional[PubSubBackend] = None

def get_pubsub_backend() -> PubSubBackend:
    global _backend
    if _backend is None:
        if settings.PUB_SUB_BACKEND == "redis" and settings.REDIS_URL:
            logger.info("Initializing Redis PubSub backend")
            _backend = RedisPubSubBackend(settings.REDIS_URL)
        else:
            logger.info("Initializing InMemory PubSub backend")
            _backend = InMemoryPubSubBackend()
    return _backend
