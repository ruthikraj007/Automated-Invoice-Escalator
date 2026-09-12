import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Automated Invoice & Payment Escalator"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS origins
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [v]
        return v

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = "whsec_test_secret_12345"

    # Resend
    RESEND_API_KEY: str = ""
    DEFAULT_SENDER_EMAIL: str = "billing@example.com"

    # Escalation Cadence & Scheduler
    ESCALATION_CHECK_HOURS: int = 24
    ENABLE_SCHEDULER: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
