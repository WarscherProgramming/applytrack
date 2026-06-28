import json
from functools import lru_cache
from typing import Any, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_URL: str = "http://localhost:5173"

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS — stored as a JSON string in the env file, parsed below
    BACKEND_CORS_ORIGINS: list[str] = []

    # Google / Gmail integration.
    # When client id/secret are unset (or GMAIL_SIMULATION is true) the Gmail
    # feature runs in simulation mode: a fake client seeds realistic job emails
    # so the whole pipeline (connect → sync → match → timeline) works locally
    # without real Google credentials.
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/gmail/callback"
    GOOGLE_CALENDAR_REDIRECT_URI: str = (
        "http://localhost:8000/api/v1/calendar-integration/google/callback"
    )
    GMAIL_SIMULATION: bool = True

    # AI platform.
    # AI_PROVIDER selects the adapter behind the AIProvider abstraction
    # (see app.ai). "mock" returns deterministic canned output for local dev and
    # tests; "openai" calls the real API but only activates when OPENAI_API_KEY
    # is set — otherwise the platform transparently falls back to the mock so the
    # app always runs without external credentials. No provider-specific config
    # leaks into feature services; they consume app.ai's AIClient only.
    AI_PROVIDER: Literal["mock", "openai"] = "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4o-mini"
    # Number of *retries* for transient provider failures (attempts = retries+1).
    AI_MAX_RETRIES: int = 2
    AI_REQUEST_TIMEOUT: float = 30.0

    @property
    def ai_configured(self) -> bool:
        """True when real OpenAI credentials are present."""
        return bool(self.OPENAI_API_KEY)

    @property
    def ai_active_provider(self) -> str:
        """Resolved provider: 'openai' only when selected AND a key exists."""
        if self.AI_PROVIDER == "openai" and self.OPENAI_API_KEY:
            return "openai"
        return "mock"

    # File storage (resumes, cover letters).
    # STORAGE_BACKEND selects the implementation behind the FileStorage
    # abstraction (see app.shared.storage). "local" writes to STORAGE_LOCAL_PATH;
    # future values ("azure", "s3", "gdrive") plug in without touching business
    # logic. STORAGE_MAX_UPLOAD_BYTES caps a single upload (default 10 MB).
    STORAGE_BACKEND: Literal["local"] = "local"
    STORAGE_LOCAL_PATH: str = "storage"
    STORAGE_MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024

    @property
    def gmail_configured(self) -> bool:
        """True when real Google OAuth credentials are present."""
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)

    @property
    def gmail_simulation(self) -> bool:
        """Use the fake client unless explicitly disabled AND creds exist."""
        return self.GMAIL_SIMULATION or not self.gmail_configured

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @model_validator(mode="after")
    def validate_production_cors(self) -> "Settings":
        if self.is_production and "*" in self.BACKEND_CORS_ORIGINS:
            raise ValueError("BACKEND_CORS_ORIGINS must not contain '*' in production")
        return self

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
