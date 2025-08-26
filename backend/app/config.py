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
    REDIS_URL: str = "redis://redis:6379"
    
    # External APIs
    OPENAI_API_KEY: Optional[str] = None
    
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