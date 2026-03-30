# config.example.py
# Example configuration file. Copy this to config.py and fill in real values.
# This keeps secrets out of GitHub while preserving the expected module layout.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # SAM.gov API settings
    sam_api_key: str = "YOUR_API_KEY_HERE"
    sam_api_base_url: str = "https://api.sam.gov/opportunities/v2/search"
    sam_fetch_limit: int = 25

    # Date range for the query - leave blank to use last 7 days
    sam_posted_from: str = ""
    sam_posted_to: str = ""

    # PostgreSQL connection details
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "gov_contracts_dw"
    db_user: str = "postgres"
    db_password: str = "CHANGE_ME"

    # FastAPI server host/port
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
