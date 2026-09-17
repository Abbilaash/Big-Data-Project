from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os
from pathlib import Path


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "campusconnect"

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "change_me"

    GOOGLE_CLIENT_ID: str = "your_google_client_id"
    GOOGLE_CLIENT_SECRET: str = "your_google_client_secret"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    JWT_SECRET_KEY: str = "change_this_to_a_long_random_secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    FRONTEND_URL: str = "http://localhost:5173"
    ADMIN_EMAIL: str = "admin@example.com"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
