"""Schema helpers for birth input normalization."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class BirthInput(BaseModel):
    """Client-facing birth payload with timezone normalization helpers."""

    date: str = Field(..., description="Birth date in YYYY-MM-DD format", example="1992-07-21")
    time: Optional[str] = Field(None, description="Birth time in HH:MM (24h)", example="14:35")
    tz: str = Field(..., description="IANA timezone identifier", example="Europe/Istanbul")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    house: str = Field("P", description="Requested house system code (P=Placidus, W=Whole Sign)")
    orb: float = Field(6.0, ge=0.0, le=12.0, description="Aspect orb allowance in degrees")

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("date")
    @classmethod
    def _validate_date(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("date must be in YYYY-MM-DD format") from exc
        return value

    @field_validator("time")
    @classmethod
    def _validate_time(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError as exc:
            raise ValueError("time must be in HH:MM 24h format") from exc
        return value

    @field_validator("house")
    @classmethod
    def _validate_house(cls, value: str) -> str:
        normalized = (value or "P").upper()
        if normalized not in {"P", "W"}:
            raise ValueError("house must be 'P' (Placidus) or 'W' (Whole Sign)")
        return normalized

    @model_validator(mode="after")
    def _default_time(self) -> "BirthInput":
        if self.time is None:
            object.__setattr__(self, "time", "12:00")
        return self

    @property
    def dt_local(self) -> datetime:
        """Local datetime aware of the provided timezone."""
        try:
            tzinfo = ZoneInfo(self.tz)
        except Exception as exc:  # pragma: no cover - depends on system tzdata
            raise ValueError(f"Unknown timezone '{self.tz}'") from exc
        naive = datetime.fromisoformat(f"{self.date}T{self.time}:00")
        return naive.replace(tzinfo=tzinfo)

    @property
    def dt_utc(self) -> datetime:
        """Birth datetime converted to UTC."""
        return self.dt_local.astimezone(timezone.utc)

    def to_birth_data(self):
        """Convert to the internal BirthData used by downstream pipelines."""
        from app.schemas.chart import BirthData

        return BirthData(
            date=self.date,
            time=self.time,
            tz=self.tz,
            lat=self.lat,
            lng=self.lon,
        )

