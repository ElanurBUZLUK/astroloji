"""
Application configuration using Pydantic Settings
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # App settings
    DEBUG: bool = False
    SECRET_KEY: str = "astro-aa-super-secret-key-change-this-in-production-2025"
    ALLOWED_ORIGINS: str = "https://localhost,https://127.0.0.1"
    LOG_LEVEL: str = "INFO"
    
    # Database settings
    POSTGRES_URL: str = "postgresql://astro_user:astro_secure_pass_2025@postgres:5432/astro_aa"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_USER: str = "astro_user"
    POSTGRES_PASSWORD: str = "astro_secure_pass_2025"
    POSTGRES_DB: str = "astro_aa"
    REDIS_URL: str = "redis://redis:6379"
    QDRANT_URL: str = "http://localhost:6333"
    OPENSEARCH_URL: str = "http://localhost:9200"
    SEMANTIC_CACHE_TTL: int = 604800
    VECTOR_COLLECTION: str = "astro_semantic_tr_en"
    BM25_INDEX: str = "astro_lexical"
    
    # External APIs
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL_DEFAULT: str = "gpt-4o-mini"
    OPENAI_MODEL_FALLBACK: str = "gpt-3.5-turbo"
    
    # JWT settings
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    
    # Monitoring
    MONITORING_ENABLED: bool = True
    ALERT_EMAIL: str = "admin@astro-aa.com"
    
    # File paths
    LOG_DIR: str = "/app/logs"
    EPHEMERIS_DATA_PATH: Optional[str] = None  # Use built-in data
    
    # Security settings
    BCRYPT_ROUNDS: int = 12
    SESSION_TIMEOUT_HOURS: int = 24
    
    # Performance settings
    WORKER_PROCESSES: int = 4
    MAX_CONNECTIONS: int = 100
    CACHE_TTL_SECONDS: int = 3600
    
    # Feature flags
    ENABLE_SWAGGER_UI: bool = True
    ENABLE_METRICS_ENDPOINT: bool = True
    ENABLE_ADMIN_ENDPOINTS: bool = True
    RAG_DEGRADE_ENABLED: bool = True
    RAG_DEGRADE_LATENCY_THRESHOLD_MS: int = 2300
    RAG_DEGRADE_MIN_SAMPLES: int = 20
    RAG_DEGRADE_TOP_K: int = 5
    COST_GUARDRAIL_MAX_USD: float = 0.01
    COST_GUARDRAIL_CE_REDUCE_TO: int = 8
    COST_GUARDRAIL_SMALL_RATIO_DELTA: float = 0.2
    COST_GUARDRAIL_TTL_FACTOR: float = 1.5
    LLM_ROUTER_TIMEOUT_SMALL_MS: int = 1200
    LLM_ROUTER_TIMEOUT_MEDIUM_MS: int = 1600
    LLM_ROUTER_TIMEOUT_LARGE_MS: int = 2200
    LLM_ROUTER_CONF_LOW: float = 0.55
    LLM_ROUTER_CONF_HIGH: float = 0.75
    LLM_ROUTER_POLICY_KEYWORDS: str = "medical,financial,privacy,confidential,legal,therapy"
    LLM_ROUTER_LORA_ENABLED: bool = False
    LLM_ROUTER_SMALL_PROVIDER: str = "primary_openai"
    LLM_ROUTER_SMALL_MODEL: str = "gpt-4o-mini"
    LLM_ROUTER_MEDIUM_PROVIDER: str = "primary_openai"
    LLM_ROUTER_MEDIUM_MODEL: str = "gpt-4o-mini"
    LLM_ROUTER_LARGE_PROVIDER: str = "fallback_openai"
    LLM_ROUTER_LARGE_MODEL: str = "gpt-4o-mini"
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from environment variable"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.ALLOWED_ORIGINS
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.DEBUG and os.getenv("BUILD_TARGET") == "production"
    
    @property
    def database_url(self) -> str:
        """Get database URL with proper formatting"""
        return self.POSTGRES_URL
    
    @property
    def redis_url(self) -> str:
        """Get Redis URL with proper formatting"""
        return self.REDIS_URL
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Validate critical settings
if settings.SECRET_KEY == "your-secret-key-here":
    raise ValueError("SECRET_KEY must be changed from default value")

if settings.is_production and not settings.OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not set. AI features will be limited.")

# Log configuration summary
print(f"🔧 Configuration loaded:")
print(f"   - Debug mode: {settings.DEBUG}")
print(f"   - Production: {settings.is_production}")
print(f"   - Log level: {settings.LOG_LEVEL}")
print(f"   - CORS origins: {len(settings.cors_origins)} configured")
print(f"   - Rate limiting: {settings.RATE_LIMIT_ENABLED}")
print(f"   - Monitoring: {settings.MONITORING_ENABLED}")
