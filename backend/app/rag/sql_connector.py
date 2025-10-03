"""SQL connector synthesising summaries from stored chart data."""
from __future__ import annotations

from typing import Dict, List


def summarize_timing(chart_data: Dict[str, any]) -> List[Dict[str, object]]:
    timing = chart_data.get("zodiacal_releasing", {}), chart_data.get("profection"), chart_data.get("firdaria")
    zr = chart_data.get("zodiacal_releasing", {})
    profection = chart_data.get("profection")
    firdaria = chart_data.get("firdaria")
    summary_lines = []
    if zr and zr.get("current_periods"):
        l1 = zr["current_periods"].get("l1")
        if l1:
            summary_lines.append(
                f"Current ZR L1 ruled by {l1.get('ruler')} ({l1.get('sign')}) peaking={l1.get('is_peak')}"
            )
        l2 = zr["current_periods"].get("l2")
        if l2:
            summary_lines.append(
                f"ZR L2 sub-period ruler {l2.get('ruler')} tone={l2.get('tone')}"
            )
    if profection:
        summary_lines.append(
            f"Annual profection activates house {profection.get('profected_house')} ({profection.get('profected_sign')}), "
            f"year lord {profection.get('year_lord')}"
        )
    if firdaria:
        major = firdaria.get("current_major", {})
        minor = firdaria.get("current_minor", {})
        if major:
            summary_lines.append(f"Firdaria major {major.get('lord')} through {major.get('end_date')}")
        if minor:
            summary_lines.append(f"Firdaria minor {minor.get('lord')} until {minor.get('end_date')}")

    if not summary_lines:
        return []

    content = " " .join(summary_lines)
    return [
        {
            "content": content,
            "score": 0.9,
            "source_id": "sql::timing_overview",
            "metadata": {
                "topic": "timing_overview",
                "school": "chart_data",
                "language": "en",
                "source": "sql_cache",
            },
            "method": "sql",
        }
    ]


def summarize_core(chart_data: Dict[str, any]) -> List[Dict[str, object]]:
    planets = chart_data.get("planets", {})
    almuten = chart_data.get("almuten", {})
    winner = almuten.get("winner")
    notes = []
    if winner:
        notes.append(f"Almuten Figuris: {winner}")
    for name in ["Sun", "Moon", "Mercury"]:
        planet_info = planets.get(name)
        if planet_info:
            notes.append(f"{name} in {planet_info.get('sign')} {planet_info.get('degree_in_sign')}°")
    if not notes:
        return []
    return [
        {
            "content": " | ".join(notes),
            "score": 0.75,
            "source_id": "sql::core_overview",
            "metadata": {
                "topic": "core_overview",
                "school": "chart_data",
                "language": "en",
                "source": "sql_cache",
            },
            "method": "sql",
        }
    ]
