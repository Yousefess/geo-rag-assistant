from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    openrouter_api_key: str = ""
    max_pdf_pages: int = 0  # 0 means "no limit, process all pages"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
