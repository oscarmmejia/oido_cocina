from collections.abc import Callable

from fastapi import Depends

from app.core.kernel.errors import AppError
from app.core.kernel.identity import CurrentUser, get_current_user


def require_permission(permission: str) -> Callable[..., CurrentUser]:
    async def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if "*" in user.permissions or permission in user.permissions:
            return user

        raise AppError(
            "FORBIDDEN",
            "No tienes permisos para realizar esta acción",
            403,
        )

    return checker
