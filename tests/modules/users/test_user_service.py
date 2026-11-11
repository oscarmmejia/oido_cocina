from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.kernel.errors import AppError
from app.core.passwords import verify_password
from app.core.kernel.permissions import ROLE_SUPERADMIN, ROLE_WAITER
from app.models import Restaurant, Role, User
from app.modules.users.schemas import UserCreate, UserPagination
from app.modules.users.services.user_service import create_user, list_users


@pytest.fixture
def role(db, restaurant):
    value = Role(restaurant_id=restaurant.id, name=ROLE_WAITER)
    db.add(value)
    db.commit()
    db.refresh(value)
    return value


def _payload(role_id, email="ana@example.com"):
    return UserCreate(
        name="Ana", email=email, password="test-password", role_id=role_id
    )


def test_create_persists_hashed_password_and_public_response(db, restaurant, role):
    response = create_user(db, restaurant.id, _payload(role.id))
    db.expire_all()
    stored = db.get(User, response.id)

    assert stored.restaurant_id == restaurant.id
    assert stored.role_id == role.id
    assert stored.is_active is True
    assert stored.password_hash != "test-password"
    assert verify_password("test-password", stored.password_hash)
    assert response.model_dump() == {
        "id": stored.id,
        "restaurant_id": restaurant.id,
        "role_id": role.id,
        "name": "Ana",
        "email": "ana@example.com",
        "phone_number": None,
        "is_active": True,
    }


def test_duplicate_email_is_case_insensitive_and_atomic(db, restaurant, role):
    create_user(db, restaurant.id, _payload(role.id))

    with pytest.raises(AppError) as error:
        create_user(db, restaurant.id, _payload(role.id, "ANA@EXAMPLE.COM"))

    assert error.value.status_code == 409
    assert error.value.message == "Ya existe un usuario con ese correo electrónico."
    assert db.scalar(select(func.count()).select_from(User)) == 1


def test_other_restaurant_role_is_not_assignable(db, restaurant, role):
    other = Restaurant(id=restaurant.id + 1, name="Other", time_zone="Europe/Madrid")
    db.add(other)
    db.flush()
    other_role = Role(restaurant_id=other.id, name=ROLE_WAITER)
    db.add(other_role)
    db.commit()

    with pytest.raises(AppError) as error:
        create_user(db, restaurant.id, _payload(other_role.id))

    assert error.value.status_code == 404
    assert db.scalar(select(func.count()).select_from(User)) == 0


def test_duplicate_email_in_another_restaurant_is_rejected(db, restaurant, role):
    create_user(db, restaurant.id, _payload(role.id))
    other = Restaurant(id=restaurant.id + 1, name="Other", time_zone="Europe/Madrid")
    db.add(other)
    db.flush()
    other_role = Role(restaurant_id=other.id, name=ROLE_WAITER)
    db.add(other_role)
    db.commit()

    with pytest.raises(AppError) as error:
        create_user(db, other.id, _payload(other_role.id))

    assert error.value.status_code == 409
    assert db.scalar(select(func.count()).select_from(User)) == 1


def test_superadmin_role_is_rejected_without_creating_user(db, restaurant):
    privileged = Role(restaurant_id=restaurant.id, name=ROLE_SUPERADMIN)
    db.add(privileged)
    db.commit()

    with pytest.raises(AppError) as error:
        create_user(db, restaurant.id, _payload(privileged.id))

    assert error.value.status_code == 403
    assert error.value.message == "No está permitido asignar el rol de superadministrador."
    assert db.scalar(select(func.count()).select_from(User)) == 0


def test_unknown_role_is_rejected(db, restaurant):
    with pytest.raises(AppError) as error:
        create_user(db, restaurant.id, _payload(9999))

    assert error.value.status_code == 404
    assert error.value.message == "El rol solicitado no existe."
    assert db.scalar(select(func.count()).select_from(User)) == 0


def test_listing_is_paginated_ordered_and_scoped(db, restaurant, role):
    first = create_user(db, restaurant.id, _payload(role.id, "first@example.com"))
    second = create_user(db, restaurant.id, _payload(role.id, "second@example.com"))
    other = Restaurant(id=restaurant.id + 1, name="Other", time_zone="Europe/Madrid")
    db.add(other)
    db.flush()
    other_role = Role(restaurant_id=other.id, name=ROLE_WAITER)
    db.add(other_role)
    db.commit()
    create_user(db, other.id, _payload(other_role.id, "other@example.com"))

    page = list_users(db, restaurant.id, UserPagination(page=2, page_size=1))
    empty = list_users(db, restaurant.id, UserPagination(page=3, page_size=1))

    assert page.total == 2
    assert page.page == 2
    assert page.page_size == 1
    assert [user.id for user in page.items] == [second.id]
    assert first.id < second.id
    assert empty.items == []
    assert empty.total == 2


def test_empty_restaurant_listing(db, restaurant):
    page = list_users(db, restaurant.id, UserPagination())

    assert page.items == []
    assert page.total == 0


def test_unique_constraint_race_is_translated_and_rolled_back():
    db = Mock()
    db.scalar.side_effect = [SimpleNamespace(id=7, name=ROLE_WAITER), None]
    original = Exception("simulated conflict")
    original.diag = SimpleNamespace(constraint_name="uq_users_email_lower")
    db.flush.side_effect = IntegrityError("INSERT", {}, original)

    with pytest.raises(AppError) as error:
        create_user(db, 1, _payload(7))

    assert error.value.status_code == 409
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_unrelated_integrity_error_is_not_reported_as_duplicate():
    db = Mock()
    db.scalar.side_effect = [SimpleNamespace(id=7, name=ROLE_WAITER), None]
    original = Exception("unrelated conflict")
    original.diag = SimpleNamespace(constraint_name="other_constraint")
    db.flush.side_effect = IntegrityError("INSERT", {}, original)

    with pytest.raises(IntegrityError):
        create_user(db, 1, _payload(7))

    db.rollback.assert_called_once()
    db.commit.assert_not_called()
