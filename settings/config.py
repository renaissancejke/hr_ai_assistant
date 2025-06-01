from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_token: str = Field(..., env="TELEGRAM_TOKEN")
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    summary_chat_id: int = Field(..., env="SUMMARY_CHAT_ID")

    vacancies_file: str = "vacancies/vacancies.json"
    data_dir: str = "data/resumes"

    database_url: str | None = Field(None, env="DATABASE_URL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


setup = Settings()
