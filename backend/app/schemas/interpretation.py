"""Interpretation payloads exchanged with clients."""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


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
    """Represents a single citation used in the answer."""

    n: int
    doc_id: str
    span: str
    title: Optional[str] = None
    source: Optional[str] = None


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
    evidence_summary: Optional[dict] = None
