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
