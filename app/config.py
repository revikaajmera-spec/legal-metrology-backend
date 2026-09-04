from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Central place for all environment-configurable values.
    Override any of these by creating a `.env` file in the project root, e.g.:

        DATABASE_URL=sqlite:///./legal_metrology.db
        APP_NAME=Legal Metrology Compliance Platform

    For a real Postgres deployment later, just set:
        DATABASE_URL=postgresql://user:password@host:5432/dbname
    No code changes needed elsewhere.
    """

    app_name: str = "Legal Metrology Compliance Platform"
    api_v1_prefix: str = "/api/v1"

    # SQLite for the light prototype. File will be created automatically.
    database_url: str = "sqlite:///./legal_metrology.db"

    # Path to the rules-as-code file (Section 6 of the proposal)
    rules_file_path: str = "app/data/rules.yaml"

    class Config:
        env_file = ".env"


settings = Settings()