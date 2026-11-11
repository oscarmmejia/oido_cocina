import pytest

from app.core.kernel.identity import CurrentUser, get_current_user
from app.main import app
from tests.conftest import TEST_RESTAURANT_ID


@pytest.fixture
def user_without_permissions():
    def override() -> CurrentUser:
        return CurrentUser(
            id=2,
            restaurant_id=TEST_RESTAURANT_ID,
            email="sin-permisos@example.com",
            role="viewer",
            permissions=set(),
        )

    app.dependency_overrides[get_current_user] = override
    yield
    app.dependency_overrides.pop(get_current_user, None)
