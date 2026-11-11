from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database_connection import get_db
from app.core.kernel.errors import AppError
from app.models.security_model import User

security_scheme = HTTPBearer(auto_error=False)

DEV_RESTAURANT_ID = 1
DEV_USER_ID = 1


class CurrentUser(BaseModel):
    id: int
    restaurant_id: int
    email: str
    role: str
    permissions: frozenset[str]
    token_version: int


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
        role=role_name,
        permissions=permissions,
        token_version=user.token_version,
    )