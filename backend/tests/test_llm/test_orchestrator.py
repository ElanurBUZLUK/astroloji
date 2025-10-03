"""Unit tests for LLM routing orchestration components."""
import asyncio
import json
from types import SimpleNamespace

import pytest

from app.core.llm.orchestrator import (
    ConfidenceEstimator,
    IntentComplexityClassifier,
    LLMOrchestrator,
    ModelSelector,
    ProviderHealthMonitor,
)
from app.core.llm.provider_pool import LLMProviderPool, ProviderEntry
from app.core.llm.providers.base import LLMProvider, LLMResponse
from app.core.llm.strategies.auto_repair import AutoRepair
from app.pipelines.degrade import DegradeDecision
from app.schemas import RAGAnswerRequest


class FakeProvider(LLMProvider):
    async def generate(self, prompt: str = "", **kwargs):
        payload = {
            "answer": {
                "general_profile": "Updated profile",
                "strengths": ["Clear thinking"],
                "watchouts": ["Over-analysis"],
                "timing": [],
            },
            "citations": [],
            "confidence": 0.42,
            "limits": {"coverage_ok": True},
        }
        return LLMResponse(content=json.dumps(payload), tokens_used=128, raw={"latency_ms": 75})


@pytest.mark.asyncio
async def test_llm_orchestrator_generates_revision():
    pool = LLMProviderPool()
    provider = FakeProvider()
    pool.register(ProviderEntry(name="primary_openai", provider=provider, cooldown_seconds=1))
    pool.register(ProviderEntry(name="fallback_openai", provider=provider, cooldown_seconds=1))

    orchestrator = LLMOrchestrator(pool, AutoRepair())

    request = RAGAnswerRequest(query="Explain Mercury", birth_data=None)
    messages = [{"role": "user", "content": "Explain"}]
    coverage = {"score": 0.8, "pass": True, "topics": ["mercury"]}
    rag_response = SimpleNamespace(documents=[{"score": 0.6}], citations=[{"id": "doc"}], reranking_stats={})
    evidence_pack = {"diversity": {"unique_topics": 2}}
    degrade_state = DegradeDecision(active=False)

    outcome = await orchestrator.generate_revision(
        request=request,
        messages=messages,
        coverage=coverage,
        rag_response=rag_response,
        evidence_pack=evidence_pack,
        degrade_state=degrade_state,
        max_tokens=512,
    )

    assert outcome is not None
    assert outcome.repaired_payload is not None
    assert outcome.decision.model.key in {"small", "medium", "large"}


def test_intent_classifier_policy_risk():
    classifier = IntentComplexityClassifier(policy_keywords=["financial"])
    simple_request = RAGAnswerRequest(query="Tell me about finances", birth_data=None)
    result = classifier.classify(simple_request, {"pass": True, "topics": []})
    assert result == "policy_risk"


def test_confidence_estimator_levels():
    estimator = ConfidenceEstimator(low_threshold=0.4, high_threshold=0.7)
    coverage = {"score": 0.2, "pass": False}
    rag = SimpleNamespace(documents=[], citations=[])
    evidence_pack = {"diversity": {"unique_topics": 0}}
    score, level = estimator.score(coverage, rag, evidence_pack)
    assert level == "low"

    coverage = {"score": 0.8, "pass": True}
    rag = SimpleNamespace(documents=[{"score": 0.8}], citations=[1, 2, 3])
    evidence_pack = {"diversity": {"unique_topics": 3}}
    score, level = estimator.score(coverage, rag, evidence_pack)
    assert level == "high"


def test_model_selector_prefers_large_on_low_confidence():
    monitor = ProviderHealthMonitor()
    profiles = orchestrator_profiles_stub()
    selector = ModelSelector(profiles)
    degrade = DegradeDecision(active=False)
    health = {profile.provider: 1.0 for profile in profiles.values()}
    model, _ = selector.select("complex", "low", degrade, health)
    assert model.key == "large"


def test_model_selector_degrade_prefers_medium_on_low_confidence():
    monitor = ProviderHealthMonitor()
    profiles = orchestrator_profiles_stub()
    selector = ModelSelector(profiles)
    degrade = DegradeDecision(active=True)
    health = {profile.provider: 1.0 for profile in profiles.values()}
    model, _ = selector.select("simple", "low", degrade, health)
    assert model.key == "medium"


def orchestrator_profiles_stub():
    from app.core.llm.orchestrator import ModelProfile

    return {
        "small": ModelProfile("small", "s", ["primary_openai"], max_context=8000),
        "medium": ModelProfile("medium", "m", ["primary_openai", "alt_openai"], max_context=16000),
        "large": ModelProfile("large", "l", ["fallback_openai"], max_context=64000),
    }
