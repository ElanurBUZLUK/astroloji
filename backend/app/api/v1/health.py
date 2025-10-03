"""Simple health endpoints for v1 namespace."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}
