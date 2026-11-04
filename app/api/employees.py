from fastapi import APIRouter, Depends, Query
from app.controllers import employee_controller as controller
from app.core.database_connection import get_db
from app.core.kernel.identity import CurrentUser, get_current_user
from app.core.kernel.permissions import require_permission
from app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate

router = APIRouter(prefix="/api/v1/employees", tags=["employees"])
manage = Depends(require_permission("employee:manage"))


@router.post("", response_model=EmployeeRead, status_code=201, dependencies=[manage])
def create_employee(data: EmployeeCreate, db=Depends(get_db), user=Depends(get_current_user)):
    return controller.create_employee(db, user.restaurant_id, data)


@router.get("", response_model=list[EmployeeRead], dependencies=[manage])
def list_employees(
    is_active: bool | None = Query(None),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    return controller.list_employees(db, user.restaurant_id, is_active)


@router.get("/{employee_id}", response_model=EmployeeRead, dependencies=[manage])
def get_employee(employee_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    return controller.get_employee(db, user.restaurant_id, employee_id)


@router.patch("/{employee_id}", response_model=EmployeeRead, dependencies=[manage])
def update_employee(
    employee_id: int, data: EmployeeUpdate, db=Depends(get_db), user=Depends(get_current_user)
):
    return controller.update_employee(db, user.restaurant_id, employee_id, data)


@router.post("/{employee_id}/deactivate", response_model=EmployeeRead, dependencies=[manage])
def deactivate_employee(employee_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    return controller.set_active(db, user.restaurant_id, employee_id, False)


@router.post("/{employee_id}/activate", response_model=EmployeeRead, dependencies=[manage])
def activate_employee(employee_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    return controller.set_active(db, user.restaurant_id, employee_id, True)