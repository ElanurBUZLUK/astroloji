"""Adaptive degrade policy manager for the RAG pipeline."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from backend.app.config import settings
from app.evaluation.observability import observability


@dataclass
class DegradeDecision:
    """Represents the outcome of a degrade-policy evaluation."""

    active: bool
    reasons: List[str] = field(default_factory=list)
    rag_overrides: Dict[str, Any] = field(default_factory=dict)
    llm_overrides: Dict[str, Any] = field(default_factory=dict)
    flags: Dict[str, Any] = field(default_factory=dict)
    timeout_factor: float = 1.0
    cost_actions: Dict[str, Any] = field(default_factory=dict)


class DegradePolicyManager:
    """Computes degrade actions using live observability metrics."""

    def __init__(
        self,
        *,
        metrics=None,
        enabled: Optional[bool] = None,
        latency_threshold_ms: Optional[int] = None,
        min_latency_samples: Optional[int] = None,
        rag_low_top_k: Optional[int] = None,
    ) -> None:
        """Parameterize the degrade guardrails and wire in the metrics backend."""
        self._metrics = metrics or observability.metrics
        self._enabled = settings.RAG_DEGRADE_ENABLED if enabled is None else enabled
        self._latency_threshold_ms = (
            settings.RAG_DEGRADE_LATENCY_THRESHOLD_MS
            if latency_threshold_ms is None
            else latency_threshold_ms
        )
        self._min_latency_samples = (
            settings.RAG_DEGRADE_MIN_SAMPLES
            if min_latency_samples is None
            else min_latency_samples
        )
        self._rag_low_top_k = (
            settings.RAG_DEGRADE_TOP_K if rag_low_top_k is None else rag_low_top_k
        )
        self._cost_threshold = getattr(settings, "COST_GUARDRAIL_MAX_USD", None)
        self._cost_ce_reduce_to = getattr(settings, "COST_GUARDRAIL_CE_REDUCE_TO", None)
        self._cost_small_ratio_delta = getattr(settings, "COST_GUARDRAIL_SMALL_RATIO_DELTA", 0.0)
        self._cost_ttl_factor = getattr(settings, "COST_GUARDRAIL_TTL_FACTOR", 1.0)

    def evaluate(self) -> DegradeDecision:
        """Derive degrade decision from metric snapshots."""
        if not self._enabled:
            return DegradeDecision(active=False)

        reasons: List[str] = []
        flags: Dict[str, Any] = {}
        rag_overrides: Dict[str, Any] = {}
        llm_overrides: Dict[str, Any] = {}
        cost_actions: Dict[str, Any] = {}
        timeout_factor = 1.0

        latency_values = self._metrics.get_metric_values("rag_latency", 5)
        if len(latency_values) >= self._min_latency_samples:
            p95_latency = _percentile(latency_values, 95)
            flags["latency_p95_ms"] = round(p95_latency, 2)
            if p95_latency >= self._latency_threshold_ms:
                reasons.append(
                    f"rag_latency_p95>{self._latency_threshold_ms}ms"
                )
                rag_overrides.update(
                    {
                        "top_k": max(2, self._rag_low_top_k),
                        "expand_query": False,
                        "rerank_results": False,
                        "include_citations": True,
                        "retrieval_method": "dense",
                    }
                )
                llm_overrides["skip_revision"] = True
                flags["skip_multi_hop"] = True
                timeout_factor = 1.1
        else:
            flags["latency_samples"] = len(latency_values)

        if self._cost_threshold is not None:
            cost_values = self._metrics.get_metric_values("llm_cost_per_answer_usd", 15)
            if cost_values:
                latest_cost = cost_values[-1]
                flags["cost_latest_usd"] = round(latest_cost, 4)
                if latest_cost > self._cost_threshold:
                    reasons.append(f"cost_per_answer>{self._cost_threshold}")
                    if self._cost_ce_reduce_to:
                        rag_overrides["rerank_top_k"] = self._cost_ce_reduce_to
                        cost_actions["rerank_top_k"] = self._cost_ce_reduce_to
                    if self._cost_small_ratio_delta:
                        flags["prefer_small_delta"] = self._cost_small_ratio_delta
                        cost_actions["prefer_small_delta"] = self._cost_small_ratio_delta
                    if self._cost_ttl_factor and self._cost_ttl_factor > 1.0:
                        flags["cache_ttl_factor"] = self._cost_ttl_factor
                        cost_actions["cache_ttl_factor"] = self._cost_ttl_factor

        active = bool(reasons)
        return DegradeDecision(
            active=active,
            reasons=reasons,
            rag_overrides=rag_overrides,
            llm_overrides=llm_overrides,
            flags=flags,
            timeout_factor=timeout_factor,
            cost_actions=cost_actions,
        )


def _percentile(values: Sequence[float], percentile: int) -> float:
    """Compute percentile using nearest-rank method."""
    if not values:
        return 0.0
    if percentile <= 0:
        return float(min(values))
    if percentile >= 100:
        return float(max(values))
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile / 100 * len(ordered)))
    index = min(rank - 1, len(ordered) - 1)
    return float(ordered[index])
