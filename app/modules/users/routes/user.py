from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from app.api.users import router
from app.core.database_connection import get_db
from app.core.kernel.errors import ErrorResponse
from app.core.kernel.identity import CurrentUser
from app.core.kernel.permissions import SystemPermission, require_permission
from app.core.scope import get_restaurant_scope
from app.modules.users.schemas import (
    UserPage, UserPagination, UserRead, UserUpdate, UserRoleUpdate,
)
from app.modules.users.services.user_service import (
    list_users, update_user, update_user_role,
)


@router.get(
    "",
    response_model=UserPage,
    dependencies=[Depends(require_permission(SystemPermission.USER_MANAGE.value))],
    summary="List restaurant users",
    description=(
        "List users belonging to the persisted authenticated user's restaurant. "
        "Requires user:manage. Results include active and inactive users, ordered "
        "by ID. Pagination starts at page 1, with 20 users per page and a maximum "
        "page size of 100. Pages beyond the results return an empty items list. "
        "Passwords, hashes and tokens are never included."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid authentication."},
        403: {"model": ErrorResponse, "description": "Missing permission or invalid restaurant association."},
        422: {"model": ErrorResponse, "description": "Invalid pagination or unknown query parameters."},
        500: {"model": ErrorResponse, "description": "Unexpected server error."},
    },
)
def get_users(
    pagination: Annotated[UserPagination, Query()],
    restaurant_id: int = Depends(get_restaurant_scope),
    db: Session = Depends(get_db),
) -> UserPage:
    return list_users(db, restaurant_id, pagination)


USER_UPDATE_RESPONSES = {
    401: {"model": ErrorResponse, "description": "Missing, invalid or revoked authentication."},
    403: {"model": ErrorResponse, "description": "Missing permission, self role change or protected account."},
    404: {"model": ErrorResponse, "description": "User or role not found in the authenticated restaurant."},
    422: {"model": ErrorResponse, "description": "Invalid fields or protected input."},
    500: {"model": ErrorResponse, "description": "Unexpected server error."},
}


@router.patch(
    "/{user_id}", response_model=UserRead,
    summary="Update restaurant user data",
    description=(
        "Requires user:manage. Update name, email, phone_number or password in the "
        "authenticated restaurant. Omitted fields are preserved; phone_number may "
        "be null. Changing email or supplying a password revokes existing sessions. "
        "Passwords are hashed and never returned."
    ),
    responses={**USER_UPDATE_RESPONSES, 409: {
        "model": ErrorResponse, "description": "The email is already registered."
    }},
)
def patch_user(
    user_id: int, payload: UserUpdate,
    actor: CurrentUser = Depends(require_permission(SystemPermission.USER_MANAGE.value)),
    db: Session = Depends(get_db),
) -> UserRead:
    return update_user(db, actor, user_id, payload)


@router.patch(
    "/{user_id}/role", response_model=UserRead,
    summary="Change a restaurant user's role",
    description=(
        "Requires user:manage. Assign one existing role from the authenticated "
        "restaurant. Changing your own role and assigning superadministrator are "
        "forbidden. An actual role change revokes existing sessions."
    ), responses=USER_UPDATE_RESPONSES,
)
def patch_user_role(
    user_id: int, payload: UserRoleUpdate,
    actor: CurrentUser = Depends(require_permission(SystemPermission.USER_MANAGE.value)),
    db: Session = Depends(get_db),
) -> UserRead:
    return update_user_role(db, actor, user_id, payload)
