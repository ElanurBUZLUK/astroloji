"""API key authentication and rate limiting helpers for public endpoints."""
from __future__ import annotations

from typing import Optional, Set

from fastapi import Header, HTTPException, Request, status

from backend.app.auth.security import RateLimiter
from backend.app.config import settings
from app.evaluation.observability import observability
from app.evaluation.prometheus_bridge import (
    record_api_key_denied,
    record_api_key_success,
    record_rate_limit,
)

_api_rate_limiter = RateLimiter()


def _allowed_api_keys() -> Set[str]:
    raw_keys = getattr(settings, "RAG_API_KEYS", "") or ""
    keys: Set[str] = set()
    if isinstance(raw_keys, str):
        keys = {item.strip() for item in raw_keys.split(",") if item.strip()}
    elif isinstance(raw_keys, (list, tuple, set)):
        keys = {str(item).strip() for item in raw_keys if str(item).strip()}
    return keys


async def require_api_key(
    request: Request,
    api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> str:
    """Validate the provided API key and enforce per-minute rate caps."""
    allowed = _allowed_api_keys()
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API keys are not configured",
        )
    if not api_key or api_key not in allowed:
        record_api_key_denied(request.url.path if request.url else "unknown")
        observability.metrics.increment_counter(
            "api_key_denied_total",
            1,
            {"endpoint": request.url.path if request.url else "unknown"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    limit = max(1, int(getattr(settings, "RAG_RATE_LIMIT_PER_MINUTE", 10) or 10))
    identifier = f"{api_key}:{request.client.host if request.client else 'unknown'}"
    if not _api_rate_limiter.is_allowed(identifier, limit=limit, window=60):
        record_rate_limit(request.url.path if request.url else "unknown")
        observability.metrics.increment_counter(
            "api_rate_limit_exceeded_total",
            1,
            {"endpoint": request.url.path if request.url else "unknown"},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )

    observability.metrics.increment_counter(
        "api_key_valid_total",
        1,
        {"endpoint": request.url.path if request.url else "unknown"},
    )
    record_api_key_success(request.url.path if request.url else "unknown")
    return api_key
