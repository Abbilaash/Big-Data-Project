from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

PLACEHOLDER_JWT_SECRET = "change_this_to_a_long_random_secret"
PLACEHOLDER_NEO4J_PASSWORD = "change_me"


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"  # "development" | "production"

    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "campusconnect"

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = PLACEHOLDER_NEO4J_PASSWORD

    GOOGLE_CLIENT_ID: str = "your_google_client_id"
    GOOGLE_CLIENT_SECRET: str = "your_google_client_secret"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    JWT_SECRET_KEY: str = PLACEHOLDER_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # Next.js dev server runs on 3000. Comma-separated list is allowed for CORS;
    # the first entry is used for post-login redirects.
    FRONTEND_URL: str = "http://localhost:3000"
    ADMIN_EMAIL: str = "admin@example.com"

    # Development-only login that skips Google. Never honoured in production.
    ENABLE_DEV_LOGIN: bool = False

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def frontend_origins(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.FRONTEND_URL.split(",") if o.strip()]

    @property
    def primary_frontend_url(self) -> str:
        origins = self.frontend_origins
        return origins[0] if origins else "http://localhost:3000"

    @property
    def dev_login_enabled(self) -> bool:
        return self.ENABLE_DEV_LOGIN and not self.is_production

    def validate_for_runtime(self) -> list[str]:
        """Return fatal configuration problems (empty list means OK)."""
        problems: list[str] = []
        if self.is_production:
            if self.JWT_SECRET_KEY == PLACEHOLDER_JWT_SECRET or len(self.JWT_SECRET_KEY) < 32:
                problems.append("JWT_SECRET_KEY must be set to a random value of at least 32 characters")
            if self.NEO4J_PASSWORD == PLACEHOLDER_NEO4J_PASSWORD:
                problems.append("NEO4J_PASSWORD is still the placeholder value")
        return problems


@lru_cache()
def get_settings() -> Settings:
    return Settings()
