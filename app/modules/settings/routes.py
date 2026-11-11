from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.core.kernel.errors import ErrorResponse
from app.core.kernel.permissions import SystemPermission, require_permission
from app.core.scope import get_restaurant_scope
from app.modules.settings.schemas import (
    RestaurantSettingsResponse,
    RestaurantSettingsUpdate,
)
from app.modules.settings.services.restaurant_service import (
    get_restaurant_settings,
    update_restaurant_settings,
)

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get(
    "",
    response_model=RestaurantSettingsResponse,
    description="Read settings for the restaurant associated with the authenticated user.",
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid authentication."},
        403: {"model": ErrorResponse, "description": "Invalid restaurant association."},
        404: {"model": ErrorResponse, "description": "Restaurant not found."},
        500: {"model": ErrorResponse, "description": "Unexpected server error."},
    },
)
def get_settings(
    restaurant_id: int = Depends(get_restaurant_scope),
    db: Session = Depends(get_db),
):
    return get_restaurant_settings(db, restaurant_id)


@router.patch(
    "",
    response_model=RestaurantSettingsResponse,
    dependencies=[Depends(require_permission(SystemPermission.SETTINGS_UPDATE.value))],
    description=(
        "Partially update the authenticated user's restaurant settings. Requires "
        "settings:update. Omitted fields are preserved and the resulting configuration "
        "is validated before saving. Overnight hours are supported; equal opening "
        "and closing times are rejected. Continuous 24-hour operation is not supported."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid authentication."},
        403: {"model": ErrorResponse, "description": "Missing permission or invalid restaurant association."},
        404: {"model": ErrorResponse, "description": "Restaurant not found."},
        422: {"model": ErrorResponse, "description": "Invalid fields or resulting configuration."},
        500: {"model": ErrorResponse, "description": "Unexpected server error."},
    },
)
def patch_settings(
    payload: RestaurantSettingsUpdate,
    restaurant_id: int = Depends(get_restaurant_scope),
    db: Session = Depends(get_db),
):
    return update_restaurant_settings(db, restaurant_id, payload)
