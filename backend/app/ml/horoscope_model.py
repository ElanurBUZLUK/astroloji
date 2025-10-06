"""Advanced horoscope model loading, inference, and deployment."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
from loguru import logger
from prometheus_client import Counter, Gauge, Histogram

try:  # pragma: no cover - optional dependency for deployment workflows
    import mlflow
    import mlflow.sklearn
except ImportError:  # pragma: no cover - mlflow optional at runtime
    mlflow = None  # type: ignore

from backend.app.config import settings

PREDICTION_COUNT = Counter("predictions_total", "Total predictions", ["burc", "kategori"])
PREDICTION_LATENCY = Histogram("prediction_latency_seconds", "Prediction latency")
MODEL_CONFIDENCE = Gauge("model_confidence", "Model confidence score")


class AdvancedAstrolojiModel:
    """Wrapper for trained horoscope classifiers and feature preprocessors."""

    def __init__(self, model_path: str | Path) -> None:
        self.model_path = Path(model_path)
        self.model_loaded = False
        self.model: Any = None
        self.vectorizer: Any = None
        self.label_encoders: Dict[str, Any] = {}
        self.scaler: Any = None
        self.metadata: Dict[str, Any] = {}
        self.performance_history: List[Dict[str, Any]] = []
        self.load_model()

    def load_model(self) -> None:
        """Load persisted artefacts into memory."""
        try:
            self.model = joblib.load(self.model_path / "model.joblib")
            self.vectorizer = joblib.load(self.model_path / "vectorizer.joblib")
            self.label_encoders = joblib.load(self.model_path / "label_encoders.joblib")
            self.scaler = joblib.load(self.model_path / "scaler.joblib")
            with (self.model_path / "metadata.json").open("r", encoding="utf-8") as handle:
                self.metadata = json.load(handle)
            self.model_loaded = True
            logger.info(
                "Model yüklendi",
                model=str(self.metadata.get("model_name")),
                version=self.metadata.get("version"),
            )
        except FileNotFoundError as exc:
            logger.error("Model dosyası bulunamadı", error=str(exc))
            self.model_loaded = False
        except Exception as exc:  # pragma: no cover - IO/compat issues
            logger.exception("Model yükleme hatası", error=str(exc))
            self.model_loaded = False

    def preprocess_input(self, burc: str, gun: str, tarih: Optional[str] = None) -> np.ndarray:
        """Transform incoming request into model feature space."""
        if tarih is None:
            tarih = datetime.utcnow().date().isoformat()

        date_obj = datetime.strptime(tarih, "%Y-%m-%d")
        ay = date_obj.month
        haftanin_gunu = date_obj.weekday()
        yilin_gunu = date_obj.timetuple().tm_yday

        gun_tipi = self.get_day_type(date_obj)
        mevsim = self.get_season(date_obj)
        ay_evresi = self.get_moon_phase(date_obj)

        burc_encoded = self._transform_label("burc", burc)
        gun_tipi_encoded = self._transform_label("gun_tipi", gun_tipi)
        mevsim_encoded = self._transform_label("mevsim", mevsim)
        ay_evresi_encoded = self._transform_label("ay_evresi", ay_evresi)

        numerical_features = np.array(
            [
                100,  # metin_uzunlugu placeholder
                20,  # kelime_sayisi placeholder
                0,  # duygu_skoru neutral baseline
                ay,
                haftanin_gunu,
                yilin_gunu,
                burc_encoded,
                gun_tipi_encoded,
                mevsim_encoded,
                ay_evresi_encoded,
            ]
        ).reshape(1, -1)

        scaled = self.scaler.transform(numerical_features)
        empty_text_vector = self.vectorizer.transform([""])
        combined = np.hstack([scaled, empty_text_vector.toarray()])
        return combined

    def predict_categories(self, burc: str, gun: str, tarih: Optional[str] = None) -> Dict[str, Any]:
        """Predict topical categories and aggregate confidence."""
        if not self.model_loaded:
            return self.get_fallback_categories()

        try:
            features = self.preprocess_input(burc, gun, tarih)
            with PREDICTION_LATENCY.time():
                raw_outputs = self.model.predict_proba(features)
            predicted: List[Dict[str, float]] = []
            category_labels = self.metadata.get("categories", [])
            for idx, probabilities in enumerate(raw_outputs):
                label = category_labels[idx] if idx < len(category_labels) else f"category_{idx}"
                if probabilities.shape[1] == 1:
                    pos_prob = float(probabilities[0][0])
                else:
                    pos_prob = float(probabilities[0][1])
                if pos_prob > 0.3:
                    predicted.append(
                        {
                            "kategori": label,
                            "olasilik": pos_prob,
                        }
                    )
            predicted.sort(key=lambda item: item["olasilik"], reverse=True)
            overall_confidence = float(np.mean([p["olasilik"] for p in predicted])) if predicted else 0.0
            MODEL_CONFIDENCE.set(overall_confidence)
            for item in predicted:
                PREDICTION_COUNT.labels(burc=burc.lower(), kategori=item["kategori"]).inc()
            return {
                "kategoriler": predicted,
                "toplam_guven": overall_confidence,
                "model_version": self.metadata.get("version", "unknown"),
            }
        except Exception as exc:  # pragma: no cover - inference safeguards
            logger.exception("Tahmin hatası", error=str(exc))
            return self.get_fallback_categories()

    def generate_horoscope(self, burc: str, gun: str, categories: List[Dict[str, Any]]) -> str:
        """Generate horoscope summary using template heuristics."""
        templates: Dict[str, List[str]] = {
            "ask": [
                "Aşk hayatınızda yeni gelişmeler kapıda. Kalbinizin sesini dinleyin.",
                "Romantik enerjiler yükseliyor. Kendinizi sevgiye açın.",
            ],
            "kariyer": [
                "Kariyerinizde önemli bir dönüm noktasındasınız. Fırsatları değerlendirin.",
                "İş hayatınızda yaratıcı çözümlere ihtiyaç var.",
            ],
            "saglik": [
                "Sağlığınıza dikkat etme zamanı. Dinlenmeyi ihmal etmeyin.",
                "Enerjinizi doğru kullanmak size güç katacak.",
            ],
            "finans": [
                "Maddi konularda şanslı bir dönemdesiniz. Akıllı yatırımlar yapın.",
                "Finansal planlamanızı gözden geçirme zamanı.",
            ],
        }

        main_category = categories[0]["kategori"] if categories else "genel"
        options = templates.get(main_category, [
            "Kozmik enerjiler sizi destekliyor. Sezgilerinize güvenin.",
            "Yeni başlangıçlar için uygun bir zaman.",
            "İlişkilerinizde denge kurmaya çalışın.",
        ])
        choice_idx = int(datetime.utcnow().timestamp()) % len(options)
        summary = options[choice_idx]
        return f"{burc.title()} burcu için {gun}: {summary}"

    def get_day_type(self, date_obj: datetime) -> str:
        return "hafta_sonu" if date_obj.weekday() >= 5 else "hafta_ici"

    def get_season(self, date_obj: datetime) -> str:
        month = date_obj.month
        if month in (12, 1, 2):
            return "kis"
        if month in (3, 4, 5):
            return "ilkbahar"
        if month in (6, 7, 8):
            return "yaz"
        return "sonbahar"

    def get_moon_phase(self, date_obj: datetime) -> str:
        day = date_obj.day
        if day <= 7:
            return "yeni_ay"
        if day <= 14:
            return "ilk_dordun"
        if day <= 21:
            return "dolunay"
        return "son_dordun"

    def get_fallback_categories(self) -> Dict[str, Any]:
        return {
            "kategoriler": [{"kategori": "genel", "olasilik": 0.5}],
            "toplam_guven": 0.5,
            "model_version": "fallback",
            "is_fallback": True,
        }

    def _transform_label(self, encoder_key: str, value: str) -> int:
        try:
            encoder = self.label_encoders[encoder_key]
            return int(encoder.transform([value])[0])
        except Exception:
            return 0


class ModelDeployment:
    """Simple deployment helper with MLflow logging and version control."""

    def __init__(self) -> None:
        self.current_model: AdvancedAstrolojiModel | None = None
        self.model_versions: Dict[str, AdvancedAstrolojiModel] = {}
        if mlflow and settings.MLFLOW_TRACKING_URI:
            mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)

    def deploy_model(self, model_path: str | Path, version: str) -> bool:
        try:
            candidate = AdvancedAstrolojiModel(model_path)
            if not candidate.model_loaded:
                return False
            if not self.validate_model(candidate):
                logger.warning("Model doğrulamadan geçemedi", version=version)
                return False

            self.current_model = candidate
            self.model_versions[version] = candidate

            if mlflow:
                metrics = candidate.metadata.get("metrics", {})
                numeric_metrics = {
                    key: float(value)
                    for key, value in metrics.items()
                    if isinstance(value, (int, float))
                }
                with mlflow.start_run(run_name=f"deploy_v{version}"):
                    for key, value in candidate.metadata.items():
                        if key == "metrics":
                            continue
                        if isinstance(value, (str, int, float)):
                            mlflow.log_param(key, value)
                        else:
                            mlflow.log_param(key, json.dumps(value))
                    if numeric_metrics:
                        mlflow.log_metrics(numeric_metrics)
                    mlflow.sklearn.log_model(candidate.model, "model")
            logger.info("Model deploy edildi", version=version)
            return True
        except Exception as exc:  # pragma: no cover - deployment safeguards
            logger.exception("Deploy hatası", error=str(exc))
            return False

    def validate_model(self, model: AdvancedAstrolojiModel) -> bool:
        metrics = model.metadata.get("metrics", {})
        accuracy = metrics.get("accuracy", 0)
        if accuracy < 0.6:
            return False
        feature_columns = model.metadata.get("feature_columns", [])
        if len(feature_columns) < 5:
            return False
        categories = model.metadata.get("categories", [])
        return bool(categories)

    def rollback_model(self, version: str) -> bool:
        if version not in self.model_versions:
            return False
        self.current_model = self.model_versions[version]
        logger.info("Model rollback uygulandı", version=version)
        return True

    def canary_deployment(self, model_path: str | Path, version: str, traffic_percentage: float = 0.1) -> None:
        logger.info(
            "Canary deployment henüz uygulanmadı",
            version=version,
            traffic_percentage=traffic_percentage,
            model_path=str(model_path),
        )
