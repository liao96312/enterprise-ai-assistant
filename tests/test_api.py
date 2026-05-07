from pathlib import Path

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


client = TestClient(app)


def test_health_and_ready() -> None:
    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_calculator_chat() -> None:
    response = client.post(
        "/chat",
        json={"session_id": "test", "message": "1+2*3"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "7"
    assert payload["tool_used"] == "calculator"


def test_upload_rejects_unsupported_file() -> None:
    response = client.post(
        "/upload",
        files={"file": ("bad.exe", b"nope", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_model_settings_can_be_saved() -> None:
    response = client.post(
        "/settings",
        json={
            "model_provider": "deepseek",
            "api_key": "sk-test-key",
            "base_url": "",
            "chat_model": "deepseek-chat",
            "embedding_provider": "local",
            "embedding_base_url": "",
            "embedding_model": "",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["model_provider"] == "deepseek"
    assert payload["has_api_key"] is True
    assert payload["resolved_chat_model"] == "deepseek-chat"

    response = client.get("/knowledge/status")
    assert response.status_code == 200
    assert response.json()["model_provider"] == "deepseek"

    client.post(
        "/settings",
        json={
            "model_provider": "deepseek",
            "api_key": "",
            "base_url": "",
            "chat_model": "deepseek-chat",
            "embedding_provider": "local",
            "embedding_base_url": "",
            "embedding_model": "",
        },
    )


def test_upload_txt_and_ingest_local_vector_store() -> None:
    response = client.post(
        "/upload",
        files={
            "file": (
                "demo_policy.txt",
                "年假制度：满一年享有五天年假。".encode("utf-8"),
                "text/plain",
            )
        },
    )
    assert response.status_code == 200

    response = client.post(
        "/ingest", json={"path": str(settings.raw_data_dir), "reset": True}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["documents"] >= 1
    assert payload["chunks"] >= 1

    response = client.post(
        "/chat",
        json={"session_id": "test", "message": "年假制度怎么规定？"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tool_used"] == "policy_explain"
    assert "demo_policy.txt" in payload["sources"]

    uploaded = Path(settings.raw_data_dir) / "demo_policy.txt"
    if uploaded.exists():
        uploaded.unlink()


def test_auth_can_protect_admin_routes() -> None:
    original_enabled = settings.auth_enabled
    original_token = settings.admin_token
    object.__setattr__(settings, "auth_enabled", True)
    object.__setattr__(settings, "admin_token", "secret-token")
    try:
        assert client.get("/settings").status_code == 401
        response = client.get(
            "/settings", headers={"Authorization": "Bearer secret-token"}
        )
        assert response.status_code == 200
    finally:
        object.__setattr__(settings, "auth_enabled", original_enabled)
        object.__setattr__(settings, "admin_token", original_token)


def test_upload_size_limit() -> None:
    original_limit = settings.max_upload_mb
    object.__setattr__(settings, "max_upload_mb", 0)
    try:
        response = client.post(
            "/upload",
            files={"file": ("large.txt", b"x", "text/plain")},
        )
        assert response.status_code == 413
    finally:
        object.__setattr__(settings, "max_upload_mb", original_limit)
