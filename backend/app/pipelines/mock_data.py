"""Mock helpers used during Sprint 1 before calculators are wired in."""
from __future__ import annotations

from typing import Dict, Any


def sample_chart() -> Dict[str, Any]:
    """Return a deterministic chart payload for local testing."""
    return {
        "chart_id": "mock-chart",
        "planets": {
            "Sun": {"longitude": 84.5, "sign": "Gemini", "degree_in_sign": 24.5, "is_retrograde": False},
            "Moon": {"longitude": 210.3, "sign": "Scorpio", "degree_in_sign": 20.3, "is_retrograde": False},
            "Mercury": {"longitude": 75.2, "sign": "Gemini", "degree_in_sign": 15.2, "is_retrograde": False},
            "Venus": {"longitude": 45.8, "sign": "Taurus", "degree_in_sign": 15.8, "is_retrograde": False},
            "Mars": {"longitude": 315.1, "sign": "Aquarius", "degree_in_sign": 15.1, "is_retrograde": False},
            "Jupiter": {"longitude": 120.7, "sign": "Leo", "degree_in_sign": 0.7, "is_retrograde": False},
            "Saturn": {"longitude": 285.4, "sign": "Capricorn", "degree_in_sign": 15.4, "is_retrograde": False},
        },
        "houses": {
            "asc": 0.0,
            "mc": 270.0,
            "asc_sign": "Aries",
            "mc_sign": "Capricorn",
        },
        "almuten": {
            "winner": "Mercury",
            "scores": {
                "Sun": 8,
                "Moon": 6,
                "Mercury": 12,
                "Venus": 7,
                "Mars": 5,
                "Jupiter": 9,
                "Saturn": 10,
            },
            "tie_break_reason": None,
        },
        "zodiacal_releasing": {
            "lot_used": "Spirit",
            "current_periods": {
                "l1": {
                    "sign": "Leo",
                    "ruler": "Sun",
                    "start_date": "2020-01-01",
                    "end_date": "2039-01-01",
                    "is_peak": True,
                    "is_lb": False,
                    "tone": "positive",
                },
                "l2": {
                    "sign": "Virgo",
                    "ruler": "Mercury",
                    "start_date": "2023-01-01",
                    "end_date": "2024-07-01",
                    "is_peak": False,
                    "is_lb": False,
                    "tone": "neutral",
                },
            },
        },
        "profection": {
            "age": 33,
            "profected_house": 10,
            "profected_sign": "Capricorn",
            "year_lord": "Saturn",
            "activated_topics": ["career", "reputation", "authority", "public life"],
        },
        "firdaria": {
            "current_major": {
                "lord": "Jupiter",
                "start_date": "2020-01-01",
                "end_date": "2032-01-01",
            },
            "current_minor": {
                "lord": "Venus",
                "start_date": "2023-01-01",
                "end_date": "2024-05-01",
            },
        },
        "antiscia": {
            "summary": {"total_contacts": 3},
            "strongest_contacts": [
                {
                    "original_planet": "Sun",
                    "contacted_planet": "Moon",
                    "antiscia_type": "antiscia",
                    "orb": 0.8,
                },
                {
                    "original_planet": "Venus",
                    "contacted_planet": "Mars",
                    "antiscia_type": "contra_antiscia",
                    "orb": 1.2,
                },
            ],
        },
        "is_day_birth": True,
    }
