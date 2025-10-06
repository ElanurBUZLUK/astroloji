"""Utilities for sanitizing retrieval content before LLM consumption."""
from __future__ import annotations

import re
from typing import Iterable

from app.schemas.interpretation import AnswerBody

_SCRIPT_RE = re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL)
_STYLE_RE = re.compile(r"<style.*?>.*?</style>", re.IGNORECASE | re.DOTALL)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_EXTERNAL_LINK_RE = re.compile(r"https?://\S+", re.IGNORECASE)

_PII_PATTERNS = [
    re.compile(r"\b\d{11}\b"),  # Turkish national ID length
    re.compile(r"(?i)T\.?C\.?\s*Kimlik\s*No?"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{2}:\d{2}(?::\d{2})?\b"),
    re.compile(r"(?i)lat(itude)?[:\s]*[-+]?\d+\.\d+"),
    re.compile(r"(?i)lon(gitude)?[:\s]*[-+]?\d+\.\d+"),
]

_SENSITIVE_PATTERN = re.compile(
    r"(?i)(sağlık|hastalık|tedavi|ilaç|finans|para kazan|borsa|yatırım|diagnos|medical)"
)
_ETHICS_NOTICE = (
    "**Uyarı:** Bu yorumlar eğlence ve kişisel farkındalık amaçlıdır; "
    "sağlık veya finans kararları için profesyonel danışmanlık alınız."
)


def sanitize_text(text: str) -> str:
    """Remove executable HTML/JS and neutralize external links."""
    if not text:
        return text
    cleaned = _SCRIPT_RE.sub("", text)
    cleaned = _STYLE_RE.sub("", cleaned)
    cleaned = _HTML_TAG_RE.sub(" ", cleaned)
    cleaned = _EXTERNAL_LINK_RE.sub("[external-link]", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def sanitize_sequence(texts: Iterable[str]) -> list[str]:
    """Sanitize a batch of strings, preserving ordering."""
    return [sanitize_text(item) for item in texts]


def mask_pii(text: str) -> str:
    """Redact high-sensitivity tokens from output text."""
    if not text:
        return text
    masked = text
    for pattern in _PII_PATTERNS:
        masked = pattern.sub("***", masked)
    return masked


def apply_ethics_notice(text: str) -> str:
    """Append ethics disclaimer when sensitive topics detected."""
    if not text:
        return text
    masked = mask_pii(text)
    if _SENSITIVE_PATTERN.search(masked) and _ETHICS_NOTICE not in masked:
        masked = masked.rstrip() + "\n\n" + _ETHICS_NOTICE
    return masked


def apply_answer_safeguards(body: AnswerBody) -> AnswerBody:
    """Mask PII and attach ethical notices across the answer body."""

    body.general_profile = apply_ethics_notice(body.general_profile)
    body.strengths = [mask_pii(item) for item in body.strengths]
    body.watchouts = [apply_ethics_notice(item) for item in body.watchouts]
    body.mythic_refs = [mask_pii(item) for item in body.mythic_refs]

    sanitized_timing = []
    for window in body.timing:
        window.range = mask_pii(window.range)
        if window.note:
            window.note = apply_ethics_notice(window.note)
        sanitized_timing.append(window)
    body.timing = sanitized_timing

    if body.collective_note:
        body.collective_note = apply_ethics_notice(body.collective_note)

    return body
