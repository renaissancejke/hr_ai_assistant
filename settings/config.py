from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_token: str = Field(..., env="TELEGRAM_TOKEN")
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    summary_chat_id: int = Field(..., env="SUMMARY_CHAT_ID")

    vacancies_file: str = "vacancies/vacancies.json"
    data_dir: Path = Path("data") / "resumes"
    database_url: str | None = Field(None, env="DATABASE_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __init__(self, **values):
        # создаём data/resumes при запуске (если её нет)
        super().__init__(**values)
        self.data_dir.mkdir(parents=True, exist_ok=True)


setup = Settings()
