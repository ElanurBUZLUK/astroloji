"""Semantic cache implementations for pipeline reuse."""
from __future__ import annotations

import asyncio
import pickle
from typing import Any, Dict, Optional

try:  # pragma: no cover - optional dependency
    from redis import Redis  # type: ignore
    from redis.asyncio import Redis as AsyncRedis  # type: ignore
except Exception:  # pragma: no cover - redis optional
    Redis = None
    AsyncRedis = None


class SemanticCache:
    """In-memory async-friendly cache placeholder."""

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            return self._store.get(key)

    async def set(self, key: str, value: Any, ttl_factor: float | None = None) -> None:
        async with self._lock:
            self._store[key] = value

    async def invalidate(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)


class RedisSemanticCache(SemanticCache):
    """Redis backed semantic cache with pickle serialization."""

    def __init__(self, redis_url: str, ttl_seconds: int = 604800) -> None:
        if not AsyncRedis:
            raise RuntimeError("redis library not available")
        self._redis: AsyncRedis = AsyncRedis.from_url(redis_url, encoding=None)
        self._ttl = ttl_seconds

    async def get(self, key: str) -> Optional[Any]:
        try:
            raw = await self._redis.get(key)
        except Exception:
            return None
        if raw is None:
            return None
        try:
            return pickle.loads(raw)
        except Exception:
            await self.invalidate(key)
            return None

    async def set(self, key: str, value: Any, ttl_factor: float | None = None) -> None:
        data = pickle.dumps(value)
        try:
            ttl = self._ttl
            if ttl_factor is not None and ttl:
                ttl = int(ttl * max(ttl_factor, 0.1))
            await self._redis.set(key, data, ex=ttl)
        except Exception:
            pass

    async def invalidate(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except Exception:
            pass
