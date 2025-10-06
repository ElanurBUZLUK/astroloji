from prometheus_client import Counter, Histogram

PREDICTION_COUNT = Counter(
    "prediction_count",
    "Count of horoscope predictions made",
    ["burc", "gun", "model", "fallback"],
)

MODEL_CONFIDENCE = Histogram(
    "model_confidence",
    "Confidence levels of the models used for predictions",
    ["model"],
)