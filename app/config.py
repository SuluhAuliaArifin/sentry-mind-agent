"""Centralized config via pydantic-settings. Reads .env, no globals leaking."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite:///./data/agent.db"
    scan_interval_minutes: int = 15

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    solana_enabled: bool = False
    solana_rpc_url: str = "https://api.devnet.solana.com"
    solana_keypair_path: str = ""

    allowed_schemes: str = "http,https"
    http_timeout_seconds: int = 10

    @property
    def allowed_schemes_list(self) -> list[str]:
        return [s.strip().lower() for s in self.allowed_schemes.split(",") if s.strip()]


settings = Settings()
