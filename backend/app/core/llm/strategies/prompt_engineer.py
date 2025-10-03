"""Prompt engineering helpers for interpretation generation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class PromptContext:
    language: str
    style: str
    mode: str
    coverage: Dict[str, Any]
    evidence_pack: Dict[str, Any]


class PromptEngineer:
    """Builds prompts according to style and coverage signals."""

    def build_messages(self, summary: str, context: PromptContext) -> List[Dict[str, str]]:
        system_prompt = self._system_prompt(context)
        user_prompt = self._user_prompt(summary, context)
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _system_prompt(self, context: PromptContext) -> str:
        base = {
            "en": "You are an expert astrologer who writes grounded, cited analysis.",
            "tr": "Temellere dayanan, kaynak gösteren uzman bir astrologsun.",
        }
        tone_map = {
            "technical": "Use precise terminology and assume advanced knowledge.",
            "accessible": "Use clear, encouraging language suitable for intermediate students.",
            "brief": "Respond concisely, focusing on the key points.",
            "detailed": "Provide a thorough, structured explanation with context and nuance.",
        }
        parts = [base.get(context.language, base["en"]), tone_map.get(context.style, tone_map["accessible"])]
        if not context.coverage.get("pass", True):
            parts.append("Flag gaps openly, invite the user to request more details.")
        return " " .join(parts)

    def _user_prompt(self, summary: str, context: PromptContext) -> str:
        components = [
            f"Mode: {context.mode}",
            f"Style: {context.style}",
            f"Coverage Score: {context.coverage.get('score', 'n/a')}",
            f"Conflicts: {len(context.evidence_pack.get('conflicts', []))}",
            "Summary:\n" + summary,
            "Requirements:\n- Keep claims tied to cited evidence.\n- Mention coverage gaps or conflicts explicitly.\n- Provide actionable guidance appropriate for the user level.",
        ]
        if context.evidence_pack.get("conflicts"):
            components.append("Conflicts detail:\n" + "\n".join(
                f"- {c['topic']}: {c['summary']}" for c in context.evidence_pack["conflicts"]
            ))
        return "\n\n".join(components)
