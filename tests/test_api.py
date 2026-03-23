from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "platform" in response.json()
    assert "disclaimer" in response.json()

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_explain_stub_returns_200():
    response = client.post("/api/explain/", json={
        "paragraph_ref": "SW-14.1",
        "question": "What does this mean?"
    })
    assert response.status_code == 200
    assert "explanation" in response.json()
    assert "disclaimer" in response.json()

def test_session_not_found_returns_404():
    response = client.get(
        "/api/session/00000000-0000-0000-0000-000000000000/status"
    )
    assert response.status_code == 404

def test_result_not_found_returns_404():
    response = client.get(
        "/api/questions/result/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404
