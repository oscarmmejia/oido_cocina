from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database_connection import get_db
from app.schemas.user import UserCreate
from app.controllers.user import create_user
from app.core.kernel.permissions import require_permission, SystemPermission
from app.core.kernel.identity import CurrentUser

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("")
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission(SystemPermission.USER_MANAGE))
):
    return create_user(db=db, user_data=user_data)