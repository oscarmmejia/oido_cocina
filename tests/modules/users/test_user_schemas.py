import pytest
from pydantic import ValidationError

from app.modules.users.schemas import UserCreate, UserPagination, UserRead


def _payload(**changes):
    return {
        "name": "Ana",
        "email": "ana@example.com",
        "password": "test-password",
        "role_id": 7,
        **changes,
    }


def test_creation_normalizes_email_and_hides_password_in_repr():
    payload = UserCreate.model_validate(_payload(email=" ANA@EXAMPLE.COM "))

    assert payload.email == "ana@example.com"
    assert payload.password.get_secret_value() == "test-password"
    assert "test-password" not in repr(payload)


@pytest.mark.parametrize(
    "changes",
    [
        {"name": ""},
        {"name": "a" * 151},
        {"email": "invalid-address"},
        {"password": ""},
        {"role_id": 0},
        {"role_id": None},
        {"phone_number": "1" * 31},
    ],
)
def test_creation_rejects_invalid_fields(changes):
    with pytest.raises(ValidationError):
        UserCreate.model_validate(_payload(**changes))


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", 1),
        ("restaurant_id", 2),
        ("is_active", False),
        ("password_hash", "hash"),
        ("token_version", 0),
        ("permissions", ["*"]),
    ],
)
def test_creation_rejects_server_managed_fields(field, value):
    with pytest.raises(ValidationError):
        UserCreate.model_validate(_payload(**{field: value}))


@pytest.mark.parametrize("changes", [{"page": 0}, {"page_size": 0}, {"page_size": 101}])
def test_pagination_rejects_invalid_ranges(changes):
    with pytest.raises(ValidationError):
        UserPagination.model_validate(changes)


def test_response_has_only_public_fields():
    assert set(UserRead.model_fields) == {
        "id", "restaurant_id", "role_id", "name", "email", "phone_number", "is_active"
    }
