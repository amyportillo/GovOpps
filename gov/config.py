# config.py
# This file manages all the settings for the project.
# Instead of hardcoding values like passwords or API keys directly in your code,
# we read them from a .env file. That way you never accidentally share secrets.
# pydantic-settings does all the reading automatically when Settings() is created.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Tell pydantic-settings to look for a file called .env in the project folder
    # and read variables from it. If a variable is also set in your real environment
    # (like a system env var), that takes priority over the .env file.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Your SAM.gov API key - get one free at https://sam.gov
    sam_api_key: str = "YOUR_API_KEY_HERE"

    # The SAM.gov endpoint we send requests to
    sam_api_base_url: str = "https://api.sam.gov/opportunities/v2/search"

    # How many results to ask for per API call (keeping it small during development)
    sam_fetch_limit: int = 25

    # Date range for the query - if you leave these blank in .env the ETL script
    # automatically uses the last 7 days instead
    sam_posted_from: str = ""
    sam_posted_to: str = ""

    # PostgreSQL connection details - these must match your existing database
    # If you already ran the C# project just point these at the same database,
    # the tables are identical so Python will connect and everything will work
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "gov_contracts_dw"
    db_user: str = "postgres"
    db_password: str = "094825"

    # Host and port the FastAPI server will listen on when you run uvicorn
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @property
    def database_url(self) -> str:
        # Builds the full connection string SQLAlchemy needs to talk to PostgreSQL
        # Format: postgresql+psycopg2://user:password@host:port/database_name
        # psycopg2 is the driver that actually handles the low-level connection
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


# Create one shared instance here so every other file can just do:
#   from config import settings
# and get the same object without re-reading the .env file multiple times
settings = Settings()