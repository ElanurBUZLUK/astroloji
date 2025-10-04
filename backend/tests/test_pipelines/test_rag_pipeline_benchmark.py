"""Tests for benchmark instrumentation in the RAG answer pipeline."""
import pytest

from app.pipelines.cache import SemanticCache
from app.pipelines.chart_builder import ChartBuildResult
from app.pipelines.mock_data import sample_chart
from app.pipelines.rag_pipeline import RAGAnswerPipeline
from app.schemas import (
    BirthData,
    ChartContext,
    EvaluationContext,
    LocaleSettings,
    ModeSettings,
    RAGAnswerRequest,
)


class _StubChartBootstrapper:
    async def load(self, birth_data):
        return ChartBuildResult(chart_data=sample_chart(), context=ChartContext())


@pytest.mark.asyncio
async def test_pipeline_emits_benchmark_metrics():
    """Benchmark metadata should trigger retrieval/groundedness metrics."""
    pipeline = RAGAnswerPipeline(semantic_cache=SemanticCache(), chart_bootstrapper=_StubChartBootstrapper())

    request = RAGAnswerRequest(
        query="Explain the Almuten Figuris and why it leads chart synthesis",
        birth_data=BirthData(
            date="1990-06-15",
            time="14:30",
            tz="Europe/Istanbul",
            lat=41.015137,
            lng=28.97953,
        ),
        locale_settings=LocaleSettings(locale="en-US", user_level="intermediate"),
        mode_settings=ModeSettings(mode="definition"),
        evaluation=EvaluationContext(
            benchmark_id="unit_test",
            case_id="almuten_case",
            relevant_documents=["almuten_001", "dignity_001"],
            expected_citations=["almuten_001"],
            at_k=5,
        ),
    )

    response = await pipeline.run(request)
    metrics = response.debug.evaluation_metrics

    assert metrics["at_k"] == 5
    assert "recall_at_k" in metrics
    assert "precision_at_k" in metrics
    assert "groundedness" in metrics
    assert metrics["recall_at_k"] >= 0.0

    await pipeline.close()
