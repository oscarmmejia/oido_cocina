from fastapi import FastAPI
from app.core.database_connection import engine, Base
from app.models.user import User 
from app.api.auth import router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Oído Cocina API")


app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Oído Cocina"}