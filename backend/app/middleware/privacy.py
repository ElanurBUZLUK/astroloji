"""PII-aware middleware for inbound requests."""
from __future__ import annotations

import json
import re
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


PII_FIELD_NAMES = {
    "birth_date",
    "birth_time",
    "birth_location",
    "birth_place",
    "birth_city",
    "birth_country",
    "date_of_birth",
    "time_of_birth",
    "latitude",
    "longitude",
}

DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
TIME_PATTERN = re.compile(r"\b\d{2}:\d{2}(?::\d{2})?\b")


class PIIMaskingMiddleware(BaseHTTPMiddleware):
    """Captures and redacts PII from request payloads for safe logging."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        body_bytes = await request.body()
        request._body = body_bytes

        if body_bytes:
            redacted_repr, redacted_obj = self._redact_payload(body_bytes)
            request.state.redacted_body = redacted_repr
            request.state.redacted_payload = redacted_obj

        response = await call_next(request)
        return response

    def _redact_payload(self, raw: bytes) -> tuple[str, Any]:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            text = raw.decode("utf-8", errors="ignore")
            masked = self._mask_text(text)
            return masked, masked

        redacted = self._mask_structure(parsed)
        return json.dumps(redacted), redacted

    def _mask_structure(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: "[REDACTED]" if self._is_pii_field(key) else self._mask_structure(val)
                for key, val in value.items()
            }
        if isinstance(value, list):
            return [self._mask_structure(item) for item in value]
        if isinstance(value, str):
            return self._mask_text(value)
        return value

    def _mask_text(self, value: str) -> str:
        masked = DATE_PATTERN.sub("[REDACTED]", value)
        masked = TIME_PATTERN.sub("[REDACTED]", masked)
        return masked

    def _is_pii_field(self, key: str) -> bool:
        return key.lower() in PII_FIELD_NAMES


__all__ = ["PIIMaskingMiddleware"]
