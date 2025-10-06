"""Quality filter and fallback builder for RAG answer payloads."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence

from loguru import logger

from app.schemas import AnswerBody, AnswerPayload, CitationEntry, RAGAnswerRequest, TimingWindow
from app.pipelines.sanitization import sanitize_text

ASTRO_KEYWORDS = {
    "sun",
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "pluto",
    "asc",
    "ascendant",
    "house",
    "sign",
    "transit",
    "aspect",
    "retrograde",
}


@dataclass
class QualityThresholds:
    """Thresholds applied by the quality filter."""

    min_general_chars: int = 280
    min_general_sentences: int = 3
    min_strengths: int = 1
    min_watchouts: int = 1
    min_citations: int = 1
    min_signal_terms: int = 1


@dataclass
class AnswerQualityReport:
    """Outcome of running the quality filter."""

    passed: bool
    issues: List[str]

    @property
    def primary_issue(self) -> str:
        return self.issues[0] if self.issues else "ok"


class AnswerQualityFilter:
    """Evaluate generated payloads against basic quality heuristics."""

    SENTENCE_SPLIT = re.compile(r"[.!?]+")

    def __init__(self, thresholds: QualityThresholds | None = None) -> None:
        self._thresholds = thresholds or QualityThresholds()

    def evaluate(self, payload: AnswerPayload) -> AnswerQualityReport:
        issues: List[str] = []
        body = payload.answer
        general = (body.general_profile or "").strip()

        if len(general) < self._thresholds.min_general_chars:
            issues.append("general_profile_too_short")

        if self._count_sentences(general) < self._thresholds.min_general_sentences:
            issues.append("insufficient_sentences")

        signal_terms = self._signal_terms(general)
        if signal_terms < self._thresholds.min_signal_terms:
            issues.append("missing_astrology_signal")

        if len(body.strengths or []) < self._thresholds.min_strengths:
            issues.append("missing_strengths")

        if len(body.watchouts or []) < self._thresholds.min_watchouts:
            issues.append("missing_watchouts")

        if len(payload.citations or []) < self._thresholds.min_citations:
            issues.append("missing_citations")

        passed = not issues
        return AnswerQualityReport(passed=passed, issues=issues)

    def _count_sentences(self, text: str) -> int:
        tokens = [segment.strip() for segment in self.SENTENCE_SPLIT.split(text) if segment.strip()]
        return len(tokens)

    def _signal_terms(self, text: str) -> int:
        terms = {token.strip(" ,;:").lower() for token in text.split()}
        count = sum(1 for token in terms if token in ASTRO_KEYWORDS)
        return count


class TemplateFallbackBuilder:
    """Render a deterministic fallback payload when the quality filter fails."""

    def build(
        self,
        request: RAGAnswerRequest,
        interpretation_summary: Dict[str, Any],
        rag_response: Any,
        base_payload: AnswerPayload,
        issues: Sequence[str],
        coverage: Dict[str, Any] | None = None,
    ) -> AnswerPayload:
        language = (request.locale_settings.language or "en").lower()
        topics = interpretation_summary.get("main_themes") or []
        topics = [sanitize_text(str(topic)) for topic in topics if topic]
        if not topics:
            topics = [sanitize_text(request.query.strip()) or "Genel eğilim"]

        general_profile = self._general_profile(language, topics, issues)
        strengths = self._strengths(language, topics, base_payload.answer.strengths)
        watchouts = self._watchouts(language, topics, base_payload.answer.watchouts)
        timing = base_payload.answer.timing or []
        citations = self._citations(base_payload.citations, rag_response)

        metadata = base_payload.limits.model_copy(deep=True)
        metadata.coverage_ok = bool(coverage.get("pass")) if coverage else False
        metadata.hallucination_risk = "medium"

        note = base_payload.answer.collective_note or self._collective_note(language)
        mythic_refs = base_payload.answer.mythic_refs or []

        fallback_body = AnswerBody(
            general_profile=general_profile,
            strengths=strengths,
            watchouts=watchouts,
            timing=[TimingWindow(range=tw.range, note=tw.note) for tw in timing],
            collective_note=note,
            mythic_refs=mythic_refs,
        )

        try:
            fallback_payload = AnswerPayload(
                answer=fallback_body,
                citations=citations,
                confidence=min(base_payload.confidence, 0.55),
                limits=metadata,
                evidence_summary=base_payload.evidence_summary,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Fallback payload failed validation: %s", exc)
            raise
        return fallback_payload

    def _general_profile(self, language: str, topics: Sequence[str], issues: Sequence[str]) -> str:
        topic_text = ", ".join(topics[:3])
        if language.startswith("tr"):
            header = "Otomatik kalite denetimi devrede."
            body = (
                f"Sistem, güvenilirlik sinyali zayıf olduğu için şablon yanıtına döndü. "
                f"Güncel odak başlıkları: {topic_text}. "
                "Kaynaklara dayanarak ilerlemek için yeni veri veya ek soru sağlayabilirsiniz."
            )
        else:
            header = "Safety fallback engaged."
            body = (
                f"The pipeline detected low-confidence signals and served a templated outline instead. "
                f"Primary themes to monitor: {topic_text}. "
                "Provide extra context or ask for a refinement to unlock a richer analysis."
            )
        issue_hint = f" (issues: {', '.join(issues)})" if issues else ""
        return f"{header} {body}{issue_hint}"

    def _strengths(
        self,
        language: str,
        topics: Sequence[str],
        original: Iterable[str],
    ) -> List[str]:
        strengths = [sanitize_text(item) for item in original if item]
        if strengths:
            return strengths
        templates = []
        for topic in topics[:2]:
            if language.startswith("tr"):
                templates.append(f"{topic} konusunda öğrenmeye açık ve dayanıklı bir tutum sergilemek avantaj sağlar.")
            else:
                templates.append(f"Curiosity around {topic} helps build resilience and momentum.")
        if not templates:
            templates.append("Adaptability and reflective practice remain reliable assets.")
        return templates

    def _watchouts(
        self,
        language: str,
        topics: Sequence[str],
        original: Iterable[str],
    ) -> List[str]:
        watchouts = [sanitize_text(item) for item in original if item]
        if watchouts:
            return watchouts
        templates = []
        for topic in topics[:2]:
            if language.startswith("tr"):
                templates.append(f"{topic} alanında aşırıya kaçmamaya, dinlenme ve sınır belirlemeye dikkat edin.")
            else:
                templates.append(f"Watch for overextending yourself when navigating {topic}; pacing protects clarity.")
        if not templates:
            templates.append("Monitor energy levels and revisit plans if external feedback signals drift.")
        return templates

    def _citations(self, existing: Sequence[CitationEntry], rag_response: Any) -> List[CitationEntry]:
        if existing:
            return list(existing)
        documents = getattr(rag_response, "documents", None) or []
        citations: List[CitationEntry] = []
        for index, doc in enumerate(documents[:2]):
            metadata = doc.get("metadata") if isinstance(doc, dict) else getattr(doc, "metadata", {}) or {}
            snippet = doc.get("content", "") if isinstance(doc, dict) else getattr(doc, "content", "")
            chunk_id = metadata.get("chunk_id") or metadata.get("doc_id") or doc.get("doc_id") if isinstance(doc, dict) else getattr(doc, "source_id", f"doc-{index+1}")
            citations.append(
                CitationEntry(
                    doc_id=str(chunk_id or f"doc-{index+1}"),
                    section=int(metadata.get("section") or metadata.get("chunk_index") or index),
                    line_start=int(metadata.get("line_start") or 0),
                    line_end=int(metadata.get("line_end") or 0),
                    tradition=metadata.get("tradition"),
                    language=metadata.get("language"),
                    source_url=metadata.get("source_url"),
                    snippet=snippet[:200] if snippet else None,
                )
            )
        if not citations:
            citations.append(
                CitationEntry(
                    doc_id="fallback-doc",
                    section=0,
                    line_start=0,
                    line_end=0,
                    snippet="Fallback citation: pipeline returned templated guidance.",
                )
            )
        return citations

    def _collective_note(self, language: str) -> str:
        if language.startswith("tr"):
            return (
                "Bu yanıt otomatik güvenlik katmanı tarafından oluşturuldu. Yeni belgeler veya doğrudan sorular"
                " ile daha derin bir yorum talep edebilirsiniz."
            )
        return (
            "This answer comes from the safety fallback template. Supply additional documents or a focused prompt "
            "to unlock a richer interpretation."
        )
