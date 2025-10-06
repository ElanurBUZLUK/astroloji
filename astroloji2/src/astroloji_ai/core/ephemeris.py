from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Tuple

from cachetools import TTLCache

from astroloji_ai.config.settings import EphemerisConfig
from astroloji_ai.monitoring.metrics import EPHEMERIS_CACHE_HIT, EPHEMERIS_CACHE_MISS

PlanetPositions = Dict[str, Dict[str, float | int]]


@dataclass(frozen=True)
class EphemerisKey:
    lat: float | None
    lon: float | None
    timestamp_hour: datetime


class EphemerisService:
    """Ephemeris hesaplamalarını (şimdilik) deterministik sahte verilerle sağlayan çekirdek."""

    def __init__(self, config: EphemerisConfig) -> None:
        self._config = config
        ttl_seconds = config.ttl_minutes * 60
        self._cache: TTLCache[EphemerisKey, Tuple[PlanetPositions, bool]] = TTLCache(
            maxsize=256, ttl=ttl_seconds
        )

    def get_positions(
        self,
        lat: float | None,
        lon: float | None,
        timestamp: datetime | None = None,
    ) -> Tuple[PlanetPositions, bool]:
        """Return planet positions and fallback marker."""

        timestamp = timestamp or datetime.now(timezone.utc)
        timestamp_hour = timestamp.replace(minute=0, second=0, microsecond=0)
        key = EphemerisKey(lat=lat, lon=lon, timestamp_hour=timestamp_hour)
        if key in self._cache:
            EPHEMERIS_CACHE_HIT.inc()
            return self._cache[key]

        positions, fallback = self._calculate_positions(lat, lon, timestamp)
        self._cache[key] = (positions, fallback)
        EPHEMERIS_CACHE_MISS.inc()
        return positions, fallback

    def _calculate_positions(
        self,
        lat: float | None,
        lon: float | None,
        timestamp: datetime,
    ) -> Tuple[PlanetPositions, bool]:
        """
        Çok kaba bir gezegen konumu hesaplayıcısı.

        Not: Bu versiyon, gerçek ephemeris verisi yerine deterministik sinüs tabanlı
        bir yaklaşım kullanır. Gerçek uygulamada Swiss Ephemeris veya Skyfield ile
        gezegen konumlarının hesaplanması gerekecek.
        """

        fallback = True  # gerçek hesap yapılmadığı için fallback olduğunu işaretle
        unix_hours = timestamp.timestamp() / 3600.0

        def fake_position(seed: int) -> float:
            return (math.sin(unix_hours / 24 + seed) * 180) % 360

        planets = (
            "Güneş",
            "Ay",
            "Merkür",
            "Venüs",
            "Mars",
            "Jüpiter",
            "Satürn",
        )
        positions: PlanetPositions = {}
        for idx, planet in enumerate(planets, start=1):
            lon_deg = round(fake_position(idx) % 360, 2)
            house = ((idx + int((lon or 0) // 30)) % 12) + 1 if lon is not None else ((idx % 12) + 1)
            positions[planet] = {"lon_deg": lon_deg, "house": house}

        # ASC / MC kabaca
        positions["ASC"] = {"lon_deg": round(fake_position(99), 2), "house": 1}
        positions["MC"] = {"lon_deg": round(fake_position(199), 2), "house": 10}
        return positions, fallback
