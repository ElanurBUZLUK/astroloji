from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple
from uuid import uuid4

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.middleware.cors import CORSMiddleware

from astroloji_ai import __version__
from astroloji_ai.config.settings import Settings, get_settings
from astroloji_ai.core.astrology import (
    calculate_aspects,
    dominant_energies,
    house_label,
    zodiac_sign,
)
from astroloji_ai.core.ephemeris import EphemerisService
from astroloji_ai.monitoring.metrics import MODEL_CONFIDENCE, PREDICTION_COUNT, track_prediction
from astroloji_ai.rag.client import RAGClient
from astroloji_ai.schemas.horoscope import HoroscopeRequest, HoroscopeResponse
from astroloji_ai.utils.logging import bind_request, configure_logging


def get_logger() -> structlog.stdlib.BoundLogger:
    return structlog.get_logger("astroloji_ai")


def create_app(settings: Settings) -> FastAPI:
    configure_logging(settings.log_level)
    logger = get_logger()
    app = FastAPI(
        title="Astroloji AI",
        version=__version__,
        default_response_class=JSONResponse,
    )

    app.state.settings = settings
    app.state.logger = logger
    app.state.ephemeris_service = EphemerisService(settings.ephemeris)
    app.state.rag_client = None

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event() -> None:
        try:
            app.state.rag_client = RAGClient(settings)
            logger.info("rag_client_initialized", persist_dir=settings.rag.persist_dir)
        except Exception as exc:  # noqa: BLE001
            logger.warning("rag_client_init_failed", error=str(exc))
            app.state.rag_client = None

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        return {"status": "ok", "version": __version__}

    @app.get("/metrics")
    async def metrics() -> PlainTextResponse:
        data = generate_latest()
        return PlainTextResponse(data.decode("utf-8"), media_type=CONTENT_TYPE_LATEST)

    @app.post("/horoscope", response_model=HoroscopeResponse)
    async def horoscope_endpoint(
        request: Request,
        payload: HoroscopeRequest,
        settings_dep: Settings = Depends(get_settings),
    ) -> HoroscopeResponse:
        # settings_dep ensures pydantic env reload if necessary
        del settings_dep
        app_settings: Settings = app.state.settings
        logger: structlog.stdlib.BoundLogger = app.state.logger
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        log = bind_request(
            logger,
            request_id=request_id,
            user_id=payload.user_id,
            burc=payload.burc,
            gun=payload.gun,
        )
        model_name = select_model(app_settings, payload)

        with track_prediction(model_name):
            try:
                timestamp = resolve_timeframe(payload.gun, payload.birth.tz)
            except ValueError as exc:
                log.warning("invalid_timeframe", error=str(exc))
                raise HTTPException(status_code=400, detail=str(exc)) from exc

            positions, ephemeris_fallback = app.state.ephemeris_service.get_positions(
                lat=payload.birth.lat,
                lon=payload.birth.lon,
                timestamp=timestamp,
            )

            rag_result = await query_rag(app, payload, positions)
            raw_text = rag_result.get("text", "").strip()
            sources = rag_result.get("sources", [])

            if not raw_text:
                ephemeris_fallback = True
                raw_text = fallback_commentary(payload, positions)

            if not quality_gate(raw_text, app_settings):
                ephemeris_fallback = True
                raw_text = fallback_commentary(payload, positions)

            dominant = dominant_energies(positions)
            aspects = calculate_aspects(positions, app_settings.ephemeris)

            natal_block = build_natal_block(positions)
            transit_block = build_transit_block(positions, aspects)
            pratik_tavsiyeler = generate_advice(payload, dominant)

            confidence = 0.72
            if ephemeris_fallback:
                confidence = 0.45

            response_payload = HoroscopeResponse(
                burc=payload.burc,
                gun=payload.gun,
                yorum=raw_text,
                confidence=round(confidence, 2),
                natal=natal_block,
                transit=transit_block,
                dominant_enerjiler=dominant,
                pratik_tavsiyeler=pratik_tavsiyeler,
                kaynaklar=sources,
                selected_model=model_name,
                is_fallback=ephemeris_fallback,
            )

            PREDICTION_COUNT.labels(
                burc=payload.burc,
                gun=payload.gun,
                model=model_name,
                fallback=str(ephemeris_fallback),
            ).inc()
            MODEL_CONFIDENCE.labels(model=model_name).observe(response_payload.confidence)

            log.info(
                "horoscope_generated",
                confidence=response_payload.confidence,
                fallback=response_payload.is_fallback,
                dominant=dominant,
            )

            return response_payload

    return app


def select_model(settings: Settings, payload: HoroscopeRequest) -> str:
    timeframe = payload.gun
    goals = payload.goals or []
    complex_intent = timeframe == "bu ay" or len(goals) >= 2
    return settings.llm.complex_model if complex_intent else settings.llm.routine_model


def resolve_timeframe(gun: str, tz_name: str) -> datetime:
    now = datetime.now(timezone.utc)
    if gun == "bugün":
        return now
    if gun == "yarın":
        return now + timedelta(days=1)
    if gun == "bu hafta":
        return now + timedelta(days=3)
    if gun == "bu ay":
        return now + timedelta(days=10)
    # ISO tarih bekleniyor
    try:
        date = datetime.fromisoformat(gun)
    except ValueError as exc:
        raise ValueError("Geçersiz tarih formatı. YYYY-MM-DD bekleniyor.") from exc
    return date.replace(tzinfo=timezone.utc)


async def query_rag(app: FastAPI, payload: HoroscopeRequest, positions: Dict[str, Any]) -> Dict[str, Any]:
    rag_client: RAGClient | None = app.state.rag_client
    if rag_client is None:
        return {"text": "", "sources": []}
    question = (
        f"{payload.burc} burcu için {payload.gun} tarihine yönelik astrolojik yorum. "
        f"Hedefler: {', '.join(payload.goals or [])}"
    )
    try:
        return await asyncio.to_thread(rag_client.query, question, positions)
    except Exception:  # noqa: BLE001
        return {"text": "", "sources": []}


def fallback_commentary(payload: HoroscopeRequest, positions: Dict[str, Any]) -> str:
    burc = payload.burc.capitalize()
    asc_sign = zodiac_sign(positions.get("ASC", {}).get("lon_deg", 0))
    sun_sign = zodiac_sign(positions.get("Güneş", {}).get("lon_deg", 0))
    return (
        f"{burc} burcu için temel denge ve iç gözlem önem kazanıyor. "
        f"Güneş etkisi {sun_sign} vurgusunu arttırırken yükselen çizgin {asc_sign} üzerinden çevresel "
        "eşiklerde daha bilinçli ilerlemen gerektiğini gösteriyor. "
        "Duygusal dalgalanmalarına dikkat ederek planlarını küçük ama sürdürülebilir adımlarla ilerletmen faydalı olacak. "
        "Bugün yapacağın kısa nefes egzersizleri ve gerçekçi hedef listeleri sana alan açabilir."
    )


def build_natal_block(positions: Dict[str, Any]) -> Dict[str, Any]:
    asc_lon = positions.get("ASC", {}).get("lon_deg", 0)
    mc_lon = positions.get("MC", {}).get("lon_deg", 0)
    asc_house = house_label(positions.get("ASC", {}).get("house", 1))
    mc_house = house_label(positions.get("MC", {}).get("house", 10))
    planets = {
        planet: values
        for planet, values in positions.items()
        if planet not in {"ASC", "MC"}
    }
    return {
        "asc": f"{round(asc_lon, 2)}° / {asc_house}",
        "mc": f"{round(mc_lon, 2)}° / {mc_house}",
        "planets": planets,
    }


def build_transit_block(positions: Dict[str, Any], aspects: list[Dict[str, Any]]) -> Dict[str, Any]:
    planets = {
        planet: values
        for planet, values in positions.items()
        if planet not in {"ASC", "MC"}
    }
    return {"planets": planets, "aspects": aspects}


def quality_gate(text: str, settings: Settings) -> bool:
    stripped = text.strip()
    if len(stripped) < settings.quality.min_chars:
        return False
    sentence_count = stripped.count(".")
    if sentence_count < settings.quality.min_sentences:
        return False
    keywords = settings.quality.required_keywords
    if not any(keyword in stripped.lower() for keyword in keywords):
        return False
    return True


def generate_advice(payload: HoroscopeRequest, dominant: list[str]) -> list[str]:
    focus = payload.goals or []
    advice = [
        "Günün ilk saatlerinde kısa bir nefes veya meditasyon pratiği ile zihnini dengele.",
        "Planlarını küçük adımlara böl ve ilerlemeni gün sonunda gözden geçir.",
    ]
    if "kariyer" in focus:
        advice.append("Profesyonel hedeflerine uygun bir mentör veya iş arkadaşı ile fikir paylaş.")
    if "aşk" in focus:
        advice.append("Duygularını yumuşak bir tonda paylaş ve karşındakini aktif dinle.")
    if not focus:
        advice.append("Gün içinde beden sinyallerine dikkat ederek dinlenme araları ekle.")
    if dominant:
        advice.append(f"Dominant enerjiye uyum için {dominant[0].lower()} temalarıyla çalış.")
    return advice[:4]


def run() -> None:
    import uvicorn

    settings = get_settings()
    app = create_app(settings)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=settings.log_level.lower())


app = create_app(get_settings())
