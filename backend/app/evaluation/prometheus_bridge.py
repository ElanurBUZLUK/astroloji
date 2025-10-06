"""Prometheus metrics bridge for FastAPI and RAG pipeline instrumentation."""
from __future__ import annotations

from typing import Iterable, Sequence

from prometheus_client import Counter, Gauge, Histogram


API_REQUEST_COUNTER = Counter(
    "astro_api_requests_total",
    "Total number of API requests",
    labelnames=("method", "endpoint", "status"),
)

API_REQUEST_LATENCY = Histogram(
    "astro_api_request_latency_seconds",
    "API request latency in seconds",
    labelnames=("method", "endpoint"),
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0),
)

API_KEY_SUCCESS_COUNTER = Counter(
    "astro_api_key_valid_total",
    "Successful API key validations",
    labelnames=("endpoint",),
)

API_KEY_DENIED_COUNTER = Counter(
    "astro_api_key_denied_total",
    "Denied API key attempts",
    labelnames=("endpoint",),
)

API_RATE_LIMIT_COUNTER = Counter(
    "astro_api_rate_limit_exceeded_total",
    "Rate limit rejections",
    labelnames=("endpoint",),
)

RAG_PIPELINE_LATENCY = Histogram(
    "astro_rag_pipeline_latency_seconds",
    "End-to-end RAG pipeline latency",
    labelnames=("mode",),
    buckets=(0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0),
)

RAG_DEGRADE_GAUGE = Gauge(
    "astro_rag_degrade_active",
    "Indicates whether degrade safeguards are active",
)

RAG_QUALITY_ISSUE_COUNTER = Counter(
    "astro_rag_quality_issue_total",
    "Quality filter issues detected",
    labelnames=("issue",),
)

RAG_QUALITY_FALLBACK_COUNTER = Counter(
    "astro_rag_quality_fallback_total",
    "Fallback template activations",
    labelnames=("reason",),
)


def record_api_request(method: str, endpoint: str, status: int, latency_seconds: float) -> None:
    API_REQUEST_COUNTER.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    API_REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency_seconds)


def record_api_key_success(endpoint: str) -> None:
    API_KEY_SUCCESS_COUNTER.labels(endpoint=endpoint).inc()


def record_api_key_denied(endpoint: str) -> None:
    API_KEY_DENIED_COUNTER.labels(endpoint=endpoint).inc()


def record_rate_limit(endpoint: str) -> None:
    API_RATE_LIMIT_COUNTER.labels(endpoint=endpoint).inc()


def record_rag_latency(mode: str, latency_seconds: float) -> None:
    RAG_PIPELINE_LATENCY.labels(mode=mode or "unknown").observe(latency_seconds)


def set_degrade_active(active: bool) -> None:
    RAG_DEGRADE_GAUGE.set(1.0 if active else 0.0)


def record_quality_issues(issues: Sequence[str]) -> None:
    for issue in issues:
        RAG_QUALITY_ISSUE_COUNTER.labels(issue=issue).inc()


def record_quality_fallback(issues: Iterable[str]) -> None:
    for issue in issues:
        RAG_QUALITY_FALLBACK_COUNTER.labels(reason=issue).inc()

