from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config import settings
from app.providers import PROVIDER_PRESETS


def _env_path() -> Path:
    return Path.cwd() / ".env"


def _read_env() -> dict[str, str]:
    path = _env_path()
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _write_env(updates: dict[str, str]) -> None:
    existing = _read_env()
    existing.update(updates)
    lines = [
        "APP_NAME=Enterprise AI Assistant",
        "APP_ENV=development",
        "",
        f"MODEL_PROVIDER={existing.get('MODEL_PROVIDER', settings.model_provider)}",
        f"API_KEY={existing.get('API_KEY', '')}",
        f"BASE_URL={existing.get('BASE_URL', '')}",
        f"CHAT_MODEL={existing.get('CHAT_MODEL', '')}",
        "",
        f"EMBEDDING_PROVIDER={existing.get('EMBEDDING_PROVIDER', settings.embedding_provider)}",
        f"EMBEDDING_API_KEY={existing.get('EMBEDDING_API_KEY', '')}",
        f"EMBEDDING_BASE_URL={existing.get('EMBEDDING_BASE_URL', '')}",
        f"EMBEDDING_MODEL={existing.get('EMBEDDING_MODEL', '')}",
        "",
        f"RAW_DATA_DIR={existing.get('RAW_DATA_DIR', './data/raw')}",
        f"CHROMA_DIR={existing.get('CHROMA_DIR', './data/chroma')}",
        f"CHROMA_COLLECTION_NAME={existing.get('CHROMA_COLLECTION_NAME', 'enterprise_knowledge')}",
        f"TOP_K={existing.get('TOP_K', '4')}",
        f"CHUNK_SIZE={existing.get('CHUNK_SIZE', '500')}",
        f"CHUNK_OVERLAP={existing.get('CHUNK_OVERLAP', '50')}",
        f"LOCAL_EMBEDDING_DIMENSIONS={existing.get('LOCAL_EMBEDDING_DIMENSIONS', '384')}",
    ]
    _env_path().write_text("\n".join(lines) + "\n", encoding="utf-8")


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def provider_options() -> list[dict[str, str]]:
    return [
        {
            "name": name,
            "base_url": preset.base_url,
            "chat_model": preset.chat_model,
            "embedding_base_url": preset.embedding_base_url,
            "embedding_model": preset.embedding_model,
        }
        for name, preset in PROVIDER_PRESETS.items()
    ]


def current_settings() -> dict[str, Any]:
    return {
        "model_provider": settings.provider_name,
        "api_key_masked": _mask(settings.api_key),
        "has_api_key": bool(settings.api_key),
        "base_url": settings.base_url,
        "resolved_base_url": settings.resolved_base_url,
        "chat_model": settings.chat_model,
        "resolved_chat_model": settings.resolved_chat_model,
        "embedding_provider": settings.embedding_provider,
        "embedding_api_key_masked": _mask(settings.embedding_api_key),
        "has_embedding_api_key": bool(settings.embedding_api_key),
        "embedding_base_url": settings.embedding_base_url,
        "resolved_embedding_base_url": settings.resolved_embedding_base_url,
        "embedding_model": settings.embedding_model,
        "resolved_embedding_model": settings.resolved_embedding_model,
        "providers": provider_options(),
    }


def update_runtime_settings(payload: dict[str, str]) -> dict[str, Any]:
    provider = payload.get("model_provider", settings.model_provider).strip()
    if provider not in PROVIDER_PRESETS:
        supported = ", ".join(sorted(PROVIDER_PRESETS))
        raise RuntimeError(f"不支持的模型提供商：{provider}。可选：{supported}")

    updates: dict[str, str] = {
        "MODEL_PROVIDER": provider,
        "BASE_URL": payload.get("base_url", settings.base_url).strip(),
        "CHAT_MODEL": payload.get("chat_model", settings.chat_model).strip(),
        "EMBEDDING_PROVIDER": payload.get(
            "embedding_provider", settings.embedding_provider
        ).strip(),
        "EMBEDDING_BASE_URL": payload.get(
            "embedding_base_url", settings.embedding_base_url
        ).strip(),
        "EMBEDDING_MODEL": payload.get("embedding_model", settings.embedding_model).strip(),
    }
    if "api_key" in payload:
        updates["API_KEY"] = payload["api_key"].strip()
    if "embedding_api_key" in payload:
        updates["EMBEDDING_API_KEY"] = payload["embedding_api_key"].strip()

    _write_env(updates)

    object.__setattr__(settings, "model_provider", updates["MODEL_PROVIDER"])
    object.__setattr__(settings, "base_url", updates["BASE_URL"])
    object.__setattr__(settings, "chat_model", updates["CHAT_MODEL"])
    object.__setattr__(settings, "embedding_provider", updates["EMBEDDING_PROVIDER"])
    object.__setattr__(settings, "embedding_base_url", updates["EMBEDDING_BASE_URL"])
    object.__setattr__(settings, "embedding_model", updates["EMBEDDING_MODEL"])
    if "API_KEY" in updates:
        object.__setattr__(settings, "api_key", updates["API_KEY"])
    if "EMBEDDING_API_KEY" in updates:
        object.__setattr__(settings, "embedding_api_key", updates["EMBEDDING_API_KEY"])

    return current_settings()
