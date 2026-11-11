from datetime import date, timedelta
import pytest
from fastapi import status
from app.modules.schedules.models.schedule import ScheduleStatus
from app.models.employee import Employee
from app.core.config import get_settings

settings = get_settings()
PREFIX = f"{settings.api_prefix}/schedules"


def create_dummy_employee(db, restaurant_id):
    employee = db.query(Employee).filter(Employee.id == 1).first()
    if not employee:
        employee = Employee(
            id=1,
            restaurant_id=restaurant_id,
            full_name="Empleado Demo",
            job_position="cook",
            is_active=True,
        )
        db.add(employee)
        db.commit()
    return employee


def test_schedule_schema_valid_dates():

    from app.modules.schedules.schemas.schedule import ScheduleCreate

    today = date.today()
    next_week = today + timedelta(days=7)

    schedule_data = ScheduleCreate(
        period_start=today,
        period_end=next_week,
        responsible_id=1
    )
    assert schedule_data.period_start == today
    assert schedule_data.period_end == next_week


def test_schedule_schema_invalid_dates_raises_value_error():

    from pydantic import ValidationError
    from app.modules.schedules.schemas.schedule import ScheduleCreate

    today = date.today()
    yesterday = today - timedelta(days=1)

    with pytest.raises(ValidationError) as exc_info:
        ScheduleCreate(
            period_start=today,
            period_end=yesterday,
            responsible_id=1
        )

    assert "La fecha de inicio del periodo no puede ser posterior a la fecha de fin." in str(exc_info.value)



def test_create_schedule_success(client, db, restaurant):

    create_dummy_employee(db, restaurant_id=restaurant.id)

    today = date.today()
    next_week = today + timedelta(days=7)

    payload = {
        "period_start": today.isoformat(),
        "period_end": next_week.isoformat(),
        "responsible_id": 1
    }

    response = client.post(f"{PREFIX}/", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == ScheduleStatus.BORRADOR.value
    assert data["period_start"] == today.isoformat()
    assert data["period_end"] == next_week.isoformat()
    assert data["published_at"] is None


def test_create_schedule_invalid_period_returns_422(client):

    today = date.today()
    yesterday = today - timedelta(days=1)

    payload = {
        "period_start": today.isoformat(),
        "period_end": yesterday.isoformat(),
        "responsible_id": 1
    }

    response = client.post(f"{PREFIX}/", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_publish_schedule_success(client, db, restaurant):

    create_dummy_employee(db, restaurant_id=restaurant.id)

    today = date.today()
    next_week = today + timedelta(days=7)

    create_res = client.post(
        f"{PREFIX}/",
        json={
            "period_start": today.isoformat(),
            "period_end": next_week.isoformat(),
            "responsible_id": 1
        }
    )
    schedule_id = create_res.json()["id"]

    publish_res = client.patch(f"{PREFIX}/{schedule_id}/publish")

    assert publish_res.status_code == status.HTTP_200_OK
    data = publish_res.json()
    assert data["status"] == ScheduleStatus.PUBLICADO.value
    assert data["published_at"] is not None
    assert data["responsible_id"] is not None


def test_publish_already_published_schedule_returns_400(client, db, restaurant):

    create_dummy_employee(db, restaurant_id=restaurant.id)

    today = date.today()
    create_res = client.post(
        f"{PREFIX}/",
        json={
            "period_start": today.isoformat(),
            "period_end": (today + timedelta(days=7)).isoformat(),
            "responsible_id": 1
        }
    )
    schedule_id = create_res.json()["id"]
    client.patch(f"{PREFIX}/{schedule_id}/publish")

    republish_res = client.patch(f"{PREFIX}/{schedule_id}/publish")

    assert republish_res.status_code == status.HTTP_400_BAD_REQUEST


def test_get_nonexistent_schedule_returns_404(client):

    response = client.get(f"{PREFIX}/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_create_shift_nocturno_returns_201(client, db, restaurant):
    # crear empleado activo, crear schedule borrador, crear shift 22:00 -> 02:00 (siguiente día)
    ...

def test_create_shift_jornada_partida_returns_201(client, db, restaurant):
    # crear dos shifts: 12:00-16:00 y 20:00-23:00, duración total 7h
    ...

def test_delete_shift_in_published_schedule_returns_409(client, db, restaurant):
    # publish, crear shift, delete shift -> 409, sigue existiendo
    ...

def test_create_shift_inactive_employee_returns_422(client, db, restaurant):
    # empleado inactivo, shift -> 422, no se guarda
    ...