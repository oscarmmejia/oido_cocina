from typing import Optional
from fastapi import Depends
from pydantic import BaseModel
from app.api.auth import get_current_user as get_authenticated_user
from app.models.user import User

class CurrentUser(BaseModel):
    id: int
    restaurant_id: Optional[int] = None
    email: str
    role: str
    permissions: set[str]

async def get_current_user(user: User = Depends(get_authenticated_user)) -> CurrentUser:
    role_name = "superadmin" if user.role_id == 1 else "user"
    
    return CurrentUser(
        id=user.id,
        restaurant_id=user.restaurant_id,
        email=user.email,
        role=role_name,
        permissions=set()
    )