from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.controllers.user import create_user
from app.core.database_connection import get_db
from app.core.kernel.permissions import SystemPermission, require_permission
from app.core.scope import get_restaurant_scope
from app.modules.users.schemas import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermission.USER_MANAGE))],
    summary="Create a restaurant user",
    description="Create a user with an existing role from the authenticated restaurant.",
    responses={
        401: {"description": "Authentication is required."},
        403: {"description": "Permission is missing or the role is forbidden."},
        404: {"description": "The requested restaurant role does not exist."},
        409: {"description": "The email is already registered."},
        422: {"description": "The request data is invalid."},
    },
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    restaurant_id: int = Depends(get_restaurant_scope),
) -> UserRead:
    return create_user(db=db, user_data=user_data, restaurant_id=restaurant_id)
