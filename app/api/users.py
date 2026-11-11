from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.controllers.user import create_user
from app.core.database_connection import get_db
from app.core.kernel.errors import ErrorResponse
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
        401: {"model": ErrorResponse, "description": "Authentication is required."},
        403: {"model": ErrorResponse, "description": "Permission is missing or the role is forbidden."},
        404: {"model": ErrorResponse, "description": "The requested restaurant role does not exist."},
        409: {"model": ErrorResponse, "description": "The email is already registered."},
        422: {"model": ErrorResponse, "description": "The request data is invalid."},
        500: {"model": ErrorResponse, "description": "Unexpected server error."},
    },
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    restaurant_id: int = Depends(get_restaurant_scope),
) -> UserRead:
    return create_user(db=db, user_data=user_data, restaurant_id=restaurant_id)
