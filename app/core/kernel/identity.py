from fastapi import Depends
from pydantic import BaseModel

from app.api.auth import get_current_user as get_authenticated_user
from app.core.kernel.errors import AppError
from app.models import User


class CurrentUser(BaseModel):
    id: int
    restaurant_id: int | None = None
    email: str
    role: str
    permissions: set[str]


async def get_current_user(user: User = Depends(get_authenticated_user)) -> CurrentUser:
    role = user.role
    if (
        user.restaurant_id is None
        or role is None
        or role.restaurant_id != user.restaurant_id
    ):
        raise AppError("FORBIDDEN", "The user has no valid restaurant role.", 403)

    return CurrentUser(
        id=user.id,
        restaurant_id=user.restaurant_id,
        email=user.email,
        role=role.name,
        permissions={permission.name for permission in role.permissions},
    )
