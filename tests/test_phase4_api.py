from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_ready_endpoint():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] in {"ready", "not_ready"}

def test_request_validation_rejects_bad_skin_type():
    response = client.post("/v1/recommend", json={"city":"Kanpur","skin_type":7,"body_area":25,"age":25})
    assert response.status_code == 422

def test_request_validation_rejects_extra_fields():
    response = client.post("/v1/recommend", json={"city":"Kanpur","skin_type":3,"body_area":25,"age":25,"unexpected":True})
    assert response.status_code == 422

def test_request_id_is_returned(monkeypatch):
    from api import main
    monkeypatch.setattr(main, "generate_recommendation", lambda payload: {"city":payload.city,"country":"India"})
    response = client.post("/v1/recommend", json={"city":"Kanpur","skin_type":3,"body_area":25,"age":25}, headers={"X-Request-ID":"test-123"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-123"
    assert response.json()["request_id"] == "test-123"
