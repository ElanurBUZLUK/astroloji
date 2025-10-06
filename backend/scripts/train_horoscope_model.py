"""Training utilities for horoscope classification model."""
from __future__ import annotations

import ast
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.utils.multiclass import type_of_target
import xgboost as xgb


class AstrolojiModelTrainer:
    """Train multi-label classifiers for horoscope category prediction."""

    def __init__(self) -> None:
        self.vectorizer: TfidfVectorizer | None = None
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.scaler = StandardScaler()
        self.models: Dict[str, MultiOutputClassifier] = {}
        self.metrics: Dict[str, Dict[str, float]] = {}
        self.feature_columns: List[str] = []
        self.categories: List[str] = []

    def load_and_preprocess_data(self, data_path: str | Path) -> pd.DataFrame:
        """Load, clean, and cache dataset."""
        data_file = Path(data_path)
        if not data_file.exists():
            raise FileNotFoundError(f"Veri seti bulunamadı: {data_file}")

        df = pd.read_csv(data_file)
        df = df.dropna(subset=["tahmin_metni", "burc", "kategori"])
        df = df[df["tahmin_metni"].str.len() > 10]
        df = df.reset_index(drop=True)
        self.df = df
        logger.info("Veri yüklendi", rows=len(df))
        return df

    def feature_engineering(self) -> np.ndarray:
        """Generate numerical and textual features."""
        if not hasattr(self, "df"):
            raise RuntimeError("Önce veriyi yükleyin")

        df = self.df
        df["metin_uzunlugu"] = df["tahmin_metni"].str.len()
        df["kelime_sayisi"] = df["tahmin_metni"].str.split().str.len()

        df["tarih"] = pd.to_datetime(df["tarih"])
        df["ay"] = df["tarih"].dt.month
        df["haftanin_gunu"] = df["tarih"].dt.dayofweek
        df["yilin_gunu"] = df["tarih"].dt.dayofyear

        categorical_features = ["burc", "gun_tipi", "mevsim", "ay_evresi"]
        for feature in categorical_features:
            encoder = LabelEncoder()
            df[f"{feature}_encoded"] = encoder.fit_transform(df[feature])
            self.label_encoders[feature] = encoder

        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=["bir", "ve", "ile", "için", "gibi"],
            ngram_range=(1, 2),
        )
        tfidf_matrix = self.vectorizer.fit_transform(df["tahmin_metni"])

        numerical_features = [
            "metin_uzunlugu",
            "kelime_sayisi",
            "duygu_skoru",
            "ay",
            "haftanin_gunu",
            "yilin_gunu",
        ]
        encoded_features = [f"{feat}_encoded" for feat in categorical_features]
        self.feature_columns = numerical_features + encoded_features

        numerical_array = df[numerical_features + encoded_features].to_numpy()
        scaled_numerical = self.scaler.fit_transform(numerical_array)
        combined = np.hstack([scaled_numerical, tfidf_matrix.toarray()])
        self.X = combined
        return combined

    def prepare_targets(self) -> np.ndarray:
        """Build multi-label target matrix."""
        if not hasattr(self, "df"):
            raise RuntimeError("Önce veriyi yükleyin")

        labels: List[List[str]] = []
        all_categories = set()
        for raw_value in self.df["kategori"]:
            if isinstance(raw_value, str):
                parsed = ast.literal_eval(raw_value)
            elif isinstance(raw_value, list):
                parsed = raw_value
            else:
                parsed = []
            labels.append(parsed)
            all_categories.update(parsed)

        self.categories = sorted(all_categories)
        if not self.categories:
            raise ValueError("Kategori bilgisi bulunamadı")

        y = np.zeros((len(labels), len(self.categories)), dtype=int)
        for row_idx, categories in enumerate(labels):
            for category in categories:
                try:
                    col_idx = self.categories.index(category)
                except ValueError:
                    continue
                y[row_idx, col_idx] = 1

        if type_of_target(y) != "multilabel-indicator":
            raise ValueError("Hedef değişken multi-label formata dönüştürülemedi")

        self.y = y
        return y

    def train_models(self) -> Dict[str, MultiOutputClassifier]:
        """Train baseline ensemble models."""
        if not hasattr(self, "X") or not hasattr(self, "y"):
            raise RuntimeError("Önce özellikleri ve hedefleri hazırlayın")

        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42
        )

        rf = MultiOutputClassifier(
            RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
        )
        logger.info("RandomForest modeli eğitiliyor")
        rf.fit(X_train, y_train)
        self.models["random_forest"] = rf

        xgb_classifier = MultiOutputClassifier(
            xgb.XGBClassifier(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=6,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=42,
                eval_metric="logloss",
            )
        )
        logger.info("XGBoost modeli eğitiliyor")
        xgb_classifier.fit(X_train, y_train)
        self.models["xgboost"] = xgb_classifier

        self.evaluate_models(X_test, y_test)
        return self.models

    def evaluate_models(self, X_test: np.ndarray, y_test: np.ndarray) -> None:
        """Compute evaluation metrics for trained models."""
        for model_name, model in self.models.items():
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average="weighted", zero_division=0)
            recall = recall_score(y_test, y_pred, average="weighted", zero_division=0)
            f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
            self.metrics[model_name] = {
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
            }
            logger.info(
                "Model değerlendirmesi",
                model=model_name,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1=f1,
            )

    def save_model(self, model_name: str, version: str = "1.0.0") -> Path:
        """Persist trained model artefacts to disk."""
        if model_name not in self.models:
            raise KeyError(f"Model bulunamadı: {model_name}")
        if model_name not in self.metrics:
            raise KeyError(f"Model metrikleri eksik: {model_name}")

        model_dir = Path("models") / f"{model_name}_v{version}"
        model_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.models[model_name], model_dir / "model.joblib")
        joblib.dump(self.vectorizer, model_dir / "vectorizer.joblib")
        joblib.dump(self.label_encoders, model_dir / "label_encoders.joblib")
        joblib.dump(self.scaler, model_dir / "scaler.joblib")

        metadata = {
            "model_name": model_name,
            "version": version,
            "training_date": datetime.utcnow().isoformat(),
            "feature_columns": self.feature_columns,
            "categories": self.categories,
            "metrics": self.metrics[model_name],
        }

        with (model_dir / "metadata.json").open("w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2)

        logger.info("Model kaydedildi", model=str(model_dir))
        return model_dir


def main() -> None:  # pragma: no cover - CLI helper
    trainer = AstrolojiModelTrainer()
    df = trainer.load_and_preprocess_data("horoscope_dataset.csv")
    logger.info("Yüklenen veri sayısı", rows=len(df))
    trainer.feature_engineering()
    trainer.prepare_targets()
    trainer.train_models()
    trainer.save_model("random_forest")


if __name__ == "__main__":  # pragma: no cover - CLI helper
    main()
