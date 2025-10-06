from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

VALID_SIGNS = (
    "koç",
    "boğa",
    "ikizler",
    "yengeç",
    "aslan",
    "başak",
    "terazi",
    "akrep",
    "yay",
    "oğlak",
    "kova",
    "balık",
)

VALID_TIMEFRAMES = ("bugün", "yarın", "bu hafta", "bu ay")


class BirthData(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    time: str = Field(pattern=r"^\d{2}:\d{2}$")
    tz: str = Field(min_length=1)
    lat: float | None = Field(default=None)
    lon: float | None = Field(default=None)


class HoroscopeRequest(BaseModel):
    burc: Literal[VALID_SIGNS]
    gun: str
    birth: BirthData
    user_id: Optional[str] = None
    goals: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_timeframe(cls, values: "HoroscopeRequest") -> "HoroscopeRequest":
        gun = values.gun
        if gun in VALID_TIMEFRAMES:
            return values
        if not _is_iso_date(gun):
            raise ValueError(
                "gun alanı 'bugün', 'yarın', 'bu hafta', 'bu ay' veya ISO tarih (YYYY-MM-DD) olmalıdır."
            )
        return values


class PlanetPosition(BaseModel):
    lon_deg: float
    house: int


class Aspect(BaseModel):
    from_: str = Field(alias="from")
    to: str
    type: Literal["conj", "sextile", "square", "trine", "opposition"]
    angle: float

    class Config:
        populate_by_name = True


class HoroscopeResponse(BaseModel):
    burc: str
    gun: str
    yorum: str
    confidence: float
    natal: Dict[str, object]
    transit: Dict[str, object]
    dominant_enerjiler: List[str]
    pratik_tavsiyeler: List[str]
    kaynaklar: List[Dict[str, str]]
    selected_model: str | None
    is_fallback: bool


def _is_iso_date(value: str) -> bool:
    parts = value.split("-")
    if len(parts) != 3:
        return False
    if not all(part.isdigit() for part in parts):
        return False
    year, month, day = (int(p) for p in parts)
    return 1 <= month <= 12 and 1 <= day <= 31 and year > 0
