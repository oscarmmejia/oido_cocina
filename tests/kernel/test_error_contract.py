"""Contrato único de errores: {"error": {"code", "message"}} vía el kernel."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.kernel.errors import AppError, register_error_handlers


class Body(BaseModel):
    nombre: str


@pytest.fixture
def client():
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/conflicto")
    def conflicto():
        raise AppError("TABLE_NOT_AVAILABLE", "La mesa no está disponible", 409)

    @app.get("/boom")
    def boom():
        raise RuntimeError("SELECT * FROM users -- secreto")

    @app.post("/validar")
    def validar(body: Body):
        return body

    return TestClient(app, raise_server_exceptions=False)


def test_error_de_negocio_usa_su_codigo(client):
    r = client.get("/conflicto")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "TABLE_NOT_AVAILABLE"


def test_error_inesperado_no_filtra_detalles(client):
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
