"""Versioned API routers."""
from fastapi import APIRouter

from . import health, rag, stream

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(rag.router)
api_router.include_router(stream.router)

__all__ = ["api_router"]
