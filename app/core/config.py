from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. Secrets and connection strings come from the environment (.env)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Example: postgresql+psycopg://user:password@localhost:5432/oido_cocina
    database_url: str

    # Password given to the demo users created by the seeders. Never hardcoded in the repo.
    seed_demo_password: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
