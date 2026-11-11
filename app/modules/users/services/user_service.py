from contextlib import contextmanager

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.kernel.errors import AppError
from app.core.kernel.identity import CurrentUser
from app.core.passwords import hash_password
from app.core.permissions import ROLE_SUPERADMIN
from app.models import Role, User
from app.modules.users.schemas import (
    UserCreate, UserPage, UserPagination, UserRead, UserUpdate,
    UserRoleUpdate,
)


def _email_taken() -> AppError:
    return AppError("CONFLICT", "Ya existe un usuario con ese correo electrónico.", 409)


@contextmanager
def _user_transaction(db: Session):
    try:
        yield
        db.commit()
    except IntegrityError as error:
        db.rollback()
        constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        if constraint == "uq_users_email_lower":
            raise _email_taken() from error
        raise
    except Exception:
        db.rollback()
        raise


def list_users(
    db: Session, restaurant_id: int, pagination: UserPagination
) -> UserPage:
    condition = User.restaurant_id == restaurant_id
    total = db.scalar(select(func.count()).select_from(User).where(condition)) or 0
    users = db.scalars(
        select(User)
        .where(condition)
        .order_by(User.id)
        .offset((pagination.page - 1) * pagination.page_size)
        .limit(pagination.page_size)
    )
    return UserPage(
        items=[UserRead.model_validate(user) for user in users],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


def create_user(db: Session, restaurant_id: int, payload: UserCreate) -> UserRead:
    with _user_transaction(db):
        role = db.scalar(
            select(Role).where(
                Role.id == payload.role_id,
                Role.restaurant_id == restaurant_id,
            )
        )
        if role is None:
            raise AppError("NOT_FOUND", "El rol solicitado no existe.", 404)
        if role.name == ROLE_SUPERADMIN:
            raise AppError("FORBIDDEN", "No está permitido asignar el rol de superadministrador.", 403)

        existing = db.scalar(
            select(User.id).where(func.lower(User.email) == str(payload.email))
        )
        if existing is not None:
            raise _email_taken()

        user = User(
            restaurant_id=restaurant_id,
            role_id=role.id,
            name=payload.name,
            email=str(payload.email),
            phone_number=payload.phone_number,
            password_hash=hash_password(payload.password.get_secret_value()),
            is_active=True,
        )
        db.add(user)
        db.flush()
        response = UserRead.model_validate(user)

    return response



def _editable_user(db: Session, actor: CurrentUser, user_id: int) -> User:
    user = db.scalar(
        select(User).where(
            User.id == user_id, User.restaurant_id == actor.restaurant_id,
        ).with_for_update().execution_options(populate_existing=True)
    )
    if user is None:
        raise AppError("NOT_FOUND", "El usuario solicitado no existe.", 404)
    if user.role.name == ROLE_SUPERADMIN and actor.role != ROLE_SUPERADMIN:
        raise AppError("FORBIDDEN", "No está permitido modificar esta cuenta de superadministrador.", 403)
    return user


def update_user(db: Session, actor: CurrentUser, user_id: int, payload: UserUpdate) -> UserRead:
    with _user_transaction(db):
        user = _editable_user(db, actor, user_id)
        changes = payload.model_dump(exclude_unset=True)
        email = changes.get("email")
        if email is not None and email != user.email:
            existing = db.scalar(select(User.id).where(
                func.lower(User.email) == str(email), User.id != user.id,
            ))
            if existing is not None:
                raise _email_taken()
        password = changes.pop("password", None)
        password_hash = (
            hash_password(password.get_secret_value()) if password is not None else None
        )
        if password_hash is not None or (email is not None and email != user.email):
            user.token_version += 1
        for field, value in changes.items():
            setattr(user, field, value)
        if password_hash is not None:
            user.password_hash = password_hash
        db.flush()
        response = UserRead.model_validate(user)
    return response


def update_user_role(db: Session, actor: CurrentUser, user_id: int, payload: UserRoleUpdate) -> UserRead:
    with _user_transaction(db):
        user = _editable_user(db, actor, user_id)
        if user.id == actor.id:
            raise AppError("FORBIDDEN", "No está permitido cambiar el rol propio.", 403)
        role = db.scalar(select(Role).where(
            Role.id == payload.role_id, Role.restaurant_id == actor.restaurant_id,
        ))
        if role is None:
            raise AppError("NOT_FOUND", "El rol solicitado no existe.", 404)
        if role.name == ROLE_SUPERADMIN:
            raise AppError("FORBIDDEN", "No está permitido asignar el rol de superadministrador.", 403)
        if user.role_id != role.id:
            user.role_id = role.id
            user.token_version += 1
        db.flush()
        response = UserRead.model_validate(user)
    return response
