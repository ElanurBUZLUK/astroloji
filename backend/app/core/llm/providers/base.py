"""Base interfaces for LLM providers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class LLMResponse:
    content: str
    tokens_used: int
    raw: Dict[str, Any]
    finish_reason: Optional[str] = None


class LLMProvider:
    """Abstract provider interface so we can swap vendors easily."""

    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:  # pragma: no cover - interface
        raise NotImplementedError
