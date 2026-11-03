from fastapi import FastAPI
from app.core.database_connection import engine, Base
from app.models.user import User 

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Oído Cocina API")

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Oído Cocina"}
