from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Core Database & Application Configuration
    DATABASE_URL: str = "sqlite:///./metadata.db"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # LLM & Embedding Model Settings
    GROQ_API_KEY: str = ""
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # Redis Session Memory Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Vector Storage Settings (Fallback settings if utilizing remote Qdrant)
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()