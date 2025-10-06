"""Analyze telemetry to recommend LLM router thresholds."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from types import SimpleNamespace

try:
    from backend.app.config import settings as _settings
except Exception:  # pragma: no cover - fallback for missing/extra env vars
    _settings = SimpleNamespace(
        LLM_ROUTER_CONF_LOW=0.55,
        LLM_ROUTER_CONF_HIGH=0.75,
    )

settings = _settings

try:
    from app.evaluation.observability import MetricPoint, observability
except Exception:  # pragma: no cover - allows running without app imports
    MetricPoint = None  # type: ignore
    observability = None  # type: ignore


@dataclass
class ConfidenceRecord:
    confidence: float
    success: bool
    provider: Optional[str] = None
    model: Optional[str] = None


def percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    if pct <= 0:
        return min(values)
    if pct >= 100:
        return max(values)
    ordered = sorted(values)
    k = int(round((pct / 100) * (len(ordered) - 1)))
    return ordered[k]


def load_records_from_metrics() -> List[ConfidenceRecord]:
    if observability is None:
        return []
    metric_points: Iterable[MetricPoint] = observability.metrics.metrics.get(
        "llm_router_confidence_metric", []
    )
    records: List[ConfidenceRecord] = []
    for point in metric_points:
        tags = point.tags or {}
        success = tags.get("success") == "1"
        records.append(
            ConfidenceRecord(
                confidence=float(point.value),
                success=success,
                provider=tags.get("provider"),
                model=tags.get("model"),
            )
        )
    return records


def load_provider_stats_from_metrics() -> Dict[str, Dict[str, List[float]]]:
    data: Dict[str, Dict[str, List[float]]] = {}
    if observability is None:
        return {}
    for point in observability.metrics.metrics.get("llm_provider_latency", []):
        provider = (point.tags or {}).get("provider", "unknown")
        data.setdefault(provider, {}).setdefault("latency", []).append(float(point.value))
    for point in observability.metrics.metrics.get("llm_provider_health_score", []):
        provider = (point.tags or {}).get("provider", "unknown")
        data.setdefault(provider, {}).setdefault("health", []).append(float(point.value))
    return data


def load_records_from_file(path: Path) -> List[ConfidenceRecord]:
    records: List[ConfidenceRecord] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            records.append(
                ConfidenceRecord(
                    confidence=float(payload["confidence"]),
                    success=bool(payload.get("success")),
                    provider=payload.get("provider"),
                    model=payload.get("model"),
                )
            )
    return records


def analyze_confidence(records: List[ConfidenceRecord], target_precision: float) -> Dict[str, float]:
    if not records:
        return {
            "low_threshold": settings.LLM_ROUTER_CONF_LOW,
            "high_threshold": settings.LLM_ROUTER_CONF_HIGH,
            "support": 0,
            "precision": 0.0,
        }

    successes = [r for r in records if r.success]
    success_conf = [r.confidence for r in successes]
    low_threshold = settings.LLM_ROUTER_CONF_LOW
    if success_conf:
        q1 = percentile(success_conf, 25)
        low_threshold = max(0.05, round(q1 - 0.05, 3))

    best_threshold = settings.LLM_ROUTER_CONF_HIGH
    best_precision = 0.0
    support = 0
    for candidate in sorted({round(r.confidence, 3) for r in records}, reverse=True):
        cohort = [r for r in records if r.confidence >= candidate]
        if len(cohort) < 10:
            continue
        precision = sum(1 for r in cohort if r.success) / len(cohort)
        if precision >= target_precision and precision >= best_precision:
            best_precision = precision
            best_threshold = candidate
            support = len(cohort)

    return {
        "low_threshold": round(low_threshold, 3),
        "high_threshold": round(best_threshold, 3),
        "support": support,
        "precision": round(best_precision, 3),
    }


def analyze_health(provider_stats: Dict[str, Dict[str, List[float]]]) -> Dict[str, float]:
    provider_floor: Dict[str, float] = {}
    for provider, stats in provider_stats.items():
        scores = stats.get("health", [])
        if not scores:
            continue
        floor = percentile(scores, 10)
        provider_floor[provider] = round(floor, 3)
    return provider_floor


def format_config(low: float, high: float, health_floor: Dict[str, float]) -> str:
    lines = ["# Suggested configuration overrides", "LLM_ROUTER_CONF_LOW={:.3f}".format(low), "LLM_ROUTER_CONF_HIGH={:.3f}".format(high)]
    if health_floor:
        for provider, floor in health_floor.items():
            lines.append(f"# provider {provider} 10th percentile health ≈ {floor:.3f}")
            if floor > 0.0:
                lines.append(f"# consider treating health<={floor:.3f} as unhealthy")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tune LLM router thresholds from telemetry")
    parser.add_argument(
        "--input",
        type=Path,
        help="Optional path to NDJSON telemetry export (confidence, success, provider)",
    )
    parser.add_argument(
        "--target-precision",
        type=float,
        default=0.9,
        help="Desired precision for the high-confidence cohort (default: 0.9)",
    )
    args = parser.parse_args()

    if args.input:
        records = load_records_from_file(args.input)
        provider_stats: Dict[str, Dict[str, List[float]]] = {}
    elif observability is not None:
        records = load_records_from_metrics()
        provider_stats = load_provider_stats_from_metrics()
    else:
        print("Observability module not available; provide --input telemetry file instead.")
        return

    if not records:
        print("No router confidence data available. Collect telemetry before tuning.")
        return

    confidence_summary = analyze_confidence(records, args.target_precision)
    health_floor = analyze_health(provider_stats)

    print("Confidence analysis:")
    print(f"  Recommended low threshold: {confidence_summary['low_threshold']:.3f}")
    print(
        f"  Recommended high threshold: {confidence_summary['high_threshold']:.3f}"
        f" (precision≈{confidence_summary['precision']:.3f}, support={confidence_summary['support']})"
    )
    if health_floor:
        print("Provider health floors (10th percentile of health_score):")
        for provider, floor in health_floor.items():
            print(f"  {provider}: {floor:.3f}")

    print("\nSuggested config snippet:\n")
    print(
        format_config(
            confidence_summary["low_threshold"],
            confidence_summary["high_threshold"],
            health_floor,
        )
    )


if __name__ == "__main__":
    main()
