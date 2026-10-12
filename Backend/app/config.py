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

    JWT_SECRET_KEY: str = PLACEHOLDER_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # Next.js dev server runs on 3000. Comma-separated list is allowed for CORS
    FRONTEND_URL: str = "http://localhost:3000"
    ADMIN_EMAIL: str = "admin@example.com"


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
        origins = [o.strip().rstrip("/") for o in self.FRONTEND_URL.split(",") if o.strip()]
        if not self.is_production:
            dev_defaults = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]
            for d in dev_defaults:
                if d not in origins:
                    origins.append(d)
        return origins

    @property
    def primary_frontend_url(self) -> str:
        origins = self.frontend_origins
        return origins[0] if origins else "http://localhost:3000"

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
