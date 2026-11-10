from enum import Enum
from collections.abc import Callable
from fastapi import Depends, HTTPException, status
from app.core.kernel.identity import CurrentUser, get_current_user

class SystemPermission(str, Enum):
    DISH_CREATE = "dish:create"
    MENU_UPDATE_PRICE = "menu:updatePrice"
    RESERVATION_ASSIGN = "reservation:assign"
    SETTINGS_UPDATE = "settings:update"
    USER_MANAGE = "user:manage"

def require_permission(permission: str) -> Callable[..., CurrentUser]:
    async def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario no tiene un rol asignado."
            )

        user_permissions = set()
        
        if hasattr(user, "permissions") and user.permissions:
            user_permissions = set(user.permissions)
        elif hasattr(user.role, "permissions") and user.role.permissions:
            user_permissions = {p.name for p in user.role.permissions}
        elif isinstance(user.role, str) and user.role == "superadmin":
            user_permissions = {permission}

        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes los permisos necesarios para esta acción."
            )

        return user

    return checker