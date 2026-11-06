from fastapi import FastAPI
from app.core.config import get_settings
from app.core.kernel.errors import register_error_handlers
from app.api.test_routes import router as health_router
from app.api import employees
from app.api.dish_routes import router as dish_router
from app.api.category_routes import router as category_router
from app.modules.tables.routes.table import router as tables_router
from app.api.schedule_routes import router as schedule_router

settings = get_settings()

app = FastAPI(title=settings.app_name)


register_error_handlers(app)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(tables_router, prefix=settings.api_prefix)
app.include_router(dish_router, prefix=settings.api_prefix)
app.include_router(category_router, prefix=settings.api_prefix)
app.include_router(employees.router, prefix=settings.api_prefix)
app.include_router(schedule_router, prefix=settings.api_prefix)


