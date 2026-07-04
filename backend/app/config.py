"""Environment-driven settings for the public demo backend.

Secrets (ANTHROPIC_API_KEY) come only from the VPS-side environment file —
never committed, never sent to the frontend.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str = ""
    allowed_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    # Rate limits, expressed as slowapi-style strings ("N/minute").
    rate_limit_read: str = "20/minute"
    rate_limit_diagnose: str = "10/minute"
    rate_limit_narrate: str = "5/minute"

    # Bounds concurrent Anthropic calls so a traffic burst can't run up spend.
    narrate_concurrency: int = 2

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
