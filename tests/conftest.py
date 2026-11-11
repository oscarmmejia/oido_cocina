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
from sqlalchemy import create_engine, inspect, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import app.models  # noqa: E402,F401
from app.core.database_connection import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Restaurant  # noqa: E402
from app.core.kernel.seed import seed_minimum_data  # noqa: E402

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

with engine.begin() as connection:
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_database():
    existing = set(inspect(engine).get_table_names())
    table_names = ", ".join(
        f'"{table.name}"'
        for table in Base.metadata.sorted_tables
        if table.name in existing
    )
    with engine.begin() as connection:
        connection.execute(
            text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE")
        )
    
    # Rellenamos con los datos mínimos (seeders) en cada limpieza de test
    session = TestingSessionLocal()
    try:
        seed_minimum_data(session)
        session.commit()
    finally:
        session.close()
    
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
        # Autenticación automática del admin para evitar los 401
        response = test_client.post(
            "/api/v1/auth/login",
            data={"username": "admin@oidocina.local", "password": "Demo1234!"}
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            test_client.headers = {"Authorization": f"Bearer {token}"}
            
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def restaurant(db):
    demo = db.get(Restaurant, 1)
    if not demo:
        demo = Restaurant(
            id=1,
            name="Demo",
            time_zone="Europe/Madrid",
        )
        db.add(demo)
        db.commit()
        db.refresh(demo)
    return demo