"""Utilities for sanitizing retrieval content before LLM consumption."""
from __future__ import annotations

import re
from typing import Iterable

_SCRIPT_RE = re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL)
_STYLE_RE = re.compile(r"<style.*?>.*?</style>", re.IGNORECASE | re.DOTALL)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_EXTERNAL_LINK_RE = re.compile(r"https?://\S+", re.IGNORECASE)


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
    return [sanitize_text(item) for item in texts]
