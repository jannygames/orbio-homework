from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/product_assistant"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    max_message_length: int = 2000
    max_tool_iterations: int = 5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
