from datetime import date, timedelta

import pytest
from fastapi import status

from app.core.kernel.identity import DEV_RESTAURANT_ID
from app.models import Employee, Restaurant
from app.modules.schedules.models.schedule import Schedule, ScheduleStatus
from app.modules.schedules.schemas.schedule import ScheduleCreate

PREFIX = "/api/v1/schedules"
PERIOD = {"period_start": "2026-11-09", "period_end": "2026-11-15"}


def make_employee(db, restaurant_id=DEV_RESTAURANT_ID, *, name="Empleado Demo", active=True):
    employee = Employee(
        restaurant_id=restaurant_id,
        full_name=name,
        job_position="cook",
        is_active=active,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def make_schedule(client, db, restaurant, **overrides):
    employee = overrides.pop("employee", None) or make_employee(db, restaurant.id)
    response = client.post(
        f"{PREFIX}/",
        json={**PERIOD, "responsible_id": employee.id, **overrides},
    )
    assert response.status_code == status.HTTP_201_CREATED, response.text
    return response.json()


def schedule_payload(employee_id, start="2026-11-09", end="2026-11-15"):
    return {"period_start": start, "period_end": end, "responsible_id": employee_id}


def test_schedule_schema_valid_dates():
    today = date.today()
    next_week = today + timedelta(days=7)

    schedule_data = ScheduleCreate(
        period_start=today,
        period_end=next_week,
        responsible_id=1,
    )

    assert schedule_data.period_start == today
    assert schedule_data.period_end == next_week


def test_schedule_schema_invalid_dates_raises_value_error():
    from pydantic import ValidationError

    today = date.today()
    yesterday = today - timedelta(days=1)

    with pytest.raises(ValidationError) as exc_info:
        ScheduleCreate(
            period_start=today,
            period_end=yesterday,
            responsible_id=1,
        )

    assert (
        "La fecha de inicio del periodo no puede ser posterior a la fecha de fin."
        in str(exc_info.value)
    )


def test_create_schedule_success(client, db, restaurant):
    employee = make_employee(db, restaurant.id)
    today = date.today()
    next_week = today + timedelta(days=7)

    response = client.post(
        f"{PREFIX}/",
        json=schedule_payload(employee.id, today.isoformat(), next_week.isoformat()),
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == ScheduleStatus.BORRADOR.value
    assert data["period_start"] == today.isoformat()
    assert data["period_end"] == next_week.isoformat()
    assert data["responsible_id"] == employee.id
    assert data["published_at"] is None


def test_create_schedule_invalid_period_returns_422(client, db, restaurant):
    employee = make_employee(db, restaurant.id)
    today = date.today()
    yesterday = today - timedelta(days=1)

    response = client.post(
        f"{PREFIX}/",
        json=schedule_payload(employee.id, today.isoformat(), yesterday.isoformat()),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_schedules_returns_only_restaurant_schedules(client, db, restaurant):
    employee = make_employee(db, restaurant.id)
    first = client.post(
        f"{PREFIX}/", json=schedule_payload(employee.id, "2026-11-02", "2026-11-08")
    ).json()
    second = client.post(f"{PREFIX}/", json=schedule_payload(employee.id)).json()

    other = Restaurant(id=DEV_RESTAURANT_ID + 1, name="Otro", time_zone="Europe/Madrid")
    db.add(other)
    db.commit()
    other_employee = make_employee(db, other.id, name="Otra")
    db.add(
        Schedule(
            restaurant_id=other.id,
            period_start=date(2026, 11, 2),
            period_end=date(2026, 11, 8),
            responsible_id=other_employee.id,
            status="draft",
        )
    )
    db.commit()

    response = client.get(PREFIX)

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.json()] == [second["id"], first["id"]]


def test_get_schedule_detail_and_not_found(client, db, restaurant):
    schedule = make_schedule(client, db, restaurant)

    found = client.get(f"{PREFIX}/{schedule['id']}")
    missing = client.get(f"{PREFIX}/99999")

    assert found.status_code == status.HTTP_200_OK
    assert found.json()["id"] == schedule["id"]
    assert missing.status_code == status.HTTP_404_NOT_FOUND


def test_update_schedule_in_draft(client, db, restaurant):
    schedule = make_schedule(client, db, restaurant)
    new_responsible = make_employee(db, restaurant.id, name="Nuevo responsable")

    response = client.patch(
        f"{PREFIX}/{schedule['id']}",
        json={
            "period_start": "2026-11-16",
            "period_end": "2026-11-22",
            "responsible_id": new_responsible.id,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["period_start"] == "2026-11-16"
    assert data["period_end"] == "2026-11-22"
    assert data["responsible_id"] == new_responsible.id
    assert data["status"] == ScheduleStatus.BORRADOR.value


def test_update_schedule_with_invalid_merged_period_returns_422(client, db, restaurant):
    schedule = make_schedule(client, db, restaurant)

    response = client.patch(
        f"{PREFIX}/{schedule['id']}",
        json={"period_start": "2026-11-16"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["error"]["code"] == "SCHEDULE_INVALID_PERIOD"


def test_update_published_schedule_returns_409(client, db, restaurant):
    schedule = make_schedule(client, db, restaurant)
    client.patch(f"{PREFIX}/{schedule['id']}/publish")

    response = client.patch(
        f"{PREFIX}/{schedule['id']}",
        json={"period_end": "2026-11-20"},
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["error"]["code"] == "SCHEDULE_NOT_EDITABLE"


def test_delete_schedule_in_draft(client, db, restaurant):
    schedule = make_schedule(client, db, restaurant)

    response = client.delete(f"{PREFIX}/{schedule['id']}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert client.get(f"{PREFIX}/{schedule['id']}").status_code == 404


def test_delete_schedule_cascades_work_shifts(client, db, restaurant):
    schedule = make_schedule(client, db, restaurant)
    employee = make_employee(db, restaurant.id)
    shift = client.post(
        f"{PREFIX}/{schedule['id']}/shifts",
        json={
            "employee_id": employee.id,
            "starts_at": "2026-11-09T12:00:00+01:00",
            "ends_at": "2026-11-09T16:00:00+01:00",
        },
    )
    assert shift.status_code == status.HTTP_201_CREATED, shift.text

    assert client.delete(f"{PREFIX}/{schedule['id']}").status_code == 204
    assert client.get(f"{PREFIX}/{schedule['id']}/shifts").status_code == 404


def test_delete_published_schedule_returns_409(client, db, restaurant):
    schedule = make_schedule(client, db, restaurant)
    client.patch(f"{PREFIX}/{schedule['id']}/publish")

    response = client.delete(f"{PREFIX}/{schedule['id']}")

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["error"]["code"] == "SCHEDULE_NOT_EDITABLE"
    assert client.get(f"{PREFIX}/{schedule['id']}").status_code == 200


def test_publish_schedule_success(client, db, restaurant):
    schedule = make_schedule(client, db, restaurant)

    response = client.patch(f"{PREFIX}/{schedule['id']}/publish")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == ScheduleStatus.PUBLICADO.value
    assert data["published_at"] is not None
    assert data["responsible_id"] is not None


def test_publish_already_published_schedule_returns_409(client, db, restaurant):
    schedule = make_schedule(client, db, restaurant)
    client.patch(f"{PREFIX}/{schedule['id']}/publish")

    response = client.patch(f"{PREFIX}/{schedule['id']}/publish")

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["error"]["code"] == "SCHEDULE_ALREADY_PUBLISHED"


def test_get_nonexistent_schedule_returns_404(client):
    response = client.get(f"{PREFIX}/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


PROTECTED_REQUESTS = [
    ("GET", PREFIX, None),
    ("POST", f"{PREFIX}/", {**PERIOD, "responsible_id": 1}),
    ("GET", f"{PREFIX}/9999", None),
    ("PATCH", f"{PREFIX}/9999", {"period_end": "2026-11-20"}),
    ("DELETE", f"{PREFIX}/9999", None),
    ("PATCH", f"{PREFIX}/9999/publish", None),
]


@pytest.mark.parametrize("method,url,payload", PROTECTED_REQUESTS)
def test_endpoint_without_schedule_manage_returns_403(
    client, restaurant, user_without_permissions, method, url, payload
):
    response = client.request(method, url, json=payload)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["error"]["code"] == "FORBIDDEN"
