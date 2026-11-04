from pydantic import BaseModel

from app.core.config import get_settings
from app.core.kernel.errors import AppError

DEV_RESTAURANT_ID = 1
DEV_USER_ID = 1


class CurrentUser(BaseModel):
    id: int
    restaurant_id: int
    email: str
    role: str
    permissions: set[str]


async def get_current_user() -> CurrentUser:
    # TODO: TEMPORAL: sustituir en HU-AUT-04 (leer el token JWT y buscar el usuario)
    if not get_settings().auth_stubs_enabled:
        raise AppError("UNAUTHORIZED", "Autenticación requerida.", 401)

    return CurrentUser(
        id=DEV_USER_ID,
        restaurant_id=DEV_RESTAURANT_ID,
        email="dev@oidocina.local",
        role="superadmin",
        permissions={"*"},
    )