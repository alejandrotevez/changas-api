import warnings

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./changas.db"

    # JWT
    JWT_SECRET: str = "dev-secret-not-for-prod"  # override via .env for production
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    # CORS — comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:8081,http://localhost:19006"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @model_validator(mode="after")
    def _validate_jwt_secret(self) -> "Settings":
        if self.JWT_SECRET in ("change-me-to-a-long-random-secret", "dev-secret-not-for-prod"):
            import warnings

            warnings.warn(
                "JWT_SECRET is using a dev-only default. Generate a strong secret for "
                "any non-local environment with:\n"
                "  python -c \"import secrets; print(secrets.token_urlsafe(64))\"",
                stacklevel=1,
            )
        return self


settings = Settings()
