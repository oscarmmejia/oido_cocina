import os
import secrets
from pathlib import Path

import pytest
from dotenv import load_dotenv
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not DATABASE_URL:
    pytest.exit("TEST_DATABASE_URL must point to a disposable test database.", returncode=1)
test_url = make_url(DATABASE_URL)
if (
    test_url.get_backend_name() != "postgresql"
    or test_url.database != "oido_cocina_test"
    or test_url.host not in ("localhost", "127.0.0.1", "::1")
):
    pytest.exit("Only the local oido_cocina_test database is allowed.", returncode=1)
os.environ["DATABASE_URL"] = DATABASE_URL
os.environ.setdefault("SECRET_KEY", secrets.token_urlsafe(48))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

import app.models
from app.core.database_connection import Base, get_db
from app.core.kernel.identity import CurrentUser, get_current_user
from app.core.permissions import PERMISSION_NAMES, ROLE_SUPERADMIN
from app.main import app
from app.models import Restaurant

TEST_RESTAURANT_ID = 1
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
        connection.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))
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

    def domain_user():
        return CurrentUser(
            id=1,
            restaurant_id=TEST_RESTAURANT_ID,
            email="domain@example.com",
            role=ROLE_SUPERADMIN,
            permissions=set(PERMISSION_NAMES),
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = domain_user
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def restaurant(db):
    demo = Restaurant(
        id=TEST_RESTAURANT_ID,
        name="Test restaurant",
        time_zone="Europe/Madrid",
    )
    db.add(demo)
    db.commit()
    db.refresh(demo)
    return demo
