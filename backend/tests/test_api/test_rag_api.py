from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rag_answer_smoke():
    payload = {
        "query": "Bu yıl ilişki teması neden artıyor?",
        "locale_settings": {"locale": "tr-TR", "user_level": "beginner"},
        "mode_settings": {"mode": "natal"},
    }

    response = client.post(
        "/v1/rag/answer",
        json=payload,
        headers={"X-API-Key": "dev-astro-key"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["payload"]["answer"]["general_profile"]
    assert "citations" in data["payload"]
    assert "coverage_score" in data["payload"]["limits"]
    assert "coverage" in data.get("debug", {})
    assert "evidence_pack" in data
    assert "plan" in data.get("debug", {})
