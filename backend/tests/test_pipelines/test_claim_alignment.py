"""Tests for claim-to-evidence alignment scoring."""
from app.pipelines.claim_alignment import score_claim_alignment
from app.schemas.interpretation import (
    AnswerBody,
    AnswerPayload,
    AnswerMetadata,
    CitationEntry,
    TimingWindow,
)


def _build_payload(include_citations: bool = True) -> AnswerPayload:
    answer = AnswerBody(
        general_profile="Mars in Aries indicates bold action. Leadership prominence remains a core theme.",
        strengths=["Strong leadership presence."],
        watchouts=["Impulsive decisions under pressure."],
        timing=[TimingWindow(range="2024-2025", note="Focus on career growth.")],
        collective_note="",
        mythic_refs=[],
    )
    citations = []
    if include_citations:
        citations = [
            CitationEntry(
                doc_id="doc123",
                section=0,
                line_start=0,
                line_end=0,
                tradition="modern",
                language="EN",
                source_url=None,
                snippet="Leadership prominence remains a core theme.",
            ),
            CitationEntry(
                doc_id="doc456",
                section=0,
                line_start=0,
                line_end=0,
                tradition="traditional",
                language="EN",
                source_url=None,
                snippet="Impulsive decisions under pressure may surface.",
            ),
        ]
        return AnswerPayload(
            answer=answer,
            citations=citations,
            confidence=0.8,
            limits=AnswerMetadata(),
        )

    return AnswerPayload.model_construct(
        answer=answer,
        citations=[],
        confidence=0.8,
        limits=AnswerMetadata(),
        evidence_summary=None,
    )


def _documents() -> list[dict]:
    return [
        {
            "source_id": "doc123",
            "content": (
                "Mars in Aries indicates bold action and strong leadership presence. "
                "Leadership prominence remains a core theme for sustained career growth. "
                "Focus on career growth to maximise opportunities in 2024-2025."
            ),
            "metadata": {"doc_id": "doc123"},
        },
        {
            "source_id": "doc456",
            "content": (
                "Impulsive decisions under pressure may surface; slow down to avoid rash choices."
            ),
            "metadata": {"doc_id": "doc456"},
        },
    ]


def test_score_claim_alignment_good_match():
    payload = _build_payload()
    result = score_claim_alignment(payload, _documents())

    assert result["score"] >= 0.9
    assert result["supported_ratio"] == 1.0
    assert len(result["claims"]) >= 4
    spans = [claim["span"] for claim in result["claims"] if claim["span"]]
    assert spans, "Expected at least one evidence span to be captured"


def test_score_claim_alignment_without_citations():
    payload = _build_payload(include_citations=False)
    result = score_claim_alignment(payload, _documents())

    assert result["score"] == 0.0
    assert result["reason"] == "no_citations"
    assert all(claim["score"] == 0.0 for claim in result["claims"])
