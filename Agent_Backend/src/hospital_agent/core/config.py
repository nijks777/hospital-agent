from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Bootstrap settings read from environment variables / .env.

    Only what the app needs to *start* lives here. Runtime choices (LLM model,
    voice provider, prompts) will be stored in the database and edited from the
    admin panel.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Hospital Agent"
    environment: str = "local"
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: str
    db_echo: bool = False
    jwt_secret_key: str
    jwt_expire_minutes: int = 60 * 8  # one working day
    auth_cookie_name: str = "access_token"

    # Email: "console" prints to the server log (dev); "smtp" really sends (Gmail app password).
    email_backend: Literal["console", "smtp"] = "console"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_from: str = "Hospital Agent <no-reply@localhost>"

    verification_code_ttl_minutes: int = 10
    verification_max_attempts: int = 5
    verification_resend_cooldown_seconds: int = 60

    @property
    def is_local(self) -> bool:
        return self.environment == "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue] — fields come from env
