"""Configuración de la base de datos de pruebas.

El orden de este módulo importa: la URL se resuelve y se exporta ANTES de importar
`app.core.database_connection`, que crea el engine al importarse.
"""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not DATABASE_URL:
    pytest.exit(
        "Falta TEST_DATABASE_URL. Estas pruebas hacen TRUNCATE antes de cada test, "
        "así que no aceptan DATABASE_URL: define TEST_DATABASE_URL apuntando a una "
        "base desechable.",
        returncode=1,
    )
os.environ["DATABASE_URL"] = DATABASE_URL

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.database_connection import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.shared.models.restaurant import DEMO_RESTAURANT_NAME, Restaurant  # noqa: E402
from app.modules.tables.models.table import DiningTable  # noqa: E402,F401  (registra la tabla)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_database():
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE tables, restaurant RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def restaurant(db):
    """Restaurante sembrado por el bootstrap: el destino por defecto de las mesas."""
    demo = Restaurant(name=DEMO_RESTAURANT_NAME)
    db.add(demo)
    db.commit()
    db.refresh(demo)
    return demo
