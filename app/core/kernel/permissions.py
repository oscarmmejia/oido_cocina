from collections.abc import Callable

from fastapi import Depends

from app.core.kernel.identity import CurrentUser, get_current_user


def require_permission(permission: str) -> Callable[..., CurrentUser]:
    async def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        # TODO: TEMPORAL: sustituir en HU-AUT-05 (comprobar user.permissions)
        return user

    return checker