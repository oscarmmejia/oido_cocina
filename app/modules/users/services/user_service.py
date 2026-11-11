from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.kernel.errors import AppError
from app.core.passwords import hash_password
from app.core.permissions import ROLE_SUPERADMIN
from app.models import Role, User
from app.modules.users.schemas import UserCreate, UserPage, UserPagination, UserRead


def _email_taken() -> AppError:
    return AppError("CONFLICT", "Ya existe un usuario con ese correo electrónico.", 409)


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
    try:
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

    return response
