from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.allergen_routes import router as allergen_router
from app.api.category_routes import router as category_router
from app.api.dish_routes import router as dish_router
from app.api.menu_collection_routes import router as menu_collection_router
from app.api.test_routes import router as health_router
from app.core.config import get_settings
from app.core.database_connection import SessionLocal
from app.core.kernel.errors import register_error_handlers
from app.core.kernel.seed import seed_minimum_data
from app.modules.tables.routes.table import router as tables_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.seed_on_startup:
        with SessionLocal() as db:
            seed_minimum_data(db)
            db.commit()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
register_error_handlers(app)
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(tables_router, prefix=settings.api_prefix)
app.include_router(menu_collection_router, prefix=settings.api_prefix)
app.include_router(dish_router, prefix=settings.api_prefix)
app.include_router(category_router, prefix=settings.api_prefix)
app.include_router(allergen_router, prefix=settings.api_prefix)
