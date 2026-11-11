from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from app.api.users import router
from app.core.database_connection import get_db
from app.core.kernel.errors import ErrorResponse
from app.core.kernel.permissions import SystemPermission, require_permission
from app.core.scope import get_restaurant_scope
from app.modules.users.schemas import UserPage, UserPagination
from app.modules.users.services.user_service import list_users


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
