"""Service layer for horoscope predictions using trained ML models."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from backend.app.config import settings
from backend.app.ml import AdvancedAstrolojiModel

VALID_BURCLAR = [
    "koç",
    "boğa",
    "ikizler",
    "yengeç",
    "aslan",
    "başak",
    "terazi",
    "akrep",
    "yay",
    "oğlak",
    "kova",
    "balık",
]

VALID_GUNLER = ["bugün", "yarın", "bu hafta", "bu ay"]


class HoroscopeService:
    """Prediction orchestration for horoscope API."""

    _model_instance: AdvancedAstrolojiModel | None = None

    @classmethod
    def sanitize_input(cls, value: Optional[str]) -> str:
        if value is None:
            return ""
        clean_value = re.sub(r"<.*?>", "", value)
        return clean_value.strip()

    @classmethod
    def validate_burc(cls, burc: str) -> bool:
        return burc.lower() in VALID_BURCLAR

    @classmethod
    def validate_gun(cls, gun: str) -> bool:
        return gun.lower() in VALID_GUNLER

    @classmethod
    def _resolve_model_path(cls) -> Path | None:
        if settings.HOROSCOPE_MODEL_DIR:
            model_path = Path(settings.HOROSCOPE_MODEL_DIR)
            if model_path.exists():
                return model_path
        fallback_path = Path("models") / "random_forest_v1.0.0"
        if fallback_path.exists():
            return fallback_path
        return None

    @classmethod
    def get_model(cls) -> AdvancedAstrolojiModel:
        if cls._model_instance is None:
            resolved = cls._resolve_model_path()
            if resolved is None:
                logger.warning("Horoscope modeli bulunamadı, fallback modunda")
                cls._model_instance = AdvancedAstrolojiModel(Path("."))
                cls._model_instance.model_loaded = False
            else:
                cls._model_instance = AdvancedAstrolojiModel(resolved)
        return cls._model_instance

    @classmethod
    def predict(cls, burc: str, gun: str) -> Dict[str, Any]:
        model = cls.get_model()
        result = model.predict_categories(burc, gun)
        horoscope_text = model.generate_horoscope(burc, gun, result.get("kategoriler", []))
        payload = {
            "tahmin": horoscope_text,
            "burc": burc,
            "gun": gun,
            "confidence": result.get("toplam_guven", 0.0),
            "model_version": result.get("model_version"),
            "timestamp": datetime.utcnow().isoformat(),
            "kategoriler": result.get("kategoriler", []),
        }
        return payload

    @classmethod
    def get_model_metrics(cls) -> Dict[str, Any]:
        model = cls.get_model()
        metadata = model.metadata if model.metadata else {}
        metrics = metadata.get("metrics", {})
        return {
            "model_loaded": model.model_loaded,
            "model_version": metadata.get("version"),
            "metrics": metrics,
            "categories": metadata.get("categories", []),
        }
