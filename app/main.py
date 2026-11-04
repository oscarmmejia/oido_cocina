from fastapi import FastAPI

from app.api.test_routes import router as health_router
from app.core.config import get_settings
from app.core.kernel.errors import register_error_handlers

settings = get_settings()

app = FastAPI(title=settings.app_name)
register_error_handlers(app)
app.include_router(health_router, prefix=settings.api_prefix)

# TODO (CA3): añadir lifespan que llame a seed_minimum_data
# TODO: cuando existan los modelos y la sesión de base de datos.