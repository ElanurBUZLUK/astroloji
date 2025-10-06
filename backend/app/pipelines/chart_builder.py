"""Chart bootstrapper that prepares natal/timing data for the RAG pipeline."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, date, timezone
from typing import Any, Dict, Optional

from zoneinfo import ZoneInfo

from app.calculators import (
    EphemerisService,
    Point,
    almuten_figuris,
    ZRCalculator,
    ProfectionCalculator,
    FirdariaCalculator,
    AntisciaCalculator,
    ProgressionsCalculator,
    SolarArcCalculator,
    TransitsCalculator,
    MidpointsCalculator,
    FixedStarsCalculator,
)
from backend.app.config import settings
from app.schemas import BirthData, ChartContext, NatalCore, TimingBundle


@dataclass
class ChartBuildResult:
    """Container with raw chart data used by the interpretation engine."""

    chart_data: Dict[str, Any]
    context: ChartContext


class ChartBootstrapper:
    """High level orchestrator that caches and returns chart calculations."""

    def __init__(self, cache_ttl: int | None = None) -> None:
        """Initialize the bootstrapper with an in-memory TTL cache."""
        self._ttl = cache_ttl or settings.CACHE_TTL_SECONDS
        self._cache: Dict[str, tuple[float, ChartBuildResult]] = {}

    async def load(self, birth_data: Optional[BirthData]) -> ChartBuildResult:
        """Return chart data/context for given birth input (or empty)."""
        if not birth_data:
            empty = ChartBuildResult(chart_data={}, context=ChartContext())
            return empty

        key = self._fingerprint(birth_data)
        now = time.time()
        cached = self._cache.get(key)
        if cached and now - cached[0] < self._ttl:
            return cached[1]

        chart_result = self._compute_chart(birth_data)
        self._cache[key] = (now, chart_result)
        return chart_result

    def _compute_chart(self, birth_data: BirthData) -> ChartBuildResult:
        """Run all calculators to produce chart data and rendered context objects."""
        birth_dt = self._to_datetime(birth_data)
        ephemeris = EphemerisService()

        zr_calc = ZRCalculator()
        profection_calc = ProfectionCalculator()
        firdaria_calc = FirdariaCalculator()
        antiscia_calc = AntisciaCalculator()
        progressions_calc = ProgressionsCalculator()
        solar_arc_calc = SolarArcCalculator()
        transits_calc = TransitsCalculator()
        midpoints_calc = MidpointsCalculator()
        fixed_stars_calc = FixedStarsCalculator()

        try:
            jd = ephemeris.julian_day(birth_dt)
            planets = ephemeris.get_all_planets(jd)
            houses = ephemeris.get_houses(jd, birth_data.lat, birth_data.lng)
            is_day = ephemeris.is_day_birth(planets, houses)
            lots = ephemeris.calculate_lots(planets, houses, is_day)

            almuten_points = self._prepare_almuten_points(planets, houses, lots)
            almuten_result = almuten_figuris(almuten_points, {"is_day": is_day})

            zr_timeline = zr_calc.compute_zr_timeline(
                planets["Sun"].longitude,
                planets["Moon"].longitude,
                houses.asc,
                is_day,
                date.fromisoformat(birth_data.date),
            )

            profection_result = profection_calc.calculate_profection(
                date.fromisoformat(birth_data.date),
                houses.asc,
            )

            firdaria_result = firdaria_calc.get_current_firdaria(
                date.fromisoformat(birth_data.date),
                is_day,
            )

            planet_longitudes = {name: pos.longitude for name, pos in planets.items()}
            planet_longitudes["ASC"] = houses.asc
            planet_longitudes["MC"] = houses.mc

            antiscia_result = antiscia_calc.get_antiscia_summary(planet_longitudes)
            progressions_result = progressions_calc.get_current_progressions(
                planet_longitudes, date.fromisoformat(birth_data.date)
            )
            solar_arc_result = solar_arc_calc.get_current_solar_arc_directions(
                planet_longitudes, date.fromisoformat(birth_data.date)
            )
            transits_result = transits_calc.get_major_transits(
                planet_longitudes, planet_longitudes
            )
            midpoints_result = midpoints_calc.get_major_midpoints_summary(planet_longitudes)
            fixed_stars_result = fixed_stars_calc.get_star_contacts_summary(planet_longitudes)

            chart_data = {
                "planets": {
                    name: {
                        "longitude": pos.longitude,
                        "sign": pos.sign,
                        "degree_in_sign": pos.degree_in_sign,
                        "is_retrograde": pos.is_retrograde,
                        "speed": pos.speed_longitude,
                    }
                    for name, pos in planets.items()
                },
                "houses": {
                    "system": "placidus",
                    "cusps": houses.cusps,
                    "asc": houses.asc,
                    "mc": houses.mc,
                    "asc_sign": self._longitude_to_sign(houses.asc),
                    "mc_sign": self._longitude_to_sign(houses.mc),
                },
                "almuten": {
                    "winner": almuten_result.winner,
                    "scores": almuten_result.scores,
                    "tie_break_reason": almuten_result.tie_break_reason,
                    "diagnostics": almuten_result.diagnostics,
                },
                "zodiacal_releasing": {
                    "lot_used": zr_timeline.lot_used,
                    "current_periods": self._current_zr_periods(
                        zr_timeline, datetime.utcnow().date()
                    ),
                    "next_peaks": self._next_zr_peaks(zr_timeline, datetime.utcnow().date()),
                    "diagnostics": zr_timeline.diagnostics,
                },
                "profection": {
                    "age": profection_result.age,
                    "profected_house": profection_result.profected_house,
                    "profected_sign": profection_result.profected_sign,
                    "year_lord": profection_result.year_lord,
                    "activated_topics": profection_result.activated_topics,
                },
                "firdaria": firdaria_result,
                "antiscia": {
                    "summary": antiscia_result["summary"],
                    "strongest_contacts": antiscia_calc.get_strongest_antiscia_contacts(
                        planet_longitudes, limit=3
                    ),
                },
                "progressions": progressions_result,
                "solar_arc": solar_arc_result,
                "transits": transits_result,
                "midpoints": midpoints_result,
                "fixed_stars": fixed_stars_result,
                "lots": lots,
                "is_day_birth": is_day,
                "ephemeris_status": ephemeris.status,
            }

            context = ChartContext(
                natal_core=NatalCore(
                    almuten_figuris=almuten_result.winner,
                    lights={
                        "Sun": chart_data["planets"].get("Sun", {}),
                        "Moon": chart_data["planets"].get("Moon", {}),
                    },
                    angles={
                        "ASC": {
                            "longitude": houses.asc,
                            "sign": chart_data["houses"]["asc_sign"],
                        },
                        "MC": {
                            "longitude": houses.mc,
                            "sign": chart_data["houses"]["mc_sign"],
                        },
                    },
                    dignities=almuten_result.scores,
                    antiscia=chart_data["antiscia"]["strongest_contacts"],
                    midpoints=midpoints_result.get("major_midpoints", []),
                    fixed_stars=fixed_stars_result.get("royal_star_contacts", []),
                ),
                timing_bundle=TimingBundle(
                    zr=chart_data["zodiacal_releasing"],
                    profection=chart_data["profection"],
                    firdaria=chart_data["firdaria"],
                    progressions=chart_data["progressions"],
                    solar_arc=chart_data["solar_arc"],
                    transits_applying=chart_data["transits"].get(
                        "major_current_transits", []
                    ),
                    returns={},
                ),
            )

            return ChartBuildResult(chart_data=chart_data, context=context)
        finally:
            ephemeris.close()

    def _fingerprint(self, birth_data: BirthData) -> str:
        """Build a deterministic cache key from birth data fields."""
        payload = {
            "date": birth_data.date,
            "time": birth_data.time or "12:00",
            "tz": birth_data.tz,
            "lat": birth_data.lat,
            "lng": birth_data.lng,
        }
        return json.dumps(payload, sort_keys=True)

    def _to_datetime(self, birth_data: BirthData) -> datetime:
        """Convert birth inputs into a timezone-aware datetime."""
        birth_date = date.fromisoformat(birth_data.date)
        if birth_data.time:
            hour, minute = (int(part) for part in birth_data.time.split(":")[:2])
        else:
            hour, minute = 12, 0
        naive_dt = datetime(
            birth_date.year,
            birth_date.month,
            birth_date.day,
            hour,
            minute,
        )
        try:
            tzinfo = ZoneInfo(birth_data.tz)
        except Exception:  # pragma: no cover - depends on tzdata availability
            tzinfo = timezone.utc
        return naive_dt.replace(tzinfo=tzinfo)

    def _prepare_almuten_points(self, planets: Dict[str, Any], houses: Any, lots: Dict[str, float]) -> list[Point]:
        """Gather the key points needed to compute the almuten figuris."""
        return [
            Point(
                "Sun",
                planets["Sun"].longitude,
                planets["Sun"].sign,
                planets["Sun"].degree_in_sign,
            ),
            Point(
                "Moon",
                planets["Moon"].longitude,
                planets["Moon"].sign,
                planets["Moon"].degree_in_sign,
            ),
            Point("ASC", houses.asc, self._longitude_to_sign(houses.asc), houses.asc % 30),
            Point("MC", houses.mc, self._longitude_to_sign(houses.mc), houses.mc % 30),
            Point(
                "Fortune",
                lots["Fortune"],
                self._longitude_to_sign(lots["Fortune"]),
                lots["Fortune"] % 30,
            ),
            Point(
                "Spirit",
                lots["Spirit"],
                self._longitude_to_sign(lots["Spirit"]),
                lots["Spirit"] % 30,
            ),
        ]

    def _longitude_to_sign(self, longitude: float) -> str:
        """Translate an ecliptic longitude into its zodiac sign name."""
        signs = [
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
        ]
        return signs[int(longitude % 360 // 30)]

    def _current_zr_periods(self, timeline: Any, current_date: date) -> Dict[str, Any]:
        """Select the active L1 and L2 zodiacal releasing periods."""
        current_l1 = None
        current_l2 = None
        for period in timeline.l1_periods:
            if period.start_date <= current_date <= period.end_date:
                current_l1 = {
                    "level": period.level,
                    "sign": period.sign,
                    "ruler": period.ruler,
                    "start_date": period.start_date.isoformat(),
                    "end_date": period.end_date.isoformat(),
                    "is_peak": period.is_peak,
                    "is_lb": period.is_lb,
                    "tone": period.tone,
                }
                break
        for period in timeline.l2_periods:
            if period.start_date <= current_date <= period.end_date:
                current_l2 = {
                    "level": period.level,
                    "sign": period.sign,
                    "ruler": period.ruler,
                    "start_date": period.start_date.isoformat(),
                    "end_date": period.end_date.isoformat(),
                    "is_peak": period.is_peak,
                    "is_lb": period.is_lb,
                    "tone": period.tone,
                }
                break
        return {"l1": current_l1, "l2": current_l2}

    def _next_zr_peaks(self, timeline: Any, current_date: date) -> list[Dict[str, Any]]:
        """Return the next few major ZR peaks after the current date."""
        next_peaks: list[Dict[str, Any]] = []
        for period in timeline.l1_periods:
            if period.is_peak and period.start_date > current_date:
                next_peaks.append(
                    {
                        "level": period.level,
                        "sign": period.sign,
                        "ruler": period.ruler,
                        "start_date": period.start_date.isoformat(),
                        "end_date": period.end_date.isoformat(),
                        "years_from_now": (period.start_date - current_date).days / 365.25,
                    }
                )
                if len(next_peaks) >= 3:
                    break
        return next_peaks
