from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

from app.providers import provider_preset


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Enterprise AI Assistant")
    app_env: str = os.getenv("APP_ENV", "development")

    model_provider: str = os.getenv("MODEL_PROVIDER", "deepseek")
    api_key: str = os.getenv("API_KEY", os.getenv("OPENAI_API_KEY", ""))
    base_url: str = os.getenv("BASE_URL", os.getenv("OPENAI_BASE_URL", ""))
    chat_model: str = os.getenv("CHAT_MODEL", os.getenv("OPENAI_MODEL", ""))

    embedding_api_key: str = os.getenv("EMBEDDING_API_KEY", "")
    embedding_base_url: str = os.getenv("EMBEDDING_BASE_URL", "")
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL", os.getenv("OPENAI_EMBEDDING_MODEL", "")
    )
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "auto")
    raw_data_dir: Path = Path(os.getenv("RAW_DATA_DIR", "./data/raw"))
    chroma_dir: Path = Path(os.getenv("CHROMA_DIR", "./data/chroma"))
    chroma_collection_name: str = os.getenv(
        "CHROMA_COLLECTION_NAME", "enterprise_knowledge"
    )
    top_k: int = int(os.getenv("TOP_K", "4"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    local_embedding_dimensions: int = int(os.getenv("LOCAL_EMBEDDING_DIMENSIONS", "384"))
    auth_enabled: bool = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    admin_token: str = os.getenv("ADMIN_TOKEN", "")
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "20"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def provider_name(self) -> str:
        return self.model_provider.lower().strip()

    @property
    def provider(self):
        return provider_preset(self.provider_name)

    @property
    def resolved_base_url(self) -> str:
        return self.base_url or self.provider.base_url

    @property
    def resolved_chat_model(self) -> str:
        return self.chat_model or self.provider.chat_model

    @property
    def resolved_embedding_api_key(self) -> str:
        return self.embedding_api_key or self.api_key

    @property
    def resolved_embedding_base_url(self) -> str:
        return self.embedding_base_url or self.provider.embedding_base_url or self.resolved_base_url

    @property
    def resolved_embedding_model(self) -> str:
        return self.embedding_model or self.provider.embedding_model or "text-embedding-3-small"

    @property
    def has_api_embedding_config(self) -> bool:
        return bool(
            self.resolved_embedding_api_key
            and (self.embedding_model or self.provider.embedding_model)
        )

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
