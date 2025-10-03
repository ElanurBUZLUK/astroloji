"""Tests for adaptive degrade policy manager."""
from app.evaluation.observability import MetricCollector
from app.pipelines.degrade import DegradePolicyManager
from app.config import settings


def test_degrade_inactive_without_samples():
    metrics = MetricCollector(max_points_per_metric=50)
    manager = DegradePolicyManager(
        metrics=metrics,
        min_latency_samples=5,
        latency_threshold_ms=200,
    )

    decision = manager.evaluate()

    assert decision.active is False
    assert decision.reasons == []
    assert decision.flags.get("latency_samples") == 0
    assert decision.rag_overrides == {}


def test_degrade_triggers_on_high_latency():
    metrics = MetricCollector(max_points_per_metric=100)
    for value in [180, 190, 210, 240, 260, 300]:
        metrics.record_histogram("rag_latency", value)

    manager = DegradePolicyManager(
        metrics=metrics,
        min_latency_samples=5,
        latency_threshold_ms=200,
        rag_low_top_k=4,
    )

    decision = manager.evaluate()

    assert decision.active is True
    assert any(reason.startswith("rag_latency_p95") for reason in decision.reasons)
    assert decision.rag_overrides.get("top_k") == 4
    assert decision.rag_overrides.get("rerank_results") is False
    assert decision.flags.get("skip_multi_hop") is True
    assert decision.llm_overrides.get("skip_revision") is True


def test_cost_guardrail_actions():
    metrics = MetricCollector(max_points_per_metric=50)
    for value in [0.005, 0.008, 0.012]:
        metrics.record_histogram("llm_cost_per_answer_usd", value)

    manager = DegradePolicyManager(
        metrics=metrics,
        min_latency_samples=5,
        latency_threshold_ms=9999,
        rag_low_top_k=6,
    )

    decision = manager.evaluate()

    assert decision.active is True
    assert any("cost_per_answer" in reason for reason in decision.reasons)
    assert decision.cost_actions.get("rerank_top_k") == settings.COST_GUARDRAIL_CE_REDUCE_TO
