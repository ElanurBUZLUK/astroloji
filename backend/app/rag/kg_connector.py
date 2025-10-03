"""Knowledge graph connector returning canonical snippets."""
from __future__ import annotations

from typing import List, Dict

_KG_STORE: Dict[str, Dict[str, str]] = {
    "zodiacal_releasing": {
        "content": (
            "Zodiacal Releasing divides time into chapters ruled by the sign of the Lot of Spirit. "
            "Angular periods to Fortune mark peaks, while Loosing of the Bond resets the storyline."
        ),
        "metadata": {
            "topic": "zodiacal_releasing",
            "school": "traditional",
            "language": "en",
            "source": "kg_hellenistic",
        },
    },
    "profection": {
        "content": (
            "Annual profection advances the Ascendant one sign per year, activating the natal house and its ruler. "
            "The year-lord's condition colours the agenda for the profected topics."
        ),
        "metadata": {
            "topic": "profection",
            "school": "traditional",
            "language": "en",
            "source": "kg_traditional",
        },
    },
    "firdaria": {
        "content": (
            "Firdaria allocates planetary periods according to sect. Major lords set the overarching tone while minor lords modulate events."
        ),
        "metadata": {
            "topic": "firdaria",
            "school": "persian",
            "language": "en",
            "source": "kg_persian",
        },
    },
    "traditional_sources": {
        "content": "Traditional authors emphasise testimonies that repeat across time-lord systems, giving priority to planets with multiple dignities.",
        "metadata": {
            "topic": "methodology",
            "school": "traditional",
            "language": "en",
            "source": "kg_method",
        },
    },
    "modern_sources": {
        "content": "Modern practice blends psychological framing with classical timing, translating technical indicators into actionable coaching language.",
        "metadata": {
            "topic": "methodology",
            "school": "modern",
            "language": "en",
            "source": "kg_method",
        },
    },
}


def fetch(topic: str) -> List[Dict[str, object]]:
    entry = _KG_STORE.get(topic)
    if not entry:
        return []
    return [
        {
            "content": entry["content"],
            "score": 0.85,
            "source_id": f"kg::{topic}",
            "metadata": entry["metadata"],
            "method": "kg",
        }
    ]
