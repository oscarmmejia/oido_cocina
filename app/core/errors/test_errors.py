import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors.exceptions import TableNotAvailableError
from app.core.errors.handlers import register_exception_handlers


class Body(BaseModel):
    nombre: str


@pytest.fixture
def client():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/conflicto")
    def conflicto():
        raise TableNotAvailableError()

    @app.get("/boom")
    def boom():
        raise RuntimeError("SELECT * FROM users -- secreto")

    @app.post("/validar")
    def validar(body: Body):
        return body

    return TestClient(app, raise_server_exceptions=False)


def test_conflicto_mesa(client):
    r = client.get("/conflicto")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "TABLE_NOT_AVAILABLE"


def test_error_inesperado_sin_detalles(client):
    r = client.get("/boom")
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "SELECT" not in r.text


def test_validacion_422(client):
    r = client.post("/validar", json={})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_no_encontrado_404(client):
    r = client.get("/no-existe")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"