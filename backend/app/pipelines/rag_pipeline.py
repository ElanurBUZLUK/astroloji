"""Orchestrates the Sprint 1 RAG + interpretation pipeline."""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
import logging

from fastapi import HTTPException, status

from app.interpreters.core import InterpretationEngine
from app.interpreters.output_composer import OutputMode, OutputStyle
from app.rag.core import RAGSystem
from app.rag.planner import QueryPlanner, PlanStep
from app.rag.retriever import build_retriever_profile, search_hybrid
from app.rag.re_ranker import rerank as bge_rerank
from app.rag import kg_connector, sql_connector
from app.schemas import (
    AnswerBody,
    AnswerMetadata,
    AnswerPayload,
    CitationEntry,
    ChartContext,
    RAGAnswerRequest,
    RAGAnswerResponse,
    PipelineDebugInfo,
    ScoredTheme,
    TimingWindow,
)
from app.pipelines.cache import RedisSemanticCache, SemanticCache
from app.pipelines.claim_alignment import score_claim_alignment
from app.pipelines.sanitization import (
    sanitize_text,
    sanitize_sequence,
    apply_answer_safeguards,
)
from app.pipelines.degrade import DegradePolicyManager, DegradeDecision
from app.pipelines.quality_control import (
    AnswerQualityFilter,
    TemplateFallbackBuilder,
    AnswerQualityReport,
)
from backend.app.config import settings
from app.pipelines.chart_builder import ChartBootstrapper
from app.core.llm.providers.openai import OpenAIProvider
from app.core.llm.provider_pool import LLMProviderPool, ProviderEntry
from app.core.llm.orchestrator import LLMOrchestrator, RoutingOutcome
from app.core.llm.strategies.prompt_engineer import PromptEngineer, PromptContext
from app.core.llm.strategies.auto_repair import AutoRepair
from app.evaluation import prometheus_bridge
from app.evaluation.metrics import RAGMetrics
from app.evaluation.observability import observability


class RAGAnswerPipeline:
    """Runs the high level steps outlined in the README pipeline."""

    def __init__(
        self,
        semantic_cache: SemanticCache | None = None,
        chart_bootstrapper: ChartBootstrapper | None = None,
    ) -> None:
        """Instantiate pipeline dependencies, building defaults when not provided."""
        self._cache = semantic_cache or self._build_cache()
        self._chart_bootstrapper = chart_bootstrapper or ChartBootstrapper()
        self._rag = RAGSystem()
        self._prompt_engineer = PromptEngineer()
        self._auto_repair = AutoRepair()
        self._llm_pool = self._build_llm_pool()
        self._llm_orchestrator = (
            LLMOrchestrator(self._llm_pool, self._auto_repair)
            if self._llm_pool
            else None
        )
        self._logger = logging.getLogger("rag_pipeline")
        self._planner = QueryPlanner()
        self._degrade = DegradePolicyManager()
        self._last_routing_outcome: Optional[RoutingOutcome] = None
        self._retriever_profile = build_retriever_profile()
        self._dense_store = self._retriever_profile.get("dense")
        self._sparse_store = self._retriever_profile.get("sparse")
        self._quality_filter = AnswerQualityFilter()
        self._fallback_builder = TemplateFallbackBuilder()
        self._last_quality_report: Optional[AnswerQualityReport] = None
        self._quality_fallback_issues: Optional[List[str]] = None

    async def run(self, request: RAGAnswerRequest) -> RAGAnswerResponse:
        """Execute the end-to-end RAG and interpretation workflow for a user query."""
        start_time = time.perf_counter()
        self._last_routing_outcome = None
        cache_key = self._cache_key(request)

        cached = await self._cache.get(cache_key)
        if cached:
            return cached

        masked_request = self._mask_request_for_audit(request)

        chart_result = await self._chart_bootstrapper.load(request.birth_data)
        chart_data = chart_result.chart_data

        if not chart_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chart data could not be prepared for interpretation.",
            )

        engine = InterpretationEngine(
            language=request.locale_settings.language,
            style=self._map_style(request.locale_settings.user_level),
        )

        interpretation = engine.interpret_chart(
            chart_data=chart_data,
            mode=self._map_mode(request.mode_settings.mode),
        )

        interpretation_summary = engine.get_interpretation_summary(chart_data)
        main_elements = interpretation_summary.get("main_themes", [])

        rag_context = {
            "user_level": request.locale_settings.user_level,
            "focus_areas": main_elements,
            "chart_elements": main_elements,
        }
        degrade_state = self._degrade.evaluate()
        observability.metrics.set_gauge(
            "rag_degrade_active", 1.0 if degrade_state.active else 0.0
        )
        prometheus_bridge.set_degrade_active(degrade_state.active)

        rag_policy = degrade_state.rag_overrides if degrade_state.active else None
        rag_response = await self._rag.query_for_interpretation(
            main_elements, rag_context, policy=rag_policy
        )

        base_query = getattr(request, "query", "") or ""
        hybrid_query = (" ".join(main_elements[:3]) or base_query or "astroloji yorum")
        policy_top_k = rag_policy.get("top_k") if rag_policy else None
        top_k_policy = max(1, int(policy_top_k or 5))
        await self._hydrate_documents_with_hybrid(
            hybrid_query,
            top_k_policy,
            rag_response,
        )

        rag_response.retrieved_content = sanitize_sequence(rag_response.retrieved_content or [])
        for doc in rag_response.documents or []:
            if isinstance(doc, dict) and "content" in doc:
                doc["content"] = sanitize_text(doc.get("content", ""))

        coverage = self._evaluate_coverage(
            main_elements=main_elements,
            documents=rag_response.documents,
            mode=request.mode_settings.mode,
        )
        observability.metrics.record_histogram("coverage_score", coverage.get("score", 0.0))

        plan_steps: List[PlanStep] = []
        supplemental_docs: List[Dict[str, Any]] = []
        skip_multi_hop = bool(degrade_state.flags.get("skip_multi_hop"))
        if not coverage.get("pass", True) and not skip_multi_hop:
            plan_steps = await self._run_multi_hop(
                main_elements,
                coverage,
                chart_result.chart_data,
                request,
            )
            for step in plan_steps:
                supplemental_docs.extend(step.metadata.get("docs", []))
            if supplemental_docs:
                rag_response.documents.extend(supplemental_docs)
                coverage = self._evaluate_coverage(
                    main_elements=main_elements,
                    documents=rag_response.documents,
                    mode=request.mode_settings.mode,
                )

        evidence_pack = self._build_evidence_pack(
            documents=rag_response.documents,
            main_elements=main_elements,
        )

        chart_context = self._build_chart_context(chart_result.context, interpretation_summary)
        payload = await self._build_answer_payload(
            request=request,
            interpretation_summary=interpretation_summary,
            interpretation=interpretation,
            rag_response=rag_response,
            coverage=coverage,
            evidence_pack=evidence_pack,
            degrade_state=degrade_state,
        )

        alignment_result = score_claim_alignment(payload, rag_response.documents)
        alignment_score = alignment_result.get("score", 0.0)
        payload.limits.citation_alignment = alignment_score
        payload.limits.claims_supported_ratio = alignment_result.get("supported_ratio")
        observability.metrics.record_histogram("citation_alignment_score", alignment_score)

        citation_upgrade = False
        if alignment_score < 0.75 or (alignment_result.get("supported_ratio") or 0.0) < 0.75:
            citation_upgrade = True
            degrade_state.llm_overrides["force_upgrade"] = True
            degrade_state.flags["citation_alignment_score"] = alignment_score
            degrade_state.flags["citation_supported_ratio"] = alignment_result.get("supported_ratio")

        if payload.citations:
            citation_map = {citation.doc_id: citation for citation in payload.citations}
            for claim in alignment_result.get("claims", []):
                citation_id = claim.get("citation_id")
                span_text = claim.get("span")
                if not citation_id or not span_text:
                    continue
                citation = citation_map.get(citation_id)
                if citation:
                    citation.span = span_text

        evaluation_metrics = {}
        if request.evaluation:
            evaluation_metrics = self._record_benchmark_metrics(
                request.evaluation,
                rag_response,
                payload,
            )

        debug = PipelineDebugInfo(
            intent=request.mode_settings.mode,
            complexity=float(len(main_elements)) / 5.0 if main_elements else 0.1,
            retrieval_stats=rag_response.retrieval_stats or {},
            rerank_stats=rag_response.reranking_stats or {},
            guardrail_notes=self._guardrail_notes(
                payload,
                coverage,
                evidence_pack,
                alignment_result,
                degrade_state,
                quality=self._last_quality_report,
                fallback_issues=self._quality_fallback_issues,
            ),
            coverage=coverage,
            evidence={"diversity": evidence_pack.get("diversity", {}), "conflict_count": len(evidence_pack.get("conflicts", []))},
            plan=[
                {
                    "type": step.step_type,
                    "topic": step.topic,
                    "reason": step.reason,
                    "skipped": step.metadata.get("skipped", False),
                    "docs": [doc.get("source_id") for doc in step.metadata.get("docs", [])],
                }
                for step in plan_steps
            ],
            claim_alignment=alignment_result,
            degrade={
                "active": degrade_state.active,
                "reasons": degrade_state.reasons,
                "flags": degrade_state.flags,
                "rag_overrides": degrade_state.rag_overrides,
                "llm_overrides": degrade_state.llm_overrides,
                "timeout_factor": degrade_state.timeout_factor,
                "cost_actions": degrade_state.cost_actions,
            },
            evaluation_metrics=evaluation_metrics,
        )

        if self._llm_orchestrator:
            self._llm_orchestrator.enrich_debug(debug, self._last_routing_outcome)

        response = RAGAnswerResponse(
            request=request,
            chart_context=chart_context,
            payload=payload,
            debug=debug,
            documents=rag_response.documents,
            evidence_pack=evidence_pack,
        )

        cache_ttl_factor = degrade_state.flags.get("cache_ttl_factor") if degrade_state.flags else None
        await self._cache.set(cache_key, response, ttl_factor=cache_ttl_factor)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        prometheus_bridge.record_rag_latency(request.mode_settings.mode, elapsed_ms / 1000.0)
        response.payload.limits.processing_time_ms = elapsed_ms
        response.payload.limits.latency_budget_ms = request.constraints.max_latency_ms
        observability.metrics.record_histogram("rag_latency", elapsed_ms)

        self._audit_interpretation(masked_request, response, coverage)

        return response

    def _record_benchmark_metrics(
        self,
        evaluation,
        rag_response,
        payload: AnswerPayload,
    ) -> dict[str, float]:
        """Record retrieval and groundedness metrics when benchmark metadata is present."""
        rag_metrics = RAGMetrics()
        retrieved_ids: list[str] = []
        for doc in rag_response.documents or []:
            if isinstance(doc, dict):
                doc_id = doc.get("source_id") or doc.get("doc_id")
            else:
                doc_id = getattr(doc, "source_id", None)
            if doc_id:
                retrieved_ids.append(str(doc_id))

        relevant_docs = [str(doc_id) for doc_id in (evaluation.relevant_documents or [])]
        at_k = max(1, evaluation.at_k)
        precision_at_k = rag_metrics.calculate_precision_at_k(retrieved_ids, relevant_docs, k=at_k)
        recall_at_k = rag_metrics.calculate_recall_at_k(retrieved_ids, relevant_docs, k=at_k)

        ndcg = 0.0
        if evaluation.relevance_scores:
            ndcg = rag_metrics.calculate_ndcg(
                retrieved_ids,
                {str(k): v for k, v in evaluation.relevance_scores.items()},
                k=at_k,
            )

        citations_payload = []
        for citation in payload.citations:
            citations_payload.append(
                {
                    "doc_id": citation.doc_id,
                    "credibility": 0.85 if citation.doc_id in relevant_docs else 0.65,
                }
            )
        groundedness = rag_metrics.calculate_groundedness(
            payload.answer.general_profile,
            citations_payload,
        )

        citation_coverage = None
        if evaluation.expected_citations:
            expected_set = {str(doc_id) for doc_id in evaluation.expected_citations}
            actual_citations = {citation.doc_id for citation in payload.citations}
            if expected_set:
                citation_coverage = len(expected_set & actual_citations) / len(expected_set)

        tags = {
            "benchmark": evaluation.benchmark_id,
            "case": evaluation.case_id,
        }
        observability.metrics.record_histogram(
            "benchmark_recall_at_k",
            recall_at_k,
            tags=tags,
        )
        observability.metrics.record_histogram(
            "benchmark_precision_at_k",
            precision_at_k,
            tags=tags,
        )
        observability.metrics.record_histogram(
            "benchmark_groundedness",
            groundedness,
            tags=tags,
        )
        if ndcg:
            observability.metrics.record_histogram(
                "benchmark_ndcg",
                ndcg,
                tags=tags,
            )
        if citation_coverage is not None:
            observability.metrics.record_histogram(
                "benchmark_citation_coverage",
                citation_coverage,
                tags=tags,
            )

        return {
            "at_k": at_k,
            "recall_at_k": recall_at_k,
            "precision_at_k": precision_at_k,
            "groundedness": groundedness,
            "ndcg": ndcg,
            "citation_coverage": citation_coverage,
        }

    def _build_chart_context(
        self, base_context: ChartContext, summary: dict[str, Any]
    ) -> ChartContext:
        """Augment the base chart context with scored themes from interpretation summary."""
        context = base_context.model_copy(deep=True)
        themes = [
            ScoredTheme(
                theme=theme,
                score=round(8.0 - idx * 0.5, 2),
                evidence=summary.get("scoring_summary", {}).get(theme, []),
            )
            for idx, theme in enumerate(summary.get("main_themes", [])[:3])
        ]
        context.scored_themes = themes
        return context

    async def _build_answer_payload(
        self,
        request: RAGAnswerRequest,
        interpretation_summary: dict[str, Any],
        interpretation: Any,
        rag_response: Any,
        coverage: dict,
        evidence_pack: dict,
        degrade_state: DegradeDecision,
    ) -> AnswerPayload:
        """Assemble the structured answer payload and optionally run LLM revision."""
        strengths = [
            section.content
            for section in interpretation.sections[:2]
            if section.content
        ] or ["Chart shows resilient mindset and adaptability."]
        watchouts = interpretation.warnings or ["Monitor collective outer planet transits for broader shifts."]
        timing_windows: List[TimingWindow] = []

        rag_snippets = rag_response.retrieved_content or []
        if rag_snippets:
            watchouts.append("Kaynaklardan öne çıkan not: " + rag_snippets[0][:120] + "...")

        def _safe_int(value: Any, default: int) -> int:
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        doc_meta_map: Dict[str, Dict[str, Any]] = {}
        doc_content_map: Dict[str, str] = {}
        for doc in rag_response.documents or []:
            metadata = doc.get("metadata") or {}
            primary_id = metadata.get("chunk_id") or metadata.get("doc_id") or doc.get("source_id")
            if primary_id:
                doc_meta_map[primary_id] = metadata
                doc_content_map[primary_id] = doc.get("content", "")
            source_id = doc.get("source_id")
            if source_id and source_id not in doc_meta_map:
                doc_meta_map[source_id] = metadata
                doc_content_map[source_id] = doc.get("content", "")

        raw_citations = list(rag_response.citations or [])
        citations: List[CitationEntry] = []

        if raw_citations:
            for index, cite in enumerate(raw_citations):
                source_id = getattr(cite, "source_id", None) or getattr(cite, "id", None)
                metadata = doc_meta_map.get(source_id, {})
                snippet = getattr(cite, "content_snippet", None) or doc_content_map.get(source_id, "")[:200]
                citations.append(
                    CitationEntry(
                        doc_id=source_id or f"doc-{index+1}",
                        section=_safe_int(metadata.get("section"), index),
                        line_start=_safe_int(metadata.get("line_start"), 0),
                        line_end=_safe_int(metadata.get("line_end"), 0),
                        tradition=metadata.get("tradition") or getattr(cite, "source_type", None),
                        language=metadata.get("language"),
                        source_url=getattr(cite, "url", None) or metadata.get("source_url"),
                        snippet=snippet,
                    )
                )
        elif doc_meta_map:
            # Fallback: synthesize citations from available documents
            for index, (doc_id, metadata) in enumerate(doc_meta_map.items()):
                content = doc_content_map.get(doc_id, "")
                citations.append(
                    CitationEntry(
                        doc_id=doc_id or f"doc-{index+1}",
                        section=_safe_int(metadata.get("section"), index),
                        line_start=_safe_int(metadata.get("line_start"), 0),
                        line_end=_safe_int(metadata.get("line_end"), 0),
                        tradition=metadata.get("tradition"),
                        language=metadata.get("language"),
                        source_url=metadata.get("source_url"),
                        snippet=(content or "")[:200],
                    )
                )
                if len(citations) >= 1:
                    break

        if not citations:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Citations required",
            )

        answer_body = AnswerBody(
            general_profile=interpretation.summary,
            strengths=strengths,
            watchouts=watchouts,
            timing=timing_windows,
            collective_note="Bu yorum, genel astrolojik ilkeler temel alınarak oluşturuldu.",
            mythic_refs=["Satürn = Kronos, zamanın efendisi."],
        )
        answer_body = apply_answer_safeguards(answer_body)

        coverage_ok = coverage.get("pass", bool(rag_snippets))
        coverage_score = coverage.get("score")
        collective_note = self._collective_tone_notice(evidence_pack, default=answer_body.collective_note)
        answer_body.collective_note = collective_note
        hallucination = "low" if coverage_ok and rag_snippets else "medium"
        metadata = AnswerMetadata(
            coverage_ok=coverage_ok,
            hallucination_risk=hallucination,
            coverage_score=coverage_score,
        )

        try:
            answer_payload = AnswerPayload(
                answer=answer_body,
                citations=citations,
                confidence=float(getattr(interpretation, "overall_confidence", 0.0)),
                limits=metadata,
                evidence_summary=interpretation.evidence_summary,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        allow_llm_revision = True
        if degrade_state.active and degrade_state.llm_overrides.get("skip_revision"):
            allow_llm_revision = False

        if self._llm_orchestrator and allow_llm_revision:
            llm_revision = await self._maybe_generate_llm_revision(
                answer_payload,
                request,
                coverage,
                evidence_pack,
                rag_response,
                degrade_state,
            )
            if llm_revision:
                answer_payload = llm_revision
                apply_answer_safeguards(answer_payload.answer)

        quality_report = self._quality_filter.evaluate(answer_payload)
        if quality_report.issues:
            prometheus_bridge.record_quality_issues(quality_report.issues)
        self._last_quality_report = quality_report
        self._quality_fallback_issues = None
        if not quality_report.passed:
            self._quality_fallback_issues = list(quality_report.issues)
            prometheus_bridge.record_quality_fallback(self._quality_fallback_issues)
            self._logger.warning(
                "Answer quality filter triggered",
                extra={"issues": quality_report.issues},
            )
            answer_payload = self._fallback_builder.build(
                request=request,
                interpretation_summary=interpretation_summary,
                rag_response=rag_response,
                base_payload=answer_payload,
                issues=quality_report.issues,
                coverage=coverage,
            )
            apply_answer_safeguards(answer_payload.answer)
            quality_report = self._quality_filter.evaluate(answer_payload)
            self._last_quality_report = quality_report
            if not quality_report.passed:
                self._logger.error(
                    "Fallback payload still failed quality filter",
                    extra={"issues": quality_report.issues},
                )

        return answer_payload

    def _collective_tone_notice(self, evidence_pack: dict, default: Optional[str] = None) -> str:
        """Pick the collective-tone disclaimer based on detected evidence conflicts."""
        conflicts = evidence_pack.get("conflicts", [])
        if conflicts:
            return "Bu etkiler jenerasyonel veya kolektif tonlar içerir; kişisel düzeyde filtreleyin."
        return default or "Bu yorum, genel astrolojik ilkeler temel alınarak oluşturuldu."

    def _cache_key(self, request: RAGAnswerRequest) -> str:
        """Generate a deterministic cache key from query text and birth fingerprint."""
        birth_fingerprint = {
            "date": request.birth_data.date if request.birth_data else "no-date",
            "time": request.birth_data.time if request.birth_data else "no-time",
            "lat": request.birth_data.lat if request.birth_data else "no-lat",
            "lng": request.birth_data.lng if request.birth_data else "no-lng",
        }
        fingerprint = json.dumps(
            {
                "query": request.query,
                "mode": request.mode_settings.mode,
                "locale": request.locale_settings.locale,
                "birth": birth_fingerprint,
            },
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(fingerprint).hexdigest()

    def _build_evidence_pack(
        self, documents: List[dict], main_elements: List[str]
    ) -> dict:
        """Summarize retrieved documents into diversity and conflict diagnostics."""
        if not documents:
            return {
                "documents": [],
                "diversity": {
                    "total": 0,
                    "unique_topics": 0,
                    "unique_schools": 0,
                    "unique_languages": 0,
                },
                "conflicts": [],
            }

        processed_docs: List[dict] = []
        topics_map: Dict[str, List[dict]] = {}
        schools = set()
        languages = set()

        for doc in documents:
            metadata = doc.get("metadata") or {}
            topic = metadata.get("topic") or "unknown"
            school = metadata.get("school") or "unknown"
            language = metadata.get("language") or "unknown"
            content = doc.get("content", "")
            snippet = content[:200].strip()
            tone = self._classify_tone(content, metadata)

            schools.add(school)
            languages.add(language)

            info = {
                "source_id": doc.get("source_id"),
                "score": round(doc.get("score", 0.0), 3),
                "topic": topic,
                "school": school,
                "language": language,
                "tone": tone,
                "snippet": snippet,
            }
            processed_docs.append(info)
            topics_map.setdefault(topic, []).append(info)

        conflicts: List[dict] = []
        supportive_keywords = {"support", "benefit", "harmon", "positive", "favorable"}
        challenging_keywords = {"challenge", "difficult", "malefic", "caution", "warning", "tension"}

        for topic, docs in topics_map.items():
            if topic == "unknown":
                continue
            tone_set = {doc["tone"] for doc in docs if doc["tone"] != "neutral"}
            if len(tone_set) > 1:
                conflicts.append(
                    {
                        "topic": topic,
                        "summary": f"mixed tones detected ({', '.join(sorted(tone_set))})",
                        "documents": [doc["source_id"] for doc in docs],
                    }
                )
            else:
                # fallback keyword check if tone neutral
                if "neutral" in tone_set or not tone_set:
                    has_supportive = any(
                        any(word in doc["snippet"].lower() for word in supportive_keywords)
                        for doc in docs
                    )
                    has_challenging = any(
                        any(word in doc["snippet"].lower() for word in challenging_keywords)
                        for doc in docs
                    )
                    if has_supportive and has_challenging:
                        conflicts.append(
                            {
                                "topic": topic,
                                "summary": "supportive and challenging cues appear together",
                                "documents": [doc["source_id"] for doc in docs],
                            }
                        )

        diversity = {
            "total": len(processed_docs),
            "unique_topics": len(topics_map),
            "unique_schools": len(schools),
            "unique_languages": len(languages),
            "elements_covered": len({elt.lower() for elt in main_elements if elt}),
        }

        return {
            "documents": processed_docs,
            "diversity": diversity,
            "conflicts": conflicts,
        }

    def _mask_request_for_audit(self, request: RAGAnswerRequest) -> Dict[str, Any]:
        """Strip PII from the incoming request before logging or auditing."""
        masked_birth = None
        if request.birth_data:
            masked_birth = {
                "date": f"{request.birth_data.date[:4]}-XX-XX" if request.birth_data.date else None,
                "time": "XX:XX" if request.birth_data.time else None,
                "tz": request.birth_data.tz,
                "lat": round(request.birth_data.lat, 2) if request.birth_data.lat is not None else None,
                "lng": round(request.birth_data.lng, 2) if request.birth_data.lng is not None else None,
            }
        return {
            "query": request.query[:200],
            "mode": request.mode_settings.mode,
            "locale": request.locale_settings.locale,
            "user_level": request.locale_settings.user_level,
            "ab_profile": request.ab_flags.profile,
            "birth_data": masked_birth,
        }

    def _classify_tone(self, content: str, metadata: Dict[str, Any]) -> str:
        """Heuristically label a document snippet as supportive, challenging, or neutral."""
        if not content:
            return "neutral"
        text = content.lower()
        positive_markers = [
            "support", "benefit", "favorable", "harmon", "opportunity", "peak"
        ]
        negative_markers = [
            "challenge", "difficult", "caution", "warning", "malefic", "tension"
        ]

        positive_hits = sum(marker in text for marker in positive_markers)
        negative_hits = sum(marker in text for marker in negative_markers)

        if positive_hits > negative_hits and positive_hits > 0:
            return "supportive"
        if negative_hits > positive_hits and negative_hits > 0:
            return "challenging"
        return metadata.get("tone") or "neutral"

    def _evaluate_coverage(
        self, main_elements: List[str], documents: List[dict], mode: str
    ) -> dict:
        """Score how well retrieved documents cover the requested chart elements."""
        if not documents:
            return {
                "pass": False,
                "score": 0.0,
                "issues": ["No documents retrieved for coverage gate."],
                "schools": [],
                "topics": [],
            }

        normalized_elements = [element.lower() for element in main_elements if element]
        if not normalized_elements:
            coverage_score = 1.0
            normalized_elements = []
        else:
            match_count = 0
            for element in normalized_elements:
                if any(element in (doc.get("content", "").lower()) for doc in documents):
                    match_count += 1
            base = max(len(normalized_elements), 1)
            coverage_score = min(1.0, match_count / base)


        schools = {
            (doc.get("metadata", {}) or {}).get("school")
            for doc in documents
            if doc.get("metadata")
        }
        topics = {
            (doc.get("metadata", {}) or {}).get("topic")
            for doc in documents
            if doc.get("metadata")
        }
        schools.discard(None)
        topics.discard(None)

        has_traditional = any(
            school and ("traditional" in school.lower() or "classical" in school.lower())
            for school in schools
        )
        has_modern = any(
            school and "modern" in school.lower() for school in schools
        )

        required_topic = None
        element_text = " ".join(normalized_elements)
        if "zodiacal" in element_text or "releasing" in element_text or "zr" in element_text:
            required_topic = "zodiacal_releasing"
        elif "profection" in element_text:
            required_topic = "profection"
        elif "firdaria" in element_text:
            required_topic = "firdaria"
        elif "almuten" in element_text:
            required_topic = "almuten"

        issues: List[str] = []
        if coverage_score < 0.7:
            issues.append("Coverage score below threshold (0.7).")
        if not has_traditional:
            issues.append("Traditional/classical source not found.")
        if not has_modern:
            issues.append("Modern source not found.")
        if required_topic and required_topic not in topics:
            issues.append(f"Required topic '{required_topic}' missing in evidence.")

        passes = coverage_score >= 0.7 and has_traditional
        if required_topic:
            passes = passes and required_topic in topics

        return {
            "pass": passes,
            "score": round(coverage_score, 3),
            "issues": issues,
            "schools": sorted(schools),
            "topics": sorted(topics),
        }

    def _audit_interpretation(
        self,
        masked_request: Dict[str, Any],
        response: RAGAnswerResponse,
        coverage: Dict[str, Any],
    ) -> None:
        """Emit a structured audit log for monitoring interpretation quality."""
        record = {
            "request": masked_request,
            "coverage": coverage,
            "confidence": response.payload.confidence,
            "coverage_score": response.payload.limits.coverage_score,
            "citations": len(response.payload.citations or []),
            "processing_ms": response.payload.limits.processing_time_ms,
        }
        self._logger.info("interpretation_audit", extra={"audit": record})

    async def _execute_plan(
        self, plan: List[PlanStep], chart_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Run planner steps against connectors to fetch supplemental documents."""
        supplemental_docs: List[Dict[str, Any]] = []
        for step in plan:
            if step.step_type == "kg":
                supplemental_docs.extend(kg_connector.fetch(step.topic))
            elif step.step_type == "sql":
                if step.topic == "timing_overview":
                    supplemental_docs.extend(sql_connector.summarize_timing(chart_data))
                else:
                    supplemental_docs.extend(sql_connector.summarize_core(chart_data))
        return supplemental_docs

    async def _hydrate_documents_with_hybrid(
        self,
        query_text: str,
        top_k: int,
        rag_response: Any,
        filters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Refresh RAG documents using the configured hybrid retrieval profile."""

        if not (self._dense_store or self._sparse_store):
            return

        try:
            results = await search_hybrid(
                query_text,
                max(1, top_k),
                self._dense_store,
                self._sparse_store,
                filters=filters,
            )
        except Exception as exc:  # pragma: no cover - best-effort fallback
            self._logger.warning("Hybrid retrieval failed: %s", exc)
            return

        if not results:
            return

        try:
            reranked = bge_rerank(query_text, results) or results
        except Exception as exc:  # pragma: no cover - reranker optional
            self._logger.warning("BGE reranker unavailable: %s", exc)
            reranked = results

        limited = reranked[: max(1, top_k)]
        documents: List[Dict[str, Any]] = []
        for res in limited:
            metadata = dict(res.metadata or {})
            metadata.setdefault("doc_id", metadata.get("doc_id") or res.source_id)
            metadata.setdefault("chunk_id", metadata.get("chunk_id") or res.source_id)
            documents.append(
                {
                    "content": res.content,
                    "score": float(res.score),
                    "source_id": res.source_id,
                    "doc_id": metadata.get("doc_id"),
                    "metadata": metadata,
                    "method": getattr(res.method, "value", "hybrid"),
                }
            )

        rag_response.documents = documents
        rag_response.retrieved_content = [doc["content"] for doc in documents]

        try:
            rag_response.citations = self._rag.citation_manager.create_citations(limited)
        except Exception as exc:  # pragma: no cover - citation fallback
            self._logger.warning("Citation generation failed: %s", exc)
            rag_response.citations = rag_response.citations or []

        rag_response.retrieval_stats = {
            "total_retrieved": len(results),
            "final_count": len(documents),
            "retrieval_method": "hybrid",
            "average_score": sum(doc["score"] for doc in documents) / len(documents)
            if documents
            else 0.0,
        }

    async def _run_multi_hop(
        self,
        main_elements: List[str],
        coverage: Dict[str, Any],
        chart_data: Dict[str, Any],
        request: RAGAnswerRequest,
    ) -> List[PlanStep]:
        """Expand retrieval with planner hops while respecting latency budgets."""
        max_budget_ms = min(request.constraints.max_latency_ms or 1500, 1500)
        spent_ms = 0
        hops: List[PlanStep] = []
        planner_steps = self._planner.plan(main_elements, coverage)
        for step in planner_steps:
            if spent_ms + step.cost_ms > max_budget_ms:
                step.metadata["skipped"] = True
                hops.append(step)
                continue
            docs = await self._execute_plan([step], chart_data)
            step.metadata["docs"] = docs
            spent_ms += step.cost_ms
            self._track_metric("multi_hop_spent", spent_ms)
            hops.append(step)
            if docs:
                break
        return hops

    def _map_mode(self, mode: str) -> OutputMode:
        """Translate pipeline mode strings into enumerated output modes."""
        mapping = {
            "natal": OutputMode.NATAL,
            "transit": OutputMode.TODAY,
            "technique": OutputMode.TIMING,
            "definition": OutputMode.NATAL,
            "synastry": OutputMode.NATAL,
            "mixed": OutputMode.TIMING,
        }
        return mapping.get(mode, OutputMode.NATAL)

    def _map_style(self, user_level: str) -> OutputStyle:
        """Map user skill level to the desired narrative style."""
        mapping = {
            "beginner": OutputStyle.ACCESSIBLE,
            "intermediate": OutputStyle.ACCESSIBLE,
            "advanced": OutputStyle.TECHNICAL,
        }
        return mapping.get(user_level, OutputStyle.ACCESSIBLE)

    def _guardrail_notes(
        self,
        payload: AnswerPayload,
        coverage: dict,
        evidence_pack: dict,
        alignment: Optional[dict] = None,
        degrade: Optional[DegradeDecision] = None,
        quality: Optional[AnswerQualityReport] = None,
        fallback_issues: Optional[List[str]] = None,
    ) -> List[str]:
        """Compile warnings or mitigations to surface alongside the answer."""
        notes: List[str] = []
        if not payload.citations:
            notes.append("No citations attached; coverage considered partial.")
        if payload.limits.hallucination_risk != "low":
            notes.append("Hallucination risk unknown; user guidance recommended.")
        if not coverage.get("pass", True):
            issues = coverage.get("issues", []) or ["Coverage threshold not met."]
            notes.extend(issues)
        if degrade and degrade.active:
            if degrade.reasons:
                notes.append("Degrade mode active: " + ", ".join(degrade.reasons))
            else:
                notes.append("Degrade mode active to protect latency budget.")
            latency_flag = degrade.flags.get("latency_p95_ms") if degrade.flags else None
            if latency_flag:
                notes.append(f"Observed rag_latency_p95={latency_flag} ms during degrade window.")
        if quality and not quality.passed:
            notes.append(
                "Quality filter flagged: " + ", ".join(quality.issues)
            )
        if fallback_issues:
            notes.append(
                "Template fallback served due to: " + ", ".join(fallback_issues)
            )
        alignment_score = getattr(payload.limits, "citation_alignment", None)
        if alignment_score is not None and alignment_score < 0.75:
            notes.append(
                f"Citation alignment below threshold (0.75); observed {alignment_score:.2f}."
            )
        supported_ratio = getattr(payload.limits, "claims_supported_ratio", None)
        if supported_ratio is not None and supported_ratio < 0.75:
            notes.append(
                f"Only {supported_ratio:.2f} of claims meet support threshold (≥0.60)."
            )
        if degrade and degrade.flags.get("citation_alignment_score") is not None:
            notes.append("Citation alignment breach detected; upgrade requested.")
        if alignment and alignment.get("reason"):
            reason = alignment["reason"]
            if reason == "no_citations":
                notes.append("Claim alignment skipped: no citations available.")
            elif reason == "no_documents":
                notes.append("Claim alignment skipped: no documents available.")
            elif reason == "no_claims":
                notes.append("Claim alignment skipped: no claims detected.")
        conflicts = evidence_pack.get("conflicts", [])
        for conflict in conflicts:
            notes.append(f"Conflict detected on topic '{conflict['topic']}': {conflict['summary']}")
        return notes

    async def _maybe_generate_llm_revision(
        self,
        payload: AnswerPayload,
        request: RAGAnswerRequest,
        coverage: dict,
        evidence_pack: dict,
        rag_response: Any,
        degrade_state: DegradeDecision,
    ) -> Optional[AnswerPayload]:
        """Route through the LLM orchestrator to revise the payload when allowed."""
        if not self._llm_orchestrator:
            return None
        try:
            self._last_routing_outcome = None
            context = PromptContext(
                language=request.locale_settings.language[:2],
                style=self._style_from_request(request),
                mode=request.mode_settings.mode,
                coverage=coverage,
                evidence_pack=evidence_pack,
            )
            messages = self._prompt_engineer.build_messages(
                payload.answer.general_profile,
                context,
            )
            outcome = await self._llm_orchestrator.generate_revision(
                request=request,
                messages=messages,
                coverage=coverage,
                rag_response=rag_response,
                evidence_pack=evidence_pack,
                degrade_state=degrade_state,
                max_tokens=request.constraints.max_tokens or 1200,
            )
            self._last_routing_outcome = outcome
            if not outcome or not outcome.repaired_payload:
                if outcome:
                    provider_tag = outcome.decision.provider or (
                        outcome.decision.model.default_provider or ""
                    )
                    observability.metrics.record_histogram(
                        "llm_router_confidence_metric",
                        outcome.decision.confidence_score,
                        tags={
                            "success": "0",
                            "provider": provider_tag,
                            "model": outcome.decision.model.key,
                        },
                    )
                    observability.metrics.record_histogram(
                        "llm_provider_latency",
                        outcome.latency_ms,
                        tags={"provider": provider_tag},
                    )
                    for provider_name, health in outcome.decision.health_snapshot.items():
                        observability.metrics.record_histogram(
                            "llm_provider_health_score",
                            health,
                            tags={"provider": provider_name},
                        )
                return None
            repaired = outcome.repaired_payload
            answer_data = repaired.get("answer", {})
            timing_windows = []
            for tw in answer_data.get("timing", []):
                try:
                    timing_windows.append(TimingWindow(**tw))
                except TypeError:
                    continue
            updated_payload = AnswerPayload(
                answer=AnswerBody(
                    general_profile=answer_data.get("general_profile", payload.answer.general_profile),
                    strengths=answer_data.get("strengths", payload.answer.strengths),
                    watchouts=answer_data.get("watchouts", payload.answer.watchouts),
                    timing=timing_windows or payload.answer.timing,
                    collective_note=answer_data.get("collective_note", payload.answer.collective_note),
                    mythic_refs=answer_data.get("mythic_refs", payload.answer.mythic_refs),
                ),
                citations=repaired.get("citations", payload.citations),
                confidence=float(repaired.get("confidence", payload.confidence)),
                limits={**payload.limits.model_dump(), **repaired.get("limits", {})},
                evidence_summary=payload.evidence_summary,
            )
            apply_answer_safeguards(updated_payload.answer)
            if outcome:
                provider_tag = outcome.decision.provider or (
                    outcome.decision.model.default_provider or ""
                )
                self._track_metric("llm_revision_latency", outcome.latency_ms)
                if outcome.validation_error:
                    self._logger.warning("LLM revision validation issue: %s", outcome.validation_error)
                success_flag = (
                    not outcome.validation_error
                    and bool(updated_payload.limits.coverage_ok)
                )
                observability.metrics.record_histogram(
                    "llm_router_confidence_metric",
                    outcome.decision.confidence_score,
                    tags={
                        "success": "1" if success_flag else "0",
                        "provider": provider_tag,
                        "model": outcome.decision.model.key,
                    },
                )
                observability.metrics.record_histogram(
                    "llm_provider_latency",
                    outcome.latency_ms,
                    tags={"provider": provider_tag},
                )
                for provider_name, health in outcome.decision.health_snapshot.items():
                    observability.metrics.record_histogram(
                        "llm_provider_health_score",
                        health,
                        tags={"provider": provider_name},
                    )
                cost_usd = self._extract_cost_usd(outcome)
                if cost_usd is not None:
                    observability.metrics.record_histogram(
                        "llm_cost_per_answer_usd",
                        cost_usd,
                    )
            return updated_payload
        except Exception as exc:
            self._logger.warning("LLM revision skipped: %s", exc)
            return None

    async def close(self) -> None:
        """Close any underlying provider pools that require cleanup."""
        if self._llm_pool:
            await self._llm_pool.close()

    def _style_from_request(self, request: RAGAnswerRequest) -> str:
        """Derive prompt tone from AB profile and locale preferences."""
        if request.ab_flags.profile == "cost-first":
            return "brief"
        if request.ab_flags.profile == "quality-first":
            return "detailed"
        if request.locale_settings.user_level == "advanced":
            return "technical"
        if request.locale_settings.user_level == "beginner":
            return "accessible"
        return "accessible"

    def _track_metric(self, name: str, value: float) -> None:
        """Record observability metrics defensively to avoid cascading failures."""
        try:
            observability.metrics.record_histogram(name, value)
        except Exception:
            pass

    def _extract_cost_usd(self, outcome: Optional[RoutingOutcome]) -> Optional[float]:
        """Pull provider cost information from routing outcomes when exposed."""
        if not outcome or not outcome.response:
            return None
        raw = outcome.response.raw or {}
        for key in ("cost_usd", "total_cost_usd", "cost"):
            if key in raw:
                try:
                    return float(raw[key])
                except (TypeError, ValueError):
                    continue
        usage = raw.get("usage")
        if isinstance(usage, dict):
            for key in ("cost_usd", "total_cost_usd", "cost", "total_cost"):
                if key in usage:
                    try:
                        return float(usage[key])
                    except (TypeError, ValueError):
                        continue
        return None

    def _build_cache(self) -> SemanticCache:
        """Create the semantic cache backend, falling back to in-memory storage."""
        try:
            return RedisSemanticCache(
                redis_url=settings.redis_url,
                ttl_seconds=getattr(settings, "SEMANTIC_CACHE_TTL", 604800),
            )
        except Exception:
            return SemanticCache()

    def _build_llm_pool(self) -> Optional[LLMProviderPool]:
        """Initialize provider pool with primary and optional fallback OpenAI entries."""
        api_key = getattr(settings, "OPENAI_API_KEY", None)
        default_model = getattr(settings, "OPENAI_MODEL_DEFAULT", None)
        fallback_model = getattr(settings, "OPENAI_MODEL_FALLBACK", None)
        if not api_key or not default_model:
            return None
        pool = LLMProviderPool()
        try:
            pool.register(
                ProviderEntry(
                    name="primary_openai",
                    provider=OpenAIProvider(api_key=api_key, model=default_model),
                    cooldown_seconds=90,
                )
            )
            if fallback_model and fallback_model != default_model:
                pool.register(
                    ProviderEntry(
                        name="fallback_openai",
                        provider=OpenAIProvider(api_key=api_key, model=fallback_model),
                        cooldown_seconds=180,
                    )
                )
            return pool
        except Exception as exc:
            self._logger.warning("LLM provider pool init failed: %s", exc)
            return None
