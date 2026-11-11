from sqlalchemy.orm import Session

from app.modules.users.schemas import UserCreate, UserRead
from app.modules.users.services.user_service import create_user as create_user_service


def create_user(
    db: Session, user_data: UserCreate, restaurant_id: int
) -> UserRead:
    return create_user_service(db, restaurant_id, user_data)
