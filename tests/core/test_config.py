import pytest

from app.core.config import get_settings


def test_missing_database_url_exits_with_a_clear_message(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # a folder without .env
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()

    with pytest.raises(SystemExit) as error:
        get_settings()

    assert "DATABASE_URL" in str(error.value)
    assert ".env.example" in str(error.value)
    get_settings.cache_clear()


def test_auth_stubs_are_disabled_by_default(monkeypatch, tmp_path):
    """Fake authentication must be opt-in: a forgotten variable must not open the API."""
    monkeypatch.chdir(tmp_path)  # a folder without .env
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+psycopg://user:password@localhost:5432/oido_cocina"
    )
    monkeypatch.delenv("AUTH_STUBS_ENABLED", raising=False)
    get_settings.cache_clear()

    try:
        assert get_settings().auth_stubs_enabled is False
    finally:
        get_settings.cache_clear()
