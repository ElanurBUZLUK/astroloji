from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

from prometheus_client import Counter, Histogram

PREDICTION_COUNT = Counter(
    "horoscope_predictions_total",
    "Number of horoscope predictions generated",
    labelnames=("burc", "gun", "model", "fallback"),
)

PREDICTION_LATENCY = Histogram(
    "prediction_latency_seconds",
    "Latency histogram for horoscope predictions",
    labelnames=("model",),
    buckets=(0.25, 0.5, 1, 1.5, 2, 3, 5),
)

MODEL_CONFIDENCE = Histogram(
    "model_confidence",
    "Distribution of confidence scores",
    labelnames=("model",),
    buckets=(0.1, 0.25, 0.4, 0.55, 0.7, 0.85, 1.0),
)

EPHEMERIS_CACHE_HIT = Counter(
    "ephemeris_cache_hit_total",
    "Number of ephemeris cache hits",
)

EPHEMERIS_CACHE_MISS = Counter(
    "ephemeris_cache_miss_total",
    "Number of ephemeris cache misses",
)


@contextmanager
def track_prediction(model_name: str) -> Iterator[None]:
    start = time.perf_counter()
    with PREDICTION_LATENCY.labels(model=model_name).time():
        yield
    elapsed = time.perf_counter() - start
    # Histogram already records elapsed; the variable is retained for potential future use.
    _ = elapsed
