"""Interpretation payloads exchanged with clients."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class AnswerSection(BaseModel):
    """Individual section of the generated answer."""

    title: str
    content: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    priority: Optional[str] = None


class TimingWindow(BaseModel):
    """Explicit timing range returned by the pipeline."""

    range: str
    note: Optional[str] = None


class AnswerBody(BaseModel):
    """Structured fields that the client renders."""

    general_profile: str
    strengths: List[str]
    watchouts: List[str]
    timing: List[TimingWindow] = Field(default_factory=list)
    collective_note: Optional[str] = None
    mythic_refs: List[str] = Field(default_factory=list)


class CitationEntry(BaseModel):
    """Required citation metadata for each evidence item in responses."""

    doc_id: str = Field(..., min_length=1)
    section: int = Field(..., ge=0)
    line_start: int = Field(..., ge=0)
    line_end: int = Field(..., ge=0)
    paragraph: Optional[int] = Field(default=None, ge=0)
    tradition: Optional[str] = Field(
        default=None, description="e.g., Hellenistic, Medieval, Modern"
    )
    language: Optional[str] = Field(default=None, description="TR/EN etc.")
    source_url: Optional[str] = None
    snippet: Optional[str] = Field(
        default=None, description="Short preview of the cited text."
    )


class AnswerMetadata(BaseModel):
    """Meta information about the generation run."""

    coverage_ok: bool = True
    hallucination_risk: Optional[str] = None
    processing_time_ms: Optional[int] = None
    latency_budget_ms: Optional[int] = None
    coverage_score: Optional[float] = None
    citation_alignment: Optional[float] = None
    claims_supported_ratio: Optional[float] = None


class AnswerPayload(BaseModel):
    """Composite response returned to clients."""

    answer: AnswerBody
    citations: List[CitationEntry] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limits: AnswerMetadata = Field(default_factory=AnswerMetadata)
    evidence_summary: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def _validate_citations_non_empty(cls, payload: "AnswerPayload") -> "AnswerPayload":
        if not payload.citations:
            raise ValueError("citations must include at least one entry with doc_id/section/line range")
        return payload

    class Config:
        validate_assignment = True
