"""Shared Pydantic models used across API schemas."""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, validator


class ConstraintSettings(BaseModel):
    """User provided latency/cost/token constraints."""

    max_latency_ms: Optional[int] = Field(
        default=1600,
        ge=100,
        le=10_000,
        description="Upper latency budget in milliseconds.",
    )
    max_cost_usd: Optional[float] = Field(
        default=0.10,
        ge=0.0,
        description="Maximum API cost the request is allowed to incur in USD.",
    )
    max_tokens: Optional[int] = Field(
        default=3000,
        ge=200,
        le=12_000,
        description="Soft limit for generated tokens.",
    )


class SessionContext(BaseModel):
    """Identifiers that let us thread conversation history and telemetry."""

    user_id: Optional[str] = Field(default=None, max_length=64)
    conversation_id: Optional[str] = Field(default=None, max_length=64)


class ABProfile(BaseModel):
    """Controls how the pipeline balances quality and cost for experimentation."""

    profile: Literal["quality-first", "cost-first", "balanced"] = "balanced"


class LocaleSettings(BaseModel):
    """Language and locale preferences."""

    locale: Literal["tr-TR", "en-US"] = "en-US"
    user_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"

    @property
    def language(self) -> str:
        return "tr" if self.locale.startswith("tr") else "en"


class ModeSettings(BaseModel):
    """Interpretation mode the caller is interested in."""

    mode: Literal[
        "natal",
        "transit",
        "technique",
        "definition",
        "synastry",
        "mixed",
    ] = "natal"

    @validator("mode")
    def _normalise_mode(cls, value: str) -> str:  # noqa: D401, N805
        """Lower-case and strip whitespace so callers can pass NATAl / Natal etc."""
        return value.lower().strip()
