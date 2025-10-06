"""Go/No-Go acceptance-style checks for the AI RAG module."""
from __future__ import annotations

import os
from typing import Any, Dict, List
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.pipelines.quality_control import AnswerQualityReport


client = TestClient(app)
API_HEADERS = {"X-API-Key": "dev-astro-key"}


def _base_payload() -> Dict[str, Any]:
    return {
        "query": "Koç burcu için bugünün astrolojik enerjileri ve dikkat edilmesi gereken konular nelerdir?",
        "locale_settings": {"locale": "tr-TR", "language": "tr", "user_level": "beginner"},
        "mode_settings": {"mode": "natal"},
        "constraints": {"max_tokens": 400, "max_latency_ms": 2500},
    }


def _post(payload: Dict[str, Any]) -> Dict[str, Any]:
    response = client.post("/v1/rag/answer", json=payload, headers=API_HEADERS)
    assert response.status_code == 200, response.text
    return response.json()


def test_go_no_go_primary_flow_returns_expected_shape() -> None:
    """E2E smoke: base request should populate the main response fields."""
    data = _post(_base_payload())

    assert data["request"]["query"]
    assert "payload" in data
    payload = data["payload"]
    assert payload["answer"]["general_profile"]
    assert isinstance(payload["citations"], list)
    assert payload["limits"]["coverage_score"] is not None
    assert data.get("documents") is not None
    assert "guardrail_notes" in data.get("debug", {})


def test_go_no_go_quality_fallback_path_records_guardrail_note() -> None:
    """Force the quality filter to fail once, ensuring template fallback and guardrail note."""
    forced_fail = AnswerQualityReport(passed=False, issues=["forced_quality_failure"])
    forced_pass = AnswerQualityReport(passed=True, issues=[])

    with patch(
        "app.pipelines.quality_control.AnswerQualityFilter.evaluate",
        side_effect=[forced_fail, forced_pass],
    ):
        data = _post(_base_payload())

    guardrail_notes: List[str] = data["debug"].get("guardrail_notes", [])
    fallback_notes = [note for note in guardrail_notes if "fallback" in note.lower()]
    assert fallback_notes, f"Expected fallback note, got {guardrail_notes}"

    # Ensure metrics endpoint reflects the forced fallback reason.
    metrics = client.get("/metrics").text
    assert "astro_rag_quality_fallback_total" in metrics
    assert "forced_quality_failure" in metrics


def test_go_no_go_metrics_endpoint_includes_router_and_latency_histograms() -> None:
    """Metrics endpoint should expose key gauges/histograms after traffic."""
    # warm-up two requests to generate metrics entries
    _post(_base_payload())
    _post(_base_payload())

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    body = metrics.text
    assert "astro_api_requests_total" in body
    assert "astro_rag_pipeline_latency_seconds" in body
    assert "astro_rag_quality_issue_total" in body


def test_go_no_go_respects_custom_vector_store_path(tmp_path) -> None:
    """Point vector store to empty directory and ensure the pipeline still succeeds."""
    custom_store = tmp_path / "vector_store"
    os.environ["CHROMA_PERSIST_PATH"] = str(custom_store)
    try:
        data = _post(_base_payload())
    finally:
        os.environ.pop("CHROMA_PERSIST_PATH", None)

    assert data["payload"]["answer"]["general_profile"]
    guardrail_notes: List[str] = data["debug"].get("guardrail_notes", [])
    # Expect either normal flow or fallback; most important is successful response.
    assert isinstance(guardrail_notes, list)

