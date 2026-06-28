# app/core/settings.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    LLM_MODEL: str = "gemma3:4b"
    LLM_PROVIDER: str = "ollama"


settings = Settings()
