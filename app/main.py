from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.test_routes import router as health_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.core.kernel.errors import register_error_handlers
from app.models.user import User
from app.api.dish_routes import router as dish_router
from app.api.category_routes import router as category_router
from app.core.config import get_settings
from app.core.kernel.errors import register_error_handlers
from app.modules.tables.routes.table import router as tables_router
from app.api.allergen_routes import router as allergen_router

settings = get_settings()

app = FastAPI(title=settings.app_name)
register_error_handlers(app)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(users_router, prefix=settings.api_prefix)

app.include_router(tables_router, prefix=settings.api_prefix)
app.include_router(dish_router, prefix=settings.api_prefix)
app.include_router(category_router, prefix=settings.api_prefix)
app.include_router(allergen_router, prefix=settings.api_prefix)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Oído Cocina"}