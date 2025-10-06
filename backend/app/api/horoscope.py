"""Horoscope prediction endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.app.auth.security import rate_limiter
from backend.app.config import settings
from backend.app.horoscope import HoroscopeService, VALID_BURCLAR, VALID_GUNLER

router = APIRouter(prefix="/api", tags=["horoscope"])


class HoroscopeRequest(BaseModel):
    burc: str = Field(..., description="Burç adı")
    gun: str = Field(..., description="Gün seçimi (bugün, yarın, bu hafta, bu ay)")
    tarih: Optional[str] = Field(None, description="Opsiyonel ISO tarih değeri")


class HoroscopeResponse(BaseModel):
    tahmin: str
    burc: str
    gun: str
    confidence: float
    model_version: Optional[str]
    timestamp: str
    kategoriler: List[Dict[str, Any]]


class HoroscopeHealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


@router.get("/health", response_model=HoroscopeHealthResponse)
async def horoscope_health() -> HoroscopeHealthResponse:
    """Health check for horoscope API."""
    return HoroscopeHealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
    )


@router.get("/model/metrics")
async def horoscope_model_metrics() -> Dict[str, Any]:
    """Expose current model metadata and evaluation metrics."""
    return HoroscopeService.get_model_metrics()


@router.post("/predict", response_model=HoroscopeResponse)
async def predict_horoscope(request: Request, payload: HoroscopeRequest) -> HoroscopeResponse:
    """Generate horoscope prediction with basic rate limiting and validation."""
    client_ip = request.client.host if request.client else "anonymous"
    limit = max(settings.HOROSCOPE_RATE_LIMIT_PER_MINUTE, 1)
    if not rate_limiter.is_allowed(client_ip, limit=limit, window=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit aşıldı, lütfen daha sonra tekrar deneyin.",
        )

    burc = HoroscopeService.sanitize_input(payload.burc)
    gun = HoroscopeService.sanitize_input(payload.gun)

    if not burc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Burç parametresi gereklidir")
    if not gun:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gün parametresi gereklidir")
    if not HoroscopeService.validate_burc(burc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Geçersiz burç", "valid_burclar": VALID_BURCLAR},
        )
    if not HoroscopeService.validate_gun(gun):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Geçersiz gün", "valid_gunler": VALID_GUNLER},
        )

    try:
        result = HoroscopeService.predict(burc, gun)
        return HoroscopeResponse(**result)
    except Exception as exc:  # pragma: no cover - runtime guard
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
