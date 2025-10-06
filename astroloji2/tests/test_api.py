from fastapi.testclient import TestClient

from astroloji_ai.api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_horoscope_basic_request() -> None:
    payload = {
        "burc": "koç",
        "gun": "bugün",
        "birth": {
            "date": "1994-06-12",
            "time": "14:35",
            "tz": "Europe/Istanbul",
            "lat": 41.0,
            "lon": 29.0,
        },
        "user_id": "test-user",
        "goals": ["kariyer"],
    }
    response = client.post("/horoscope", json={**payload})
    assert response.status_code == 200
    data = response.json()
    assert data["burc"] == payload["burc"]
    assert data["gun"] == payload["gun"]
    assert isinstance(data["yorum"], str) and len(data["yorum"]) >= 100
    assert isinstance(data["pratik_tavsiyeler"], list) and data["pratik_tavsiyeler"]
