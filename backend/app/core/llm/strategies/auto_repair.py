"""Simple guardrail auto-repair strategy."""
from __future__ import annotations

import json
from typing import Any, Dict


class AutoRepair:
    """Attempts to fix malformed JSON or missing fields in LLM responses."""

    REQUIRED_KEYS = {"answer", "citations", "confidence", "limits"}

    def repair(self, raw_content: str) -> Dict[str, Any]:
        try:
            data = json.loads(raw_content)
        except json.JSONDecodeError:
            # fallback: wrap raw text into structured object
            return {
                "answer": {"general_profile": raw_content, "strengths": [], "watchouts": [], "timing": []},
                "citations": [],
                "confidence": 0.0,
                "limits": {"coverage_ok": False, "hallucination_risk": "high"},
            }

        missing = self.REQUIRED_KEYS - set(data.keys())
        if missing:
            # Fill missing keys with safe defaults
            if "answer" not in data:
                data["answer"] = {"general_profile": "", "strengths": [], "watchouts": [], "timing": []}
            if "citations" not in data:
                data["citations"] = []
            if "confidence" not in data:
                data["confidence"] = 0.0
            if "limits" not in data:
                data["limits"] = {"coverage_ok": False, "hallucination_risk": "medium"}
        return data
