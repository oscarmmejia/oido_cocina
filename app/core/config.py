from functools import lru_cache

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Oido_cocina"
    api_prefix: str = "/api/v1"
    database_url: str  # obligatoria: sin valor por defecto


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError:
        raise SystemExit(
            "ERROR de configuración: falta la variable DATABASE_URL. "
            "Copia .env.example a .env y complétala."
        )