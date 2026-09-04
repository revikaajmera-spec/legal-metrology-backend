from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Legal Metrology Compliance Platform"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./legal_metrology.db"
    rules_file_path: str = "app/data/rules.yaml"

    # Your free OCR.space API key, read from the .env file (never hardcoded here)
    ocr_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()