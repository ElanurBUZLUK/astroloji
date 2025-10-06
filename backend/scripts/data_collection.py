"""Horoscope data collection utilities."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup  # noqa: F401 - kept for future HTML parsing extensions
import pandas as pd
from loguru import logger


@dataclass
class DataSource:
    """Representation of an external horoscope provider."""

    name: str
    url: str
    params: Dict[str, Any]


class AstrolojiDataCollector:
    """Collect and persist historical horoscope data."""

    def __init__(self) -> None:
        self.horoscope_data: List[Dict[str, Any]] = []

    def collect_historical_data(self) -> None:
        """Gather horoscope records from configured sources."""
        sources = [
            DataSource(
                name="AstrolojiSitesi",
                url="https://example-astrology-api.com/horoscopes",
                params={"days": 365},
            )
        ]

        for source in sources:
            try:
                raw_payload = self.fetch_from_source(source)
                self.process_data(raw_payload, source.name)
            except Exception as exc:  # pragma: no cover - external dependency
                logger.exception("Veri toplama hatası", source=source.name, error=str(exc))

    def fetch_from_source(self, source: DataSource) -> List[Dict[str, Any]]:
        """Fetch horoscope entries from API or HTML endpoint."""
        response = requests.get(source.url, params=source.params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("Beklenen liste yapısı alınamadı")
        return payload

    def process_data(self, raw_data: List[Dict[str, Any]], source_name: str) -> None:
        """Normalise provider payload into training schema."""
        for entry in raw_data:
            zodiac = (entry.get("zodiac_sign") or "").lower()
            prediction = entry.get("prediction") or ""
            date_value = entry.get("date") or datetime.utcnow().date().isoformat()

            processed_entry = {
                "burc": zodiac,
                "tarih": date_value,
                "gun_tipi": self.get_day_type(date_value),
                "mevsim": self.get_season(date_value),
                "ay_evresi": self.get_moon_phase(date_value),
                "tahmin_metni": prediction,
                "kategori": self.categorize_prediction(prediction),
                "duygu_skoru": self.sentiment_analysis(prediction),
                "kaynak": source_name,
                "toplama_tarihi": datetime.utcnow().isoformat(),
            }
            self.horoscope_data.append(processed_entry)

    def get_day_type(self, date_str: str) -> str:
        """Return weekend/weekday or special day label."""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        if date_obj.weekday() >= 5:
            return "hafta_sonu"
        special = self.get_special_day(date_obj)
        return special or "hafta_ici"

    def get_special_day(self, date_obj: datetime) -> Optional[str]:
        """Placeholder for custom special-day tagging."""
        special_days: Dict[str, str] = {}
        return special_days.get(date_obj.strftime("%m-%d"))

    def get_season(self, date_str: str) -> str:
        """Infer season from month."""
        month = datetime.strptime(date_str, "%Y-%m-%d").month
        if month in (12, 1, 2):
            return "kis"
        if month in (3, 4, 5):
            return "ilkbahar"
        if month in (6, 7, 8):
            return "yaz"
        return "sonbahar"

    def get_moon_phase(self, date_str: str) -> str:
        """Approximate moon phase from day of month."""
        day = datetime.strptime(date_str, "%Y-%m-%d").day
        if day <= 7:
            return "yeni_ay"
        if day <= 14:
            return "ilk_dordun"
        if day <= 21:
            return "dolunay"
        return "son_dordun"

    def categorize_prediction(self, prediction_text: str) -> List[str]:
        """Tag horoscope text with topical categories."""
        categories: Dict[str, List[str]] = {
            "ask": ["aşk", "sevgili", "flört", "romantik", "kalp"],
            "kariyer": ["iş", "kariyer", "terfi", "mülakat", "proje"],
            "saglik": ["sağlık", "hastalık", "enerji", "stres", "diyet"],
            "finans": ["para", "finans", "yatırım", "alışveriş", "borç"],
            "sosyal": ["arkadaş", "aile", "sosyal", "parti", "davet"],
        }
        text_lower = prediction_text.lower()
        matched: List[str] = [
            category for category, keywords in categories.items() if any(k in text_lower for k in keywords)
        ]
        return matched or ["genel"]

    def sentiment_analysis(self, text: str) -> int:
        """Basic sentiment heuristic using word lists."""
        positives = ["iyi", "güzel", "mutlu", "başarı", "şans", "sevgi", "kazanç"]
        negatives = ["kötü", "dikkat", "risk", "kaçın", "sorun", "tartışma"]
        lowered = text.lower()
        pos = sum(1 for word in positives if word in lowered)
        neg = sum(1 for word in negatives if word in lowered)
        if pos > neg:
            return 1
        if neg > pos:
            return -1
        return 0

    def save_data(self, filename: str = "horoscope_dataset.json") -> pd.DataFrame:
        """Persist collected dataset to disk."""
        if not self.horoscope_data:
            raise ValueError("Kaydedilecek veri bulunamadı")

        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(self.horoscope_data, handle, ensure_ascii=False, indent=2)

        dataframe = pd.DataFrame(self.horoscope_data)
        csv_path = output_path.with_suffix(".csv")
        dataframe.to_csv(csv_path, index=False)
        logger.info("Veri seti kaydedildi", json_path=str(output_path), csv_path=str(csv_path))
        return dataframe


def main() -> None:  # pragma: no cover - CLI helper
    collector = AstrolojiDataCollector()
    collector.collect_historical_data()
    collector.save_data()


if __name__ == "__main__":  # pragma: no cover - CLI helper
    main()
