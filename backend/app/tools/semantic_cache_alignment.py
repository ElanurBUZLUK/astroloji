"""Utilities to inspect and align semantic cache entries."""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

from app.pipelines.cache import RedisSemanticCache
from backend.app.config import settings


class SemanticCacheAligner:
    def __init__(self, cache: RedisSemanticCache | None = None) -> None:
        self._cache = cache or RedisSemanticCache(settings.redis_url, ttl_seconds=settings.SEMANTIC_CACHE_TTL)

    async def list_keys(self) -> List[str]:
        redis = self._cache._redis  # type: ignore[attr-defined]
        keys = await redis.keys("*")
        return [key.decode("utf-8") if isinstance(key, bytes) else key for key in keys]

    async def get_entry(self, key: str) -> Dict[str, Any]:
        data = await self._cache.get(key)
        if not data:
            return {}
        return json.loads(json.dumps(data, default=str))

    async def compare(self, key_a: str, key_b: str) -> Dict[str, Any]:
        entry_a = await self.get_entry(key_a)
        entry_b = await self.get_entry(key_b)
        return {
            "key_a": key_a,
            "key_b": key_b,
            "equal": entry_a == entry_b,
            "diff_summary": {
                "payload_changed": entry_a.get("payload") != entry_b.get("payload"),
                "coverage_changed": entry_a.get("payload", {}).get("limits", {}).get("coverage_score")
                != entry_b.get("payload", {}).get("limits", {}).get("coverage_score"),
            },
        }


async def main() -> None:  # pragma: no cover - CLI helper
    aligner = SemanticCacheAligner()
    keys = await aligner.list_keys()
    print(f"Found {len(keys)} cache entries")
    for key in keys:
        entry = await aligner.get_entry(key)
        print(f"Key: {key} -> coverage: {entry.get('payload', {}).get('limits', {}).get('coverage_score')}")


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
