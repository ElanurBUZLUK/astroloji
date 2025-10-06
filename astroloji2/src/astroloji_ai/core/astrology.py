from __future__ import annotations

from typing import Dict, List, Tuple

from astroloji_ai.config.settings import EphemerisConfig

PlanetPositions = Dict[str, Dict[str, float | int]]

ASPECT_ANGLES: Dict[str, float] = {
    "conj": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}


def calculate_aspects(positions: PlanetPositions, config: EphemerisConfig) -> List[Dict[str, float | str]]:
    planets = [p for p in positions.keys() if p not in {"ASC", "MC"}]
    aspects: List[Dict[str, float | str]] = []
    for idx, planet in enumerate(planets):
        lon_1 = float(positions[planet]["lon_deg"])
        for other in planets[idx + 1 :]:
            lon_2 = float(positions[other]["lon_deg"])
            angle = min(abs(lon_1 - lon_2), 360 - abs(lon_1 - lon_2))
            aspect_type = _match_aspect(angle, config.orb_deg)
            if aspect_type:
                aspects.append(
                    {
                        "from": planet,
                        "to": other,
                        "type": aspect_type,
                        "angle": round(angle, 2),
                    }
                )
    return aspects


def dominant_energies(positions: PlanetPositions) -> List[str]:
    """Basit yükselen-güneş-ay + ek vurgu seçicisi."""

    dominant: List[str] = []
    if "ASC" in positions:
        dominant.append(f"Yükselen {house_label(positions['ASC']['house'])}")
    if "Güneş" in positions:
        dominant.append(f"Güneş {zodiac_sign(positions['Güneş']['lon_deg'])}")
    if "Ay" in positions:
        dominant.append(f"Ay {zodiac_sign(positions['Ay']['lon_deg'])}")
    if "Mars" in positions:
        dominant.append(f"Mars {house_label(positions['Mars']['house'])}")
    if len(dominant) > 4:
        dominant = dominant[:4]
    return dominant


def zodiac_sign(longitude: float | int) -> str:
    signs = [
        "Koç",
        "Boğa",
        "İkizler",
        "Yengeç",
        "Aslan",
        "Başak",
        "Terazi",
        "Akrep",
        "Yay",
        "Oğlak",
        "Kova",
        "Balık",
    ]
    index = int((float(longitude) % 360) // 30)
    return signs[index]


def house_label(house_value: float | int) -> str:
    house = int(house_value)
    return f"{house}. ev"


def _match_aspect(angle: float, orb: float) -> str | None:
    for aspect, base_angle in ASPECT_ANGLES.items():
        if abs(angle - base_angle) <= orb:
            return aspect
    return None
