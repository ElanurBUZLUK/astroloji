from pydantic import BaseSettings

class Settings(BaseSettings):
    log_level: str = "INFO"
    ephemeris: str = "path/to/ephemeris/data"
    quality: dict = {
        "min_chars": 50,
        "min_sentences": 3,
        "required_keywords": ["astroloji", "burç", "yıldız"]
    }
    llm: dict = {
        "complex_model": "complex_model_name",
        "routine_model": "routine_model_name"
    }
    rag: dict = {
        "persist_dir": "path/to/rag/persist"
    }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"