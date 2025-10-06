"""Centralised logging configuration using loguru with PII safeguards."""
from __future__ import annotations

import re
import sys
from typing import Any

from loguru import logger

from .config import Settings


PII_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),  # ISO dates
    re.compile(r"\b\d{2}:\d{2}(?::\d{2})?\b"),  # times
    re.compile(r"\b\d{1,3}\.\d{2,}\b"),  # coordinates
]

PII_FIELD_PATTERN = re.compile(
    r"(?i)(birth[_\s]?(date|time|place|location)|timezone|latitude|longitude)"
)


def _mask_text(value: str) -> str:
    masked = value
    for pattern in PII_PATTERNS:
        masked = pattern.sub("[REDACTED]", masked)
    return masked


def _patch_record(record: dict[str, Any]) -> None:
    message = record.get("message", "")
    if isinstance(message, str):
        record["message"] = _mask_text(message)

    extras = record.get("extra", {})
    for key, val in list(extras.items()):
        if isinstance(val, str):
            extras[key] = _mask_text(val)
        elif isinstance(val, dict):
            extras[key] = _mask_dict(val)


def _mask_dict(data: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str) and PII_FIELD_PATTERN.search(key):
            redacted[key] = "[REDACTED]"
        elif isinstance(value, str):
            redacted[key] = _mask_text(value)
        elif isinstance(value, dict):
            redacted[key] = _mask_dict(value)
        else:
            redacted[key] = value
    return redacted


def setup_logging(settings: Settings) -> None:
    """Configure loguru logging with redaction."""
    logger.remove()
    logger.configure(patcher=_patch_record)
    logger.add(
        sys.stdout,
        level=settings.log_level.upper(),
        backtrace=settings.debug,
        diagnose=settings.debug,
        enqueue=False,
    )
    logger.info("Logging configured", settings=settings.describe())


__all__ = ["setup_logging"]
