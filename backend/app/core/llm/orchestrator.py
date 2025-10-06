"""LLM orchestration with routing, health weighting, and schema validation."""
from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from pydantic import ValidationError

from backend.app.config import settings
from app.evaluation.observability import observability
from app.schemas import AnswerPayload, RAGAnswerRequest
from app.schemas.rag import PipelineDebugInfo
from app.pipelines.degrade import DegradeDecision
from .provider_pool import LLMProviderPool, ProviderEntry
from .providers.base import LLMResponse


@dataclass
class ModelProfile:
    """Describes one model tier and its associated provider options."""
    key: str
    name: str
    providers: List[str]
    max_context: int
    json_mode: bool = True
    tool_use: bool = False
    cost_weight: float = 1.0

    @property
    def default_provider(self) -> Optional[str]:
        return self.providers[0] if self.providers else None


@dataclass
class RoutingDecision:
    """Snapshot of the router's choice, including fallbacks and health data."""
    classification: str
    confidence_level: str
    confidence_score: float
    model: ModelProfile
    fallbacks: List[ModelProfile]
    degrade_active: bool
    health_snapshot: Dict[str, float]
    lora_enabled: bool
    provider: Optional[str] = None


@dataclass
class RoutingOutcome:
    """Result bundle returned to callers after routing completes."""
    response: LLMResponse
    decision: RoutingDecision
    attempts: int
    latency_ms: float
    used_lora: bool
    validation_error: Optional[str]
    repaired_payload: Optional[Dict[str, Any]]


class IntentComplexityClassifier:
    """Simple heuristic classifier for routing decisions."""

    def __init__(self, policy_keywords: Optional[Sequence[str]] = None) -> None:
        """Cache the keyword list used to detect policy-sensitive prompts."""
        raw_keywords = policy_keywords or settings.LLM_ROUTER_POLICY_KEYWORDS.split(",")
        self._policy_keywords = {kw.strip().lower() for kw in raw_keywords if kw.strip()}

    def classify(self, request: RAGAnswerRequest, coverage: Dict[str, Any]) -> str:
        """Label the request complexity to steer routing heuristics."""
        query = request.query.lower()
        if any(keyword in query for keyword in self._policy_keywords):
            return "policy_risk"
        if request.constraints.max_latency_ms and request.constraints.max_latency_ms <= 900:
            return "simple"
        if len(query) > 220 or query.count("?") > 1:
            return "complex"
        if not coverage.get("pass", True):
            return "complex"
        main_elements = coverage.get("topics", []) or []
        if len(main_elements) >= 4:
            return "complex"
        return "simple"


class ConfidenceEstimator:
    """Combines retrieval signals into a confidence score."""

    def __init__(self, low_threshold: float, high_threshold: float) -> None:
        """Store classification thresholds for low/medium/high confidence."""
        self._low = low_threshold
        self._high = high_threshold

    def score(
        self,
        coverage: Dict[str, Any],
        rag_response: Any,
        evidence_pack: Dict[str, Any],
    ) -> Tuple[float, str]:
        """Blend retrieval metrics into an overall confidence score and bucket."""
        coverage_score = coverage.get("score", 0.0)
        coverage_bonus = 0.15 if coverage.get("pass", False) else 0.0

        document_scores = []
        for doc in getattr(rag_response, "documents", []) or []:
            try:
                document_scores.append(float(doc.get("score", 0.0)))
            except (TypeError, ValueError):
                continue
        rerank_component = min(mean(document_scores), 1.0) if document_scores else 0.0

        citations = getattr(rag_response, "citations", None) or []
        citation_component = min(len(citations), 5) / 5.0

        diversity = evidence_pack.get("diversity", {})
        topic_count = float(diversity.get("unique_topics", 0))
        diversity_component = min(topic_count / 4.0, 0.2)

        raw_score = coverage_score * 0.45 + rerank_component * 0.25 + citation_component * 0.2 + diversity_component
        total = min(max(raw_score + coverage_bonus, 0.0), 1.0)

        if total < self._low:
            level = "low"
        elif total < self._high:
            level = "medium"
        else:
            level = "high"
        return total, level


class ProviderHealthMonitor:
    """Tracks rolling provider health scores based on latency and failures."""

    def __init__(self, window: int = 30) -> None:
        """Keep rolling latency and failure history for each provider."""
        self._latencies: Dict[str, deque] = {}
        self._failures: Dict[str, int] = {}
        self._window = window

    def record_success(self, provider: str, latency_ms: float) -> None:
        """Track a successful provider call and decay prior failures."""
        bucket = self._latencies.setdefault(provider, deque(maxlen=self._window))
        bucket.append(latency_ms)
        if provider in self._failures and self._failures[provider] > 0:
            self._failures[provider] = max(self._failures[provider] - 1, 0)

    def record_failure(self, provider: str) -> None:
        """Increment failure counters for a provider."""
        self._failures[provider] = self._failures.get(provider, 0) + 1

    def health_score(self, provider: str) -> float:
        """Return a penalty-adjusted health score for the provider."""
        latencies = self._latencies.get(provider, [])
        failure_count = self._failures.get(provider, 0)
        latency_penalty = 0.0
        if latencies:
            p95_latency = self._percentile(list(latencies), 95)
            latency_penalty = min(max((p95_latency - 1400) / 2000, 0.0), 0.4)
        failure_penalty = min(failure_count * 0.1, 0.6)
        return max(0.0, 1.0 - latency_penalty - failure_penalty)

    def snapshot(self, providers: Iterable[str]) -> Dict[str, float]:
        """Produce a health snapshot dictionary for a provider list."""
        return {name: self.health_score(name) for name in providers}

    def best_provider(self, provider_candidates: Sequence[str]) -> Optional[str]:
        """Select the healthiest provider among candidate names."""
        if not provider_candidates:
            return None
        scores = {name: self.health_score(name) for name in provider_candidates}
        return max(scores.items(), key=lambda item: item[1])[0]

    @staticmethod
    def _percentile(values: List[float], percentile: float) -> float:
        """Compute the given percentile using nearest-rank logic."""
        if not values:
            return 0.0
        ordered = sorted(values)
        rank = math.ceil(percentile / 100 * len(ordered))
        index = min(rank - 1, len(ordered) - 1)
        return float(ordered[index])


class ModelSelector:
    """Chooses the best model profile given routing signals."""

    def __init__(self, profiles: Dict[str, ModelProfile]) -> None:
        """Store the ordered model tiers to consult during selection."""
        self._profiles = profiles

    def select(
        self,
        classification: str,
        confidence_level: str,
        degrade_state: DegradeDecision,
        health_snapshot: Dict[str, float],
    ) -> Tuple[ModelProfile, List[ModelProfile]]:
        """Choose a primary model and ordered fallbacks given routing context."""
        order: List[str]
        if degrade_state.active:
            if confidence_level == "low":
                order = ["medium", "large", "small"]
            elif confidence_level == "medium":
                order = ["medium", "small", "large"]
            else:
                order = ["small", "medium", "large"]
        elif classification == "policy_risk":
            order = ["large", "medium", "small"]
        elif classification == "complex":
            order = ["medium", "large", "small"] if confidence_level != "low" else ["large", "medium", "small"]
        else:
            order = ["small", "medium", "large"] if confidence_level == "high" else ["medium", "small", "large"]

        ranked_profiles = [self._profiles[key] for key in order if key in self._profiles]
        chosen: Optional[ModelProfile] = None
        for profile in ranked_profiles:
            provider_health = max(health_snapshot.get(p, 1.0) for p in profile.providers)
            if provider_health >= 0.4:
                chosen = profile
                break
        if not chosen and ranked_profiles:
            chosen = max(ranked_profiles, key=lambda profile: max(health_snapshot.get(p, 0.0) for p in profile.providers))
        if not chosen:
            raise RuntimeError("No LLM models are available for routing")
        fallbacks = [profile for profile in ranked_profiles if profile is not chosen]
        return chosen, fallbacks


class LoRAStyler:
    """Feature-flagged LoRA styler hook (stub)."""

    def __init__(self, enabled: bool) -> None:
        """Remember whether the LoRA styling experiment is active."""
        self._enabled = enabled

    def apply(self, messages: List[Dict[str, Any]], classification: str) -> Tuple[List[Dict[str, Any]], bool]:
        """Optionally prepend tone guidance when LoRA styling is enabled."""
        if not self._enabled:
            return messages, False
        styled = list(messages)
        prefix = "Maintain an encouraging and structured tone." if classification == "simple" else "Adopt a precise, technical tone with explicit citations."
        system_idx = next((idx for idx, msg in enumerate(styled) if msg.get("role") == "system"), None)
        if system_idx is not None:
            styled[system_idx] = {**styled[system_idx], "content": f"{prefix}\n\n{styled[system_idx]['content']}"}
        else:
            styled.insert(0, {"role": "system", "content": prefix})
        return styled, True


class SchemaValidator:
    """Validates repaired payloads against the API schema."""

    def validate(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate a repaired payload against the API contract."""
        try:
            AnswerPayload.model_validate(payload)
            return True, None
        except ValidationError as exc:  # pragma: no cover - validation error path
            return False, str(exc)


class LLMOrchestrator:
    """Coordinates routing, health weighting, schema validation, and LoRA styling."""

    def __init__(
        self,
        provider_pool: LLMProviderPool,
        auto_repair,
    ) -> None:
        """Wire together routing dependencies and precalculate timeout tables."""
        self._pool = provider_pool
        self._auto_repair = auto_repair
        self._classifier = IntentComplexityClassifier()
        self._confidence = ConfidenceEstimator(
            low_threshold=settings.LLM_ROUTER_CONF_LOW,
            high_threshold=settings.LLM_ROUTER_CONF_HIGH,
        )
        self._health_monitor = ProviderHealthMonitor()
        self._profiles = self._build_profiles()
        self._selector = ModelSelector(self._profiles)
        self._lora = LoRAStyler(settings.LLM_ROUTER_LORA_ENABLED)
        self._validator = SchemaValidator()
        self._timeout_table = {
            "small": getattr(settings, "LLM_ROUTER_TIMEOUT_SMALL_MS", 1200),
            "medium": getattr(settings, "LLM_ROUTER_TIMEOUT_MEDIUM_MS", 1600),
            "large": getattr(settings, "LLM_ROUTER_TIMEOUT_LARGE_MS", 2200),
        }

    def _build_profiles(self) -> Dict[str, ModelProfile]:
        """Construct the routing profile table from settings."""
        fallback_provider = settings.LLM_ROUTER_LARGE_PROVIDER or settings.LLM_ROUTER_MEDIUM_PROVIDER
        fallback_model = settings.LLM_ROUTER_LARGE_MODEL or settings.LLM_ROUTER_MEDIUM_MODEL

        def _providers(raw: str) -> List[str]:
            return [segment.strip() for segment in str(raw).split(",") if segment.strip()]

        return {
            "small": ModelProfile(
                key="small",
                name=settings.LLM_ROUTER_SMALL_MODEL,
                providers=_providers(settings.LLM_ROUTER_SMALL_PROVIDER),
                max_context=8_000,
                json_mode=True,
                tool_use=False,
                cost_weight=0.6,
            ),
            "medium": ModelProfile(
                key="medium",
                name=settings.LLM_ROUTER_MEDIUM_MODEL,
                providers=_providers(settings.LLM_ROUTER_MEDIUM_PROVIDER),
                max_context=32_000,
                json_mode=True,
                tool_use=True,
                cost_weight=1.0,
            ),
            "large": ModelProfile(
                key="large",
                name=fallback_model,
                providers=_providers(fallback_provider),
                max_context=200_000,
                json_mode=True,
                tool_use=True,
                cost_weight=1.6,
            ),
        }

    async def generate_revision(
        self,
        *,
        request: RAGAnswerRequest,
        messages: List[Dict[str, Any]],
        coverage: Dict[str, Any],
        rag_response: Any,
        evidence_pack: Dict[str, Any],
        degrade_state: DegradeDecision,
        max_tokens: Optional[int],
    ) -> Optional[RoutingOutcome]:
        """Route an answer revision request through the best available provider."""
        classification = self._classifier.classify(request, coverage)
        confidence_score, confidence_level = self._confidence.score(coverage, rag_response, evidence_pack)
        health_snapshot = self._health_monitor.snapshot(
            provider for profile in self._profiles.values() for provider in profile.providers
        )
        timeout_factor = getattr(degrade_state, "timeout_factor", 1.0)

        selected_model, fallbacks = self._selector.select(
            classification=classification,
            confidence_level=confidence_level,
            degrade_state=degrade_state,
            health_snapshot=health_snapshot,
        )

        if degrade_state.llm_overrides.get("force_upgrade") and "large" in self._profiles:
            selected_model = self._profiles["large"]
            fallbacks = [profile for profile in self._profiles.values() if profile.key != "large"]

        styled_messages, used_lora = self._lora.apply(messages, classification)
        start_time = time.perf_counter()
        attempts: int = 0
        validation_error: Optional[str] = None
        repaired_payload: Optional[Dict[str, Any]] = None
        response: Optional[LLMResponse] = None
        decision = RoutingDecision(
            classification=classification,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            model=selected_model,
            fallbacks=fallbacks,
            degrade_active=degrade_state.active,
            health_snapshot=health_snapshot,
            lora_enabled=used_lora,
        )

        for profile in [selected_model] + fallbacks:
            provider_candidates = [p for p in profile.providers if self._pool.get_provider(p)]
            if not provider_candidates:
                continue
            attempts += 1
            try:
                base_timeout = self._timeout_table.get(profile.key, self._timeout_table.get("medium", 1600))
                timeout_ms = int(base_timeout * timeout_factor)
                best_provider = self._health_monitor.best_provider(provider_candidates)
                chosen_provider = best_provider or provider_candidates[0]
                decision.provider = chosen_provider
                response = await self._pool.generate_with(
                    provider_name=chosen_provider,
                    messages=styled_messages,
                    json_mode=profile.json_mode,
                    max_tokens=max_tokens,
                    model=profile.name,
                    timeout_ms=timeout_ms,
                )
                latency_ms = (time.perf_counter() - start_time) * 1000
                self._health_monitor.record_success(chosen_provider, latency_ms)
                observability.metrics.record_histogram("llm_router_latency", latency_ms)
                observability.metrics.record_histogram("llm_router_confidence", confidence_score)
                break
            except Exception:  # pragma: no cover - depends on provider failures
                for candidate in provider_candidates:
                    self._health_monitor.record_failure(candidate)
                continue

        if not response:
            return None

        latency_ms = (time.perf_counter() - start_time) * 1000
        try:
            repaired = self._auto_repair.repair(response.content)
        except Exception:  # pragma: no cover - repair failure
            repaired = {}
        if isinstance(repaired, dict):
            repaired_payload = repaired
            valid, validation_error = self._validator.validate(repaired)
            if not valid:
                validation_error = validation_error or "schema_validation_failed"
        else:  # pragma: no cover - unexpected repair output
            validation_error = "invalid_repair_payload"

        return RoutingOutcome(
            response=response,
            decision=decision,
            attempts=attempts,
            latency_ms=latency_ms,
            used_lora=used_lora,
            validation_error=validation_error,
            repaired_payload=repaired_payload,
        )

    def enrich_debug(self, debug: PipelineDebugInfo, outcome: Optional[RoutingOutcome]) -> None:
        """Embed routing diagnostics into the pipeline debug payload."""
        if not outcome:
            return
        debug.routing = {
            "classification": outcome.decision.classification,
            "confidence": {
                "level": outcome.decision.confidence_level,
                "score": round(outcome.decision.confidence_score, 3),
            },
            "model": outcome.decision.model.key,
            "provider": outcome.decision.provider or (outcome.decision.model.default_provider or ""),
            "fallbacks": [profile.key for profile in outcome.decision.fallbacks],
            "attempts": outcome.attempts,
            "latency_ms": round(outcome.latency_ms, 2),
            "lora": outcome.used_lora,
            "validation_error": outcome.validation_error,
            "health_snapshot": outcome.decision.health_snapshot,
            "degrade_active": outcome.decision.degrade_active,
        }
