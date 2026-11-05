from functools import lru_cache

from pydantic import SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. Secrets and connection strings come from the environment (.env)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Oido_cocina"
    api_prefix: str = "/api/v1"

    # Mandatory, no default. Example: postgresql+psycopg://user:password@localhost:5432/oido_cocina
    database_url: str

    # Password given to the demo users created by the seeders. Never hardcoded in the repo.
    seed_demo_password: SecretStr | None = None

    # TEMPORAL: fake authentication for development. Removed with HU-AUT-04.
    auth_stubs_enabled: bool = True
    database_url: str  # TODO: obligatoria: sin valor por defecto
    auth_stubs_enabled: bool = True  # TODO: TEMPORAL: se elimina con HU-AUT-04


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as error:
        # Clear message instead of a pydantic traceback. Only field names, never values.
        fields = ", ".join(str(item["loc"][0]).upper() for item in error.errors())
        raise SystemExit(
            f"ERROR de configuración: falta o no es válida la variable {fields}. "
            "Copia .env.example a .env y complétala."
        ) from None
