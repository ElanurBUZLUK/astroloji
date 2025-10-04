"""Utilities to execute retrieval/groundedness benchmarks against the RAG pipeline."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from app.pipelines.rag_pipeline import RAGAnswerPipeline
from app.schemas import EvaluationContext, RAGAnswerRequest


@dataclass
class BenchmarkCase:
    """Single benchmark scenario bundled with its evaluation config."""

    benchmark_id: str
    case_id: str
    name: str
    request: RAGAnswerRequest
    tags: List[str]


@dataclass
class BenchmarkResult:
    """Normalized output emitted after a benchmark run."""

    case_id: str
    name: str
    tags: List[str]
    metrics: dict


def load_benchmark_cases(path: str | Path) -> List[BenchmarkCase]:
    """Parse a benchmark definition file into executable cases."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    benchmark_id = payload["benchmark_id"]

    cases: List[BenchmarkCase] = []
    for case in payload.get("cases", []):
        request_payload = dict(case.get("request", {}))
        evaluation = EvaluationContext(
            benchmark_id=benchmark_id,
            case_id=case["case_id"],
            relevant_documents=case.get("relevant_documents", []),
            relevance_scores=case.get("relevance_scores", {}),
            expected_citations=case.get("expected_citations", []),
            at_k=case.get("at_k", 10),
            reference_answer=case.get("reference_answer"),
            tags=case.get("tags", []),
        )
        request = RAGAnswerRequest(evaluation=evaluation, **request_payload)
        cases.append(
            BenchmarkCase(
                benchmark_id=benchmark_id,
                case_id=case["case_id"],
                name=case.get("name", case["case_id"]),
                request=request,
                tags=case.get("tags", []),
            )
        )
    return cases


async def run_benchmark_cases(
    cases: Iterable[BenchmarkCase],
    pipeline: Optional[RAGAnswerPipeline] = None,
) -> List[BenchmarkResult]:
    """Execute benchmark requests and collect the emitted metrics."""
    owns_pipeline = pipeline is None
    pipeline = pipeline or RAGAnswerPipeline()

    results: List[BenchmarkResult] = []
    try:
        for case in cases:
            response = await pipeline.run(case.request)
            debug = getattr(response, "debug", None)
            metrics = getattr(debug, "evaluation_metrics", {}) if debug else {}
            results.append(
                BenchmarkResult(
                    case_id=case.case_id,
                    name=case.name,
                    tags=case.tags,
                    metrics=metrics,
                )
            )
    finally:
        if owns_pipeline:
            await pipeline.close()
    return results


__all__ = ["BenchmarkCase", "BenchmarkResult", "load_benchmark_cases", "run_benchmark_cases"]
