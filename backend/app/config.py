"""Application configuration layer."""
from __future__ import annotations

from typing import ClassVar, Dict, List, Sequence

from pydantic import AnyHttpUrl, Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised configuration backed by environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Astro Birth Chart API"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Security
    SECRET_KEY: SecretStr = SecretStr(
        "astro-aa-super-secret-key-change-this-in-production-2025"
    )

    # Persistence & cache
    POSTGRES_URL: str = (
        "postgresql://astro_user:astro_secure_pass_2025@localhost:5432/astro_aa"
    )
    REDIS_URL: str = "redis://localhost:6379/0"
    SEMANTIC_CACHE_TTL: int = 604800
    CACHE_TTL_SECONDS: int = 3600
    SWISSEPH_DATA_PATH: str | None = None
    SEARCH_BACKEND: str = "QDRANT"
    BM25_LANGUAGE: str = "turkish"

    # Vector store
    QDRANT_URL: AnyHttpUrl = Field("http://localhost:6333")
    QDRANT_API_KEY: SecretStr | None = None
    QDRANT_COLLECTION: str = "astro_knowledge"
    OPENSEARCH_URL: AnyHttpUrl | None = Field("http://localhost:9200")
    OPENSEARCH_USER: str = "admin"
    OPENSEARCH_PASSWORD: SecretStr | None = SecretStr("admin")
    OPENSEARCH_INDEX: str = "astro_docs"
    HYBRID_ALPHA: float = 0.6

    # LLM provider
    OPENAI_API_KEY: SecretStr | None = None
    OPENAI_BASE_URL: AnyHttpUrl | None = None
    LLM_MODEL: str = "gpt-4o-mini"
    MAX_TOKENS: int = 300
    TEMPERATURE: float = 0.2
    MAX_COST_PER_REQUEST: float = 0.02
    REQUEST_TIMEOUT_SECONDS: float = 30.0
    USE_EMBEDDING_MODEL: bool = True
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    RERANKER_MODEL: str = "BAAI/bge-reranker-large"

    # Degrade policy defaults
    RAG_DEGRADE_ENABLED: bool = True
    RAG_DEGRADE_LATENCY_THRESHOLD_MS: int = 2300
    RAG_DEGRADE_MIN_SAMPLES: int = 20
    RAG_DEGRADE_TOP_K: int = 5
    COST_GUARDRAIL_MAX_USD: float = 0.02
    COST_GUARDRAIL_CE_REDUCE_TO: int = 8
    COST_GUARDRAIL_SMALL_RATIO_DELTA: float = 0.2
    COST_GUARDRAIL_TTL_FACTOR: float = 1.5

    # Router configuration
    LLM_ROUTER_CONF_LOW: float = 0.55
    LLM_ROUTER_CONF_HIGH: float = 0.75
    LLM_ROUTER_POLICY_KEYWORDS: str = (
        "medical,financial,privacy,confidential,legal,therapy"
    )
    LLM_ROUTER_LORA_ENABLED: bool = False
    LLM_ROUTER_SMALL_PROVIDER: str = "primary_openai"
    LLM_ROUTER_SMALL_MODEL: str = "gpt-4o-mini"
    LLM_ROUTER_MEDIUM_PROVIDER: str = "primary_openai"
    LLM_ROUTER_MEDIUM_MODEL: str = "gpt-4o-mini"
    LLM_ROUTER_LARGE_PROVIDER: str = "fallback_openai"
    LLM_ROUTER_LARGE_MODEL: str = "gpt-4o-mini"

    REQUIRED_ENV_VARS: ClassVar[Sequence[str]] = (
        "OPENAI_API_KEY",
        "QDRANT_URL",
        "QDRANT_COLLECTION",
    )

    @property
    def app_name(self) -> str:
        return self.APP_NAME

    @property
    def log_level(self) -> str:
        return self.LOG_LEVEL

    @property
    def debug(self) -> bool:  # type: ignore[override]
        return self.DEBUG

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def redis_url(self) -> str:
        return self.REDIS_URL

    def validate_environment(self) -> None:
        missing: List[str] = []
        for key in self.REQUIRED_ENV_VARS:
            value = getattr(self, key, None)
            if value is None:
                missing.append(key)
                continue
            if isinstance(value, SecretStr) and not value.get_secret_value():
                missing.append(key)
            elif isinstance(value, str) and not value:
                missing.append(key)

        if missing:
            formatted = ", ".join(sorted(missing))
            raise RuntimeError(
                f"Eksik ortam değişkenleri: {formatted}. `.env.example` dosyasından kopyalayarak `.env` oluşturun."
            )

    def describe(self) -> Dict[str, object]:
        summary: Dict[str, object] = {
            "app_name": self.APP_NAME,
            "debug": self.DEBUG,
            "log_level": self.LOG_LEVEL,
            "allowed_origins": self.cors_origins,
            "qdrant_url": str(self.QDRANT_URL),
            "qdrant_collection": self.QDRANT_COLLECTION,
            "openai_base_url": str(self.OPENAI_BASE_URL) if self.OPENAI_BASE_URL else None,
            "max_tokens": self.MAX_TOKENS,
            "temperature": self.TEMPERATURE,
            "request_timeout_seconds": self.REQUEST_TIMEOUT_SECONDS,
            "cache_ttl_seconds": self.CACHE_TTL_SECONDS,
            "swisseph_data_path": self.SWISSEPH_DATA_PATH,
            "embedding_model": self.EMBEDDING_MODEL,
            "use_embedding_model": self.USE_EMBEDDING_MODEL,
            "reranker_model": self.RERANKER_MODEL,
            "search_backend": self.SEARCH_BACKEND,
            "bm25_language": self.BM25_LANGUAGE,
            "opensearch_url": str(self.OPENSEARCH_URL) if self.OPENSEARCH_URL else None,
            "opensearch_index": self.OPENSEARCH_INDEX,
            "hybrid_alpha": self.HYBRID_ALPHA,
        }
        summary["openai_api_key"] = (
            "***redacted***"
            if self.OPENAI_API_KEY and self.OPENAI_API_KEY.get_secret_value()
            else None
        )
        summary["qdrant_api_key"] = (
            "***redacted***"
            if self.QDRANT_API_KEY and self.QDRANT_API_KEY.get_secret_value()
            else None
        )
        summary["opensearch_password"] = (
            "***redacted***"
            if self.OPENSEARCH_PASSWORD and self.OPENSEARCH_PASSWORD.get_secret_value()
            else None
        )
        return summary


def load_settings() -> Settings:
    try:
        loaded = Settings()
    except ValidationError as exc:  # pragma: no cover - surfaces configuration errors
        raise RuntimeError(str(exc)) from exc

    loaded.validate_environment()
    return loaded


settings = load_settings()


__all__ = ["settings", "Settings", "load_settings"]
