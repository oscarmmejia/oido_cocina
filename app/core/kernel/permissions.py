from collections.abc import Callable
from enum import Enum

from fastapi import Depends

from app.core.kernel.errors import AppError
from app.core.kernel.identity import CurrentUser, get_current_user


class SystemPermission(str, Enum):
    DISH_CREATE = "dish:create"
    MENU_UPDATE_PRICE = "menu:updatePrice"
    RESERVATION_ASSIGN = "reservation:assign"
    SETTINGS_UPDATE = "settings:update"
    USER_MANAGE = "user:manage"


def require_permission(permission: str) -> Callable[..., CurrentUser]:
    async def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if permission in user.permissions or "*" in user.permissions:
            return user
        raise AppError("FORBIDDEN", "You do not have permission for this action.", 403)

    return checker
