from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.passwords import hash_password
from app.core.permissions import PERMISSIONS, ROLE_PERMISSIONS
from app.database.seeders.catalog import (
    DEFAULT_SCHEDULE,
    DEMO_PASSWORD,
    DEMO_RESTAURANT_ID,
    DEMO_RESTAURANT_NAME,
    DEMO_TIME_ZONE,
    USERS,
)
from app.models import (
    Employee,
    Permission,
    Restaurant,
    Role,
    RolePermission,
    User,
)


def seed_restaurant(db: Session) -> Restaurant:
    restaurant = db.get(Restaurant, DEMO_RESTAURANT_ID)
    if restaurant is None:
        restaurant = Restaurant(
            id=DEMO_RESTAURANT_ID,
            name=DEMO_RESTAURANT_NAME,
            time_zone=DEMO_TIME_ZONE,
            is_active=True,
            **DEFAULT_SCHEDULE,
        )
        db.add(restaurant)
        db.flush()
    else:
        restaurant.name = DEMO_RESTAURANT_NAME
        restaurant.time_zone = DEMO_TIME_ZONE
        restaurant.is_active = True
        for field, value in DEFAULT_SCHEDULE.items():
            setattr(restaurant, field, value)
    return restaurant


def seed_permissions(db: Session) -> dict[str, Permission]:
    existing = {
        row.name: row for row in db.scalars(select(Permission))
    }
    result: dict[str, Permission] = {}
    for spec in PERMISSIONS:
        permission = existing.get(spec.name)
        if permission is None:
            permission = Permission(
                name=spec.name,
                description=spec.description,
            )
            db.add(permission)
            existing[spec.name] = permission
        else:
            permission.description = spec.description
        result[spec.name] = permission
    db.flush()
    return result


def seed_roles(
    db: Session,
    restaurant: Restaurant,
) -> dict[str, Role]:
    existing = {
        row.name: row
        for row in db.scalars(
            select(Role).where(Role.restaurant_id == restaurant.id)
        )
    }
    result: dict[str, Role] = {}
    for name in ROLE_PERMISSIONS:
        role = existing.get(name)
        if role is None:
            role = Role(restaurant_id=restaurant.id, name=name)
            db.add(role)
            existing[name] = role
        result[name] = role
    db.flush()
    return result


def seed_role_permissions(
    db: Session,
    roles: dict[str, Role],
    permissions: dict[str, Permission],
) -> None:
    role_ids = [role.id for role in roles.values()]
    db.execute(delete(RolePermission).where(RolePermission.role_id.in_(role_ids)))
    for role_name, permission_names in ROLE_PERMISSIONS.items():
        role = roles[role_name]
        for permission_name in sorted(permission_names):
            db.add(
                RolePermission(
                    role_id=role.id,
                    permission_id=permissions[permission_name].id,
                )
            )
    db.flush()


def seed_users(
    db: Session,
    restaurant: Restaurant,
    roles: dict[str, Role],
) -> dict[str, User]:
    existing = {
        user.email: user for user in db.scalars(select(User))
    }
    result: dict[str, User] = {}
    for index, spec in enumerate(USERS):
        user = existing.get(spec["email"])
        if user is None:
            user = User(
                restaurant_id=restaurant.id,
                role_id=roles[spec["role"]].id,
                name=spec["name"],
                email=spec["email"],
                password_hash=hash_password(DEMO_PASSWORD),
                phone_number=spec["phone"],
                is_active=True,
            )
            db.add(user)
            # El primer usuario del catálogo es el superadministrador y debe
            # quedar con DEV_USER_ID en una base recién sembrada.
            if index == 0:
                db.flush()
        else:
            user.restaurant_id = restaurant.id
            user.role_id = roles[spec["role"]].id
            user.name = spec["name"]
            user.phone_number = spec["phone"]
            user.is_active = True
        result[spec["email"]] = user
    db.flush()
    return result


def seed_employees(
    db: Session,
    restaurant: Restaurant,
    users: dict[str, User],
) -> list[Employee]:
    existing = {
        row.user_id: row
        for row in db.scalars(
            select(Employee).where(Employee.restaurant_id == restaurant.id)
        )
    }
    result: list[Employee] = []
    for spec in USERS:
        user = users[spec["email"]]
        employee = existing.get(user.id)
        if employee is None:
            employee = Employee(
                restaurant_id=restaurant.id,
                user_id=user.id,
                full_name=spec["name"],
                job_position=spec["job_position"],
                is_active=True,
            )
            db.add(employee)
        else:
            employee.full_name = spec["name"]
            employee.job_position = spec["job_position"]
            employee.is_active = True
        result.append(employee)
    db.flush()
    return result
