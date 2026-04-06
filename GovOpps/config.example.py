# config.example.py
# This is a safe-to-share template of config.py.
# It shows every setting the project uses, with placeholder values instead of real ones.
#
# HOW TO USE:
#   1. Copy .env.example to .env
#   2. Fill in your real API key and database password in .env
#   3. You do NOT need to touch config.py itself — it reads from .env automatically
#
# You should never need to edit config.py directly.
# All real values (passwords, API keys) go in .env — never in this file.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Tells Pydantic to read a file called ".env" in the current directory.
    # Any variable in .env automatically overrides the defaults below.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # SAM.gov API
    # Your personal API key from SAM.gov — set this in .env as SAM_API_KEY=...
    sam_api_key: str = "YOUR_API_KEY_HERE"

    # The SAM.gov endpoint we send requests to — no need to change this
    sam_api_base_url: str = "https://api.sam.gov/opportunities/v2/search"

    # How many contracts to fetch per API call (SAM.gov max is 1000)
    sam_fetch_limit: int = 1000

    # Optional: path to a local JSON file to use instead of calling the live API.
    # Useful for testing. Leave blank to always use the real API.
    local_json_path: str = ""

    # Optional: date range to fetch contracts for (format must be MM/dd/yyyy).
    # Leave both blank and the ETL will automatically use the last 7 days.
    sam_posted_from: str = ""
    sam_posted_to: str = ""

    # PostgreSQL Database
    # These must match your local PostgreSQL installation.
    # Override them in .env — e.g. add DB_PASSWORD=yourpassword to your .env file.
    db_host: str = "localhost"          # machine where PostgreSQL is running
    db_port: int = 5432                 # PostgreSQL default port — rarely needs changing
    db_name: str = "gov_contracts_dw"   # name of the database to connect to
    db_user: str = "postgres"           # PostgreSQL username
    db_password: str = ""               # PostgreSQL password — set this in .env!

    # API Server
    # Where the FastAPI server listens. Defaults are fine for local development.
    api_host: str = "0.0.0.0"  # accept connections from any network interface
    api_port: int = 8000        # visit http://localhost:8000/docs when running

    @property
    def database_url(self) -> str:
        # Builds the full PostgreSQL connection string that SQLAlchemy needs.
        # You never call this directly — SQLAlchemy uses it internally.
        # Format: postgresql+psycopg2://user:password@host:port/dbname
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


# One shared instance imported by every other file.
# Usage: from config import settings → then settings.sam_api_key, settings.db_host, etc.
settings = Settings()
