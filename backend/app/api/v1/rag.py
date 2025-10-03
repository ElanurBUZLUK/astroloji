"""API endpoints for the new RAG answer pipeline."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.pipelines.rag_pipeline import RAGAnswerPipeline
from app.schemas import RAGAnswerRequest, RAGAnswerResponse


router = APIRouter(prefix="/v1/rag", tags=["rag"])


def get_pipeline() -> RAGAnswerPipeline:
    """Resolve a pipeline instance; dependency injected for testing."""
    return RAGAnswerPipeline()


@router.post("/answer", response_model=RAGAnswerResponse)
async def create_rag_answer(
    request: RAGAnswerRequest,
    pipeline: RAGAnswerPipeline = Depends(get_pipeline),
) -> RAGAnswerResponse:
    """Run the end-to-end pipeline and return a structured answer."""
    return await pipeline.run(request)
