from fastapi.testclient import TestClient

from maintenance_preventive.api.main import app


def test_model_metrics_endpoint_returns_expected_sections():
    client = TestClient(app)
    response = client.get("/model/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert "metrics" in payload
    assert "confusion_matrix" in payload
    assert payload["metrics"]["train_cycles"] == 2000


def test_feature_importance_endpoint_returns_ranked_features():
    client = TestClient(app)
    response = client.get("/model/feature-importance?limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 5
    assert "feature" in payload[0]
    assert "importance" in payload[0]


def test_prometheus_endpoint_exposes_custom_metrics():
    client = TestClient(app)
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "maintenance_model_metric" in response.text
    assert "maintenance_api_http_requests_total" in response.text


def test_web_ui_route_serves_html():
    client = TestClient(app)
    response = client.get("/ui")

    assert response.status_code == 200
    assert "Maintenance Preventive MLOps | Interface Web" in response.text
    assert "Interface web d'analyse et de scoring" in response.text
