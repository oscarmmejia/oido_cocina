from fastapi import FastAPI

from app.api.test_routes import router as health_router
from app.core.config import get_settings
from app.modules.tables.routes.table import router as tables_router

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(tables_router, prefix=settings.api_prefix)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
