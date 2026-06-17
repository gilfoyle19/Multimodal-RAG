from fastapi.testclient import TestClient

from multimodal_rag.api.app import app


def test_health_endpoint_reports_service_status() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
