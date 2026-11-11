from fastapi import Depends
<<<<<<< HEAD
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
=======
>>>>>>> 12b3098e8eea525fb0e048e0bdba66becdc963d3
from pydantic import BaseModel
from sqlalchemy.orm import Session

<<<<<<< HEAD
from app.core.config import get_settings
from app.core.database_connection import get_db
from app.core.kernel.errors import AppError
from app.models.security_model import User

security_scheme = HTTPBearer(auto_error=False)

DEV_RESTAURANT_ID = 1
DEV_USER_ID = 1
=======
from app.api.auth import get_current_user as get_authenticated_user
from app.core.kernel.errors import AppError
from app.models import User
>>>>>>> 12b3098e8eea525fb0e048e0bdba66becdc963d3


class CurrentUser(BaseModel):
    id: int
    restaurant_id: int | None = None
    email: str
    role: str
    permissions: frozenset[str]
    token_version: int


<<<<<<< HEAD
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> CurrentUser:
    settings = get_settings()

    # Importación local para evitar el bucle circular al iniciar la app
    from app.core.kernel.permissions import ROLE_PERMISSIONS, PERMISSION_NAMES

    if settings.auth_stubs_enabled and not credentials:
        return CurrentUser(
            id=DEV_USER_ID,
            restaurant_id=DEV_RESTAURANT_ID,
            email="dev@oidocina.local",
            role="superadmin",
            permissions=PERMISSION_NAMES,
            token_version=0,
        )

    if not credentials:
        raise AppError("UNAUTHORIZED", "Autenticación requerida.", 401)
=======
async def get_current_user(user: User = Depends(get_authenticated_user)) -> CurrentUser:
    role = user.role
    if (
        user.restaurant_id is None
        or role is None
        or role.restaurant_id != user.restaurant_id
    ):
        raise AppError("FORBIDDEN", "The user has no valid restaurant role.", 403)
>>>>>>> 12b3098e8eea525fb0e048e0bdba66becdc963d3

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: int = payload.get("sub")
        token_version: int = payload.get("token_version", 0)
        
        if user_id is None:
            raise AppError("UNAUTHORIZED", "Token inválido.", 401)
    except JWTError:
        raise AppError("UNAUTHORIZED", "No se pudo validar las credenciales.", 401)

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise AppError("UNAUTHORIZED", "Usuario no encontrado o inactivo.", 401)

    if user.token_version != token_version:
        raise AppError("UNAUTHORIZED", "El token ha sido revocado (sesión cerrada).", 401)

    role_name = user.role.name if user.role else "camarero"
    permissions = ROLE_PERMISSIONS.get(role_name, frozenset())

    return CurrentUser(
        id=user.id,
        restaurant_id=user.restaurant_id,
        email=user.email,
<<<<<<< HEAD
        role=role_name,
        permissions=permissions,
        token_version=user.token_version,
    )
=======
        role=role.name,
        permissions={permission.name for permission in role.permissions},
    )
>>>>>>> 12b3098e8eea525fb0e048e0bdba66becdc963d3
