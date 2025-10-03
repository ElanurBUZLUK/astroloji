"""Query planner that proposes follow-up retrieval steps."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PlanStep:
    step_type: str  # e.g. "kg", "sql"
    topic: str
    reason: str
    cost_ms: int = 150
    metadata: Dict[str, any] = field(default_factory=dict)


class QueryPlanner:
    """Simple planner that inspects coverage gaps and drafts follow-up steps."""

    def plan(self, main_elements: List[str], coverage: Dict[str, any]) -> List[PlanStep]:
        steps: List[PlanStep] = []
        issues = coverage.get("issues", [])
        topics = coverage.get("topics", [])

        for issue in issues:
            lower = issue.lower()
            if "zodiacal" in lower:
                steps.append(PlanStep("kg", "zodiacal_releasing", issue))
            elif "profection" in lower:
                steps.append(PlanStep("kg", "profection", issue))
            elif "firdaria" in lower:
                steps.append(PlanStep("kg", "firdaria", issue))
            elif "traditional" in lower:
                steps.append(PlanStep("kg", "traditional_sources", issue))
            elif "modern" in lower:
                steps.append(PlanStep("kg", "modern_sources", issue))
            elif "coverage score" in lower:
                if main_elements:
                    steps.append(PlanStep("kg", main_elements[0].lower(), issue))

        if not steps and main_elements:
            for element in main_elements[:2]:
                steps.append(PlanStep("kg", element.lower(), "boost coverage for key element"))

        if "zodiacal_releasing" in topics or "profection" in topics or "firdaria" in topics:
            steps.append(PlanStep("sql", "timing_overview", "enrich timing context from chart"))
        else:
            steps.append(PlanStep("sql", "core_overview", "summarize chart core placements"))

        # deduplicate
        unique = []
        seen = set()
        for step in steps:
            key = (step.step_type, step.topic)
            if key in seen:
                continue
            seen.add(key)
            unique.append(step)
        return unique
