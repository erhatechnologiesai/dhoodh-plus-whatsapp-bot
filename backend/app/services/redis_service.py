import json
import time
from typing import Optional, Any, Dict, List
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import logger

class RedisService:
    """
    High-performance Redis Cache & State Manager for Dhoodh Plus AI:
    - Message Idempotency & Deduplication
    - Conversation History Caching
    - Fast RAG query cache
    - Rate limiting
    - Graceful in-memory fallback when Redis is offline or not configured
    """

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
        self._in_memory_cache: Dict[str, Any] = {}
        self._in_memory_expiry: Dict[str, float] = {}
        self._is_connected = False
        self._connection_attempted = False

    async def get_client(self) -> Optional[aioredis.Redis]:
        if not settings.REDIS_ENABLED:
            return None

        if self._client is not None and self._is_connected:
            return self._client

        redis_url = settings.REDIS_URL or "redis://localhost:6379/0"

        try:
            self._client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0
            )
            await self._client.ping()
            self._is_connected = True
            logger.info(f"Connected to Redis at: {redis_url.split('@')[-1] if '@' in redis_url else redis_url}")
            return self._client
        except Exception as e:
            self._is_connected = False
            if not self._connection_attempted:
                logger.info(f"Redis not available ({e}). Operating with resilient in-memory cache adapter.")
                self._connection_attempted = True
            return None

    # ----------------------------------------------------------------------
    # Core Cache Operations
    # ----------------------------------------------------------------------
    async def get(self, key: str) -> Optional[str]:
        client = await self.get_client()
        if client and self._is_connected:
            try:
                return await client.get(key)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
                self._is_connected = False

        # In-memory fallback
        exp = self._in_memory_expiry.get(key)
        if exp and time.time() > exp:
            self._in_memory_cache.pop(key, None)
            self._in_memory_expiry.pop(key, None)
            return None
        return self._in_memory_cache.get(key)

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        client = await self.get_client()
        if client and self._is_connected:
            try:
                if expire:
                    await client.setex(key, expire, value)
                else:
                    await client.set(key, value)
                return True
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
                self._is_connected = False

        # In-memory fallback
        self._in_memory_cache[key] = value
        if expire:
            self._in_memory_expiry[key] = time.time() + expire
        return True

    async def delete(self, key: str) -> bool:
        client = await self.get_client()
        if client and self._is_connected:
            try:
                await client.delete(key)
            except Exception:
                pass
        self._in_memory_cache.pop(key, None)
        self._in_memory_expiry.pop(key, None)
        return True

    async def get_json(self, key: str) -> Optional[Any]:
        val = await self.get(key)
        if val:
            try:
                return json.loads(val)
            except Exception:
                return None
        return None

    async def set_json(self, key: str, data: Any, expire: Optional[int] = None) -> bool:
        try:
            val = json.dumps(data)
            return await self.set(key, val, expire=expire)
        except Exception:
            return False

    # ----------------------------------------------------------------------
    # WhatsApp Specific Helpers
    # ----------------------------------------------------------------------
    async def check_and_set_idempotency(self, message_id: str, expire: int = 86400) -> bool:
        """
        Returns True if message is already processed (duplicate), False if newly recorded.
        """
        key = f"whatsapp:msg:{message_id}"
        existing = await self.get(key)
        if existing:
            return True
        await self.set(key, "1", expire=expire)
        return False

    async def cache_conversation_history(self, conversation_id: str, messages: List[Dict[str, str]], expire: int = 3600) -> bool:
        key = f"whatsapp:history:{conversation_id}"
        return await self.set_json(key, messages, expire=expire)

    async def get_cached_conversation_history(self, conversation_id: str) -> Optional[List[Dict[str, str]]]:
        key = f"whatsapp:history:{conversation_id}"
        return await self.get_json(key)

    async def get_status(self) -> Dict[str, Any]:
        client = await self.get_client()
        is_live = False
        latency_ms = None
        if client and self._is_connected:
            try:
                t0 = time.time()
                await client.ping()
                latency_ms = round((time.time() - t0) * 1000, 2)
                is_live = True
            except Exception:
                is_live = False

        return {
            "enabled": settings.REDIS_ENABLED,
            "connected": is_live,
            "adapter": "redis" if is_live else "in_memory_fallback",
            "latency_ms": latency_ms,
            "redis_url_configured": bool(settings.REDIS_URL),
            "in_memory_keys_count": len(self._in_memory_cache)
        }

redis_service = RedisService()
