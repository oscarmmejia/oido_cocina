import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database_connection import Base
from app.core.kernel.errors import AppError
from app.controllers import employee_controller as controller
from app.models.employee import Employee
from app.modules.settings.models import restaurant  # noqa: F401  (tabla "restaurant")
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


RESTAURANT_ID = 1
OTHER_RESTAURANT_ID = 2


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[Employee.__table__])
    with Session(engine) as session:
        yield session


def _create(db, name="Ana López", position="cook", restaurant_id=RESTAURANT_ID):
    return controller.create_employee(
        db, restaurant_id, EmployeeCreate(full_name=name, job_position=position)
    )



def test_create_employee_without_user(db):
    emp = _create(db)

    assert emp.id is not None
    assert emp.user_id is None
    assert emp.restaurant_id == RESTAURANT_ID      # CA1
    assert emp.is_active is True



def test_deactivate_keeps_employee(db):
    emp = _create(db)

    result = controller.set_active(db, RESTAURANT_ID, emp.id, False)

    assert result.is_active is False
    assert controller.get_employee(db, RESTAURANT_ID, emp.id).id == emp.id   # CA3


def test_reactivate_employee(db):
    emp = _create(db)
    controller.set_active(db, RESTAURANT_ID, emp.id, False)

    assert controller.set_active(db, RESTAURANT_ID, emp.id, True).is_active is True


def test_list_filters_by_restaurant_and_status(db):
    active = _create(db, name="Activa")
    inactive = _create(db, name="Inactiva")
    controller.set_active(db, RESTAURANT_ID, inactive.id, False)
    _create(db, name="Otro restaurante", restaurant_id=OTHER_RESTAURANT_ID)

    assert {e.id for e in controller.list_employees(db, RESTAURANT_ID)} == {active.id, inactive.id}
    assert [e.id for e in controller.list_employees(db, RESTAURANT_ID, True)] == [active.id]
    assert [e.id for e in controller.list_employees(db, RESTAURANT_ID, False)] == [inactive.id]


def test_cannot_read_employee_from_another_restaurant(db):
    emp = _create(db, restaurant_id=OTHER_RESTAURANT_ID)

    with pytest.raises(AppError) as error:
        controller.get_employee(db, RESTAURANT_ID, emp.id)

    assert error.value.status_code == 404
    assert error.value.code == "EMPLOYEE_NOT_FOUND"


def test_update_employee(db):
    emp = _create(db)

    result = controller.update_employee(
        db, RESTAURANT_ID, emp.id, EmployeeUpdate(job_position="head chef")
    )

    assert result.job_position == "head chef"
    assert result.full_name == "Ana López"