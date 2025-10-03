"""Request/response schemas for the RAG answer endpoint."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.chart import BirthData, ChartContext
from app.schemas.common import ConstraintSettings, SessionContext, ABProfile, LocaleSettings, ModeSettings
from app.schemas.interpretation import AnswerPayload


class RAGAnswerRequest(BaseModel):
    """Top level request contract for /rag/answer."""

    query: str = Field(..., min_length=3, max_length=2000)
    birth_data: Optional[BirthData] = None
    locale_settings: LocaleSettings = Field(default_factory=LocaleSettings)
    mode_settings: ModeSettings = Field(default_factory=ModeSettings)
    constraints: ConstraintSettings = Field(default_factory=ConstraintSettings)
    ab_flags: ABProfile = Field(default_factory=ABProfile)
    session: SessionContext = Field(default_factory=SessionContext)


class PipelineDebugInfo(BaseModel):
    """Shallow debug information we may expose for observability in dev."""

    intent: Optional[str] = None
    complexity: Optional[float] = None
    retrieval_stats: dict = Field(default_factory=dict)
    rerank_stats: dict = Field(default_factory=dict)
    guardrail_notes: list[str] = Field(default_factory=list)
    coverage: dict = Field(default_factory=dict)
    evidence: dict = Field(default_factory=dict)
    plan: list = Field(default_factory=list)
    claim_alignment: dict = Field(default_factory=dict)
    degrade: dict = Field(default_factory=dict)
    routing: dict = Field(default_factory=dict)


class RAGAnswerResponse(BaseModel):
    """Full response returned to the caller."""

    request: RAGAnswerRequest
    chart_context: ChartContext = Field(default_factory=ChartContext)
    payload: AnswerPayload
    debug: Optional[PipelineDebugInfo] = None
    documents: list[dict] = Field(default_factory=list)
    evidence_pack: dict = Field(default_factory=dict)
