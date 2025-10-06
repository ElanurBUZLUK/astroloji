"""Schemas for birth data and calculated chart primitives."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, ConfigDict, model_validator


class BirthData(BaseModel):
    """Structured birth information used by astro calculators."""

    date: str = Field(..., description="Birth date in ISO format YYYY-MM-DD")
    time: Optional[str] = Field(None, description="Birth time in HH:MM (24h)")
    tz: str = Field(..., description="Timezone identifier, e.g. Europe/Istanbul")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    lng: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")

    model_config = ConfigDict(str_strip_whitespace=True)

    @model_validator(mode="after")
    def _default_time(self) -> "BirthData":
        if self.time is None:
            object.__setattr__(self, "time", "12:00")
        return self

    def as_local_datetime(self) -> datetime:
        """Create a timezone-aware datetime in the user's locale."""
        try:
            tzinfo = ZoneInfo(self.tz)
        except Exception as exc:  # pragma: no cover - depends on tzdata availability
            raise ValueError(f"Unknown timezone '{self.tz}'") from exc
        return datetime.fromisoformat(f"{self.date}T{self.time}:00").replace(tzinfo=tzinfo)

    def as_utc_datetime(self) -> datetime:
        """Convert the birth datetime to UTC."""
        return self.as_local_datetime().astimezone(timezone.utc)


class NatalCore(BaseModel):
    """Key natal chart features consumed by the pipeline."""

    almuten_figuris: Optional[str] = None
    lights: dict = Field(default_factory=dict)
    angles: dict = Field(default_factory=dict)
    dignities: dict = Field(default_factory=dict)
    receptions: dict = Field(default_factory=dict)
    antiscia: list = Field(default_factory=list)
    midpoints: list = Field(default_factory=list)
    fixed_stars: list = Field(default_factory=list)
    asteroids_tno: list = Field(default_factory=list)
    uranian_tnp: list = Field(default_factory=list)


class TimingBundle(BaseModel):
    """Time lord and predictive technique outputs."""

    zr: dict = Field(default_factory=dict)
    profection: dict = Field(default_factory=dict)
    firdaria: dict = Field(default_factory=dict)
    progressions: dict = Field(default_factory=dict)
    solar_arc: dict = Field(default_factory=dict)
    transits_applying: list = Field(default_factory=list)
    returns: dict = Field(default_factory=dict)


class ScoredTheme(BaseModel):
    """Ranked thematic outputs derived from calculations."""

    theme: str
    score: float
    evidence: list = Field(default_factory=list)
    note: Optional[str] = None


class ChartContext(BaseModel):
    """Bundle of natal, timing and scored information for downstream use."""

    natal_core: NatalCore = Field(default_factory=NatalCore)
    timing_bundle: TimingBundle = Field(default_factory=TimingBundle)
    scored_themes: list[ScoredTheme] = Field(default_factory=list)
