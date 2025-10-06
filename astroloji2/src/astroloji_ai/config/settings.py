from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, BaseSettings, Field


class LLMConfig(BaseModel):
    routine_model: str = Field(default="gpt-4o-mini")
    complex_model: str = Field(default="gpt-4o-mini")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=700)


class RagConfig(BaseModel):
    persist_dir: str = Field(default="./data/processed/vector_store")
    retriever_type: Literal["mmr"] = Field(default="mmr")
    k: int = Field(default=5)
    fetch_k: int = Field(default=10)
    embed_model: str = Field(default="text-embedding-3-small")


class EphemerisConfig(BaseModel):
    orb_deg: float = Field(default=6.0)
    ttl_minutes: int = Field(default=60)


class QualityConfig(BaseModel):
    min_chars: int = Field(default=100)
    min_sentences: int = Field(default=3)
    required_keywords: tuple[str, ...] = Field(
        default=("tavsiye", "öneri", "dikkat", "fırsat")
    )


class SecurityConfig(BaseModel):
    sanitize_html: bool = Field(default=True)


class I18NConfig(BaseModel):
    lang: str = Field(default="tr")


class Settings(BaseSettings):
    llm: LLMConfig = LLMConfig()
    rag: RagConfig = RagConfig()
    ephemeris: EphemerisConfig = EphemerisConfig()
    quality: QualityConfig = QualityConfig()
    security: SecurityConfig = SecurityConfig()
    i18n: I18NConfig = I18NConfig()
    log_level: str = Field(default="INFO")
    api_rate_limit_per_minute: int = Field(default=10, env="API_RATE_LIMIT_PER_MINUTE")
    openai_api_key: str | None = Field(default=None, env="OPENAI_API_KEY")

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()  # type: ignore[arg-type]
