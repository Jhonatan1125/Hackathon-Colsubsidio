from credit_engine.main import app


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"


class TestAppConfig:
    def test_app_has_correct_title(self):
        assert app.title == "Credit Recommendation Engine"

    def test_app_routes_are_registered(self):
        from fastapi.testclient import TestClient

        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200

        response = client.get("/api/v1/batches/nonexistent")
        assert response.status_code == 404

        response = client.post("/api/v1/batches/upload", files={})
        assert response.status_code == 422
