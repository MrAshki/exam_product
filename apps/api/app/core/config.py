from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Class-Centric AI Exam Platform API"
    API_VERSION: str = "0.1.0"
    APP_DEBUG: bool = False
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    COOKIE_NAME: str = "exam_access_token"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_PATH: str = "/"
    COOKIE_DOMAIN: str | None = Field(default=None)
    FRONTEND_BASE_URL: str = "http://localhost:3000"
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "exam_platform"
    POSTGRES_USER: str = "exam_platform"
    POSTGRES_PASSWORD: str = "exam_platform"
    DATABASE_URL: str | None = Field(default=None)

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str | None = Field(default=None)
    CELERY_BROKER_URL: str = "redis://localhost:16379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:16379/1"

    AI_PROVIDER: str = "mock"
    AI_MODEL: str = "gemini-2.0-flash"
    GEMINI_API_KEY: str | None = Field(default=None)
    AI_TIMEOUT_SECONDS: int = 30

    EMAIL_PROVIDER: str = "mock"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = ""
    SMTP_USE_TLS: bool = True

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @computed_field
    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field
    @property
    def redis_dsn(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def cookie_domain(self) -> str | None:
        if self.COOKIE_DOMAIN is None:
            return None
        domain = self.COOKIE_DOMAIN.strip()
        return domain or None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
