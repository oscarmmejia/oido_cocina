from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors.exceptions import EmployeeNotFoundError, UserNotInRestaurantError
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


def _validate_user_link(db: Session, restaurant_id: int, user_id: int | None) -> None:
    if user_id is None:                       # vínculo opcional
        return
    # TODO: sustituir por el import real del modelo User cuando llegue a dev
    from app.modules.PENDIENTE.models.user import User

    user = db.get(User, user_id)
    if user is None or user.restaurant_id != restaurant_id:   # CA2
        raise UserNotInRestaurantError()


def get_employee(db: Session, restaurant_id: int, employee_id: int) -> Employee:
    emp = db.scalar(
        select(Employee).where(
            Employee.id == employee_id, Employee.restaurant_id == restaurant_id
        )
    )
    if emp is None:
        raise EmployeeNotFoundError()
    return emp


def create_employee(db: Session, restaurant_id: int, data: EmployeeCreate) -> Employee:
    _validate_user_link(db, restaurant_id, data.user_id)
    emp = Employee(restaurant_id=restaurant_id, **data.model_dump())   # CA1
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


def list_employees(db: Session, restaurant_id: int, is_active: bool | None = None):
    query = select(Employee).where(Employee.restaurant_id == restaurant_id)
    if is_active is not None:
        query = query.where(Employee.is_active == is_active)
    return db.scalars(query.order_by(Employee.full_name)).all()


def update_employee(
    db: Session, restaurant_id: int, employee_id: int, data: EmployeeUpdate
) -> Employee:
    emp = get_employee(db, restaurant_id, employee_id)
    changes = data.model_dump(exclude_unset=True)
    if "user_id" in changes:
        _validate_user_link(db, restaurant_id, changes["user_id"])
    for field, value in changes.items():
        setattr(emp, field, value)
    db.commit()
    db.refresh(emp)
    return emp


def set_active(db: Session, restaurant_id: int, employee_id: int, active: bool) -> Employee:
    emp = get_employee(db, restaurant_id, employee_id)
    emp.is_active = active                    # sin borrado: CA3
    db.commit()
    db.refresh(emp)
    return emp