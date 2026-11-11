from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.kernel.errors import AppError
from app.models import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


def _validate_user_link(db: Session, restaurant_id: int, user_id: int | None) -> None:
    if user_id is None:
        return
    raise AppError("BAD_REQUEST", "El vínculo con usuario aún no está disponible.", 400)


def get_employee(db: Session, restaurant_id: int, employee_id: int) -> Employee:
    emp = db.scalar(
        select(Employee).where(
            Employee.id == employee_id, Employee.restaurant_id == restaurant_id
        )
    )
    if emp is None:
        raise AppError("EMPLOYEE_NOT_FOUND", "Empleado no encontrado.", 404)
    return emp


def create_employee(db: Session, restaurant_id: int, data: EmployeeCreate) -> Employee:
    _validate_user_link(db, restaurant_id, data.user_id)
    emp = Employee(restaurant_id=restaurant_id, **data.model_dump())
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
    emp.is_active = active
    db.commit()
    db.refresh(emp)
    return emp