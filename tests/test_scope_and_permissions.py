import pytest
from fastapi import HTTPException
from app.core.kernel.identity import CurrentUser
from app.core.scope import get_restaurant_scope

def test_restaurant_scope_success():
    current_user = CurrentUser(id=1, email="test@test.com", role="admin", permissions=set(), restaurant_id=5)
    restaurant_id = get_restaurant_scope(current_user=current_user)
    assert restaurant_id == 5

def test_restaurant_scope_forbidden():
    current_user = CurrentUser(id=2, email="test2@test.com", role="user", permissions=set(), restaurant_id=None)
    with pytest.raises(HTTPException) as exc_info:
        get_restaurant_scope(current_user=current_user)
    assert exc_info.value.status_code == 403