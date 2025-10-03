"""Server-Sent Events streaming endpoint."""
from __future__ import annotations

import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from app.schemas import RAGAnswerRequest
from app.pipelines.rag_pipeline import RAGAnswerPipeline

router = APIRouter(prefix="/v1/stream", tags=["stream"])


def get_pipeline() -> RAGAnswerPipeline:
    return RAGAnswerPipeline()


@router.post("/answer")
async def stream_answer(
    request: RAGAnswerRequest,
    pipeline: RAGAnswerPipeline = Depends(get_pipeline),
) -> StreamingResponse:
    async def event_generator() -> AsyncGenerator[bytes, None]:
        response = await pipeline.run(request)
        for section in response.payload.answer.sections:
            payload = {
                "type": "section",
                "title": section.title,
                "content": section.content,
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")
        final_payload = {
            "type": "summary",
            "summary": response.payload.answer.general_profile,
            "coverage": response.payload.limits.coverage_score,
        }
        yield f"data: {json.dumps(final_payload, ensure_ascii=False)}\n\n".encode("utf-8")

    return StreamingResponse(event_generator(), media_type="text/event-stream")
