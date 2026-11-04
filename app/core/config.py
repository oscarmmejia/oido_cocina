from functools import lru_cache

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Oido_cocina"
    api_prefix: str = "/api/v1"
    database_url: str  # obligatoria: sin valor por defecto
    auth_stubs_enabled: bool = True  # TEMPORAL: se elimina con HU-AUT-04


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError:
        raise SystemExit(
            "ERROR de configuración: falta la variable DATABASE_URL. "
            "Copia .env.example a .env y complétala."
        )from functools import lru_cache

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
