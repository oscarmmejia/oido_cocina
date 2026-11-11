from fastapi import Depends, HTTPException, status
from app.core.kernel.identity import CurrentUser, get_current_user

def get_restaurant_scope(current_user: CurrentUser = Depends(get_current_user)) -> int:
    if not current_user.restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no tiene un restaurante asociado en su ámbito."
        )
    return current_user.restaurant_id