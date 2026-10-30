from fastapi import FastAPI

from app.api.test_routes import router as health_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.include_router(health_router, prefix=settings.api_prefix)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
