from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.main import app
from app.models.employee import Employee
from app.modules.schedules.models.schedule import Schedule
from app.modules.settings.models.restaurant import Restaurant

MADRID = ZoneInfo("Europe/Madrid")
PREFIX = "/api/v1/schedules"
PERIOD = {"period_start": "2026-11-09", "period_end": "2026-11-15", "responsible_id": 1}


def make_employee(db, *, active=True, name="Ana", restaurant_id=1):
    emp = Employee(
        restaurant_id=restaurant_id, full_name=name, job_position="waiter", is_active=active
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


def make_schedule(client, **overrides):
    response = client.post(f"{PREFIX}/", json={**PERIOD, **overrides})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def local(day, hour, minute=0, next_day=False):
    d = date.fromisoformat(day)
    return datetime(d.year, d.month, d.day + (1 if next_day else 0), hour, minute, tzinfo=MADRID)


def shift_body(employee_id, start, end, shift_type=None):
    body = {
        "employee_id": employee_id,
        "starts_at": start.isoformat(),
        "ends_at": end.isoformat(),
    }
    if shift_type is not None:
        body["type"] = shift_type
    return body


def add_shift(client, schedule_id, employee_id, start, end, shift_type=None):
    return client.post(
        f"{PREFIX}/{schedule_id}/shifts",
        json=shift_body(employee_id, start, end, shift_type),
    )


def test_turno_nocturno_que_cruza_medianoche(client, db, restaurant):
    emp = make_employee(db)
    schedule_id = make_schedule(client)

    r = add_shift(
        client,
        schedule_id,
        emp.id,
        local("2026-11-09", 22),
        local("2026-11-09", 2, next_day=True),
        "night",
    )

    assert r.status_code == 201, r.text
    data = r.json()
    assert data["schedule_id"] == schedule_id
    assert data["type"] == "night"
    assert data["status"] == "scheduled"


def test_solape_devuelve_409(client, db, restaurant):
    emp = make_employee(db)
    schedule_id = make_schedule(client)
    add_shift(client, schedule_id, emp.id, local("2026-11-09", 12), local("2026-11-09", 16))

    r = add_shift(client, schedule_id, emp.id, local("2026-11-09", 15), local("2026-11-09", 18))

    assert r.status_code == 409
    assert r.json()["error"]["code"] == "SHIFT_OVERLAP"


def test_turno_partido_respeta_descanso_minimo_del_restaurante(client, db, restaurant):
    restaurant.min_break_between_shifts = 60
    db.commit()
    emp = make_employee(db)
    schedule_id = make_schedule(client)
    add_shift(client, schedule_id, emp.id, local("2026-11-09", 12), local("2026-11-09", 15))

    ok = add_shift(client, schedule_id, emp.id, local("2026-11-09", 19), local("2026-11-09", 23))
    assert ok.status_code == 201, ok.text

    corto = add_shift(client, schedule_id, emp.id, local("2026-11-09", 15, 30), local("2026-11-09", 17))
    assert corto.status_code == 409
    assert corto.json()["error"]["code"] == "SHIFT_BREAK_TOO_SHORT"


def test_turno_fuera_del_periodo_devuelve_422(client, db, restaurant):
    emp = make_employee(db)
    schedule_id = make_schedule(client)

    r = add_shift(client, schedule_id, emp.id, local("2026-11-16", 12), local("2026-11-16", 16))

    assert r.status_code == 422
    assert r.json()["error"]["code"] == "SHIFT_OUTSIDE_PERIOD"


def test_fechas_sin_zona_horaria_se_rechazan(client, db, restaurant):
    emp = make_employee(db)
    schedule_id = make_schedule(client)

    r = client.post(
        f"{PREFIX}/{schedule_id}/shifts",
        json={"employee_id": emp.id, "starts_at": "2026-11-09T12:00:00", "ends_at": "2026-11-09T16:00:00"},
    )

    assert r.status_code == 422


def test_empleado_inactivo_no_puede_recibir_turnos(client, db, restaurant):
    emp = make_employee(db, active=False)
    schedule_id = make_schedule(client)

    r = add_shift(client, schedule_id, emp.id, local("2026-11-09", 12), local("2026-11-09", 16))

    assert r.status_code == 422
    assert r.json()["error"]["code"] == "EMPLOYEE_INACTIVE"


def test_cuadrante_publicado_es_inmutable(client, db, restaurant):
    emp = make_employee(db)
    schedule_id = make_schedule(client)
    client.patch(f"{PREFIX}/{schedule_id}/publish")

    r = add_shift(client, schedule_id, emp.id, local("2026-11-09", 12), local("2026-11-09", 16))

    assert r.status_code == 409
    assert r.json()["error"]["code"] == "SCHEDULE_NOT_EDITABLE"


def test_listar_filtra_por_empleado_y_fechas(client, db, restaurant):
    ana = make_employee(db, name="Ana")
    luis = make_employee(db, name="Luis")
    schedule_id = make_schedule(client)
    add_shift(client, schedule_id, ana.id, local("2026-11-09", 12), local("2026-11-09", 16))
    add_shift(client, schedule_id, luis.id, local("2026-11-10", 12), local("2026-11-10", 16))
    add_shift(client, schedule_id, ana.id, local("2026-11-11", 12), local("2026-11-11", 16))

    por_empleado = client.get(f"{PREFIX}/{schedule_id}/shifts", params={"employee_id": ana.id})
    assert len(por_empleado.json()) == 2

    por_fecha = client.get(
        f"{PREFIX}/{schedule_id}/shifts",
        params={"date_from": "2026-11-10", "date_to": "2026-11-10"},
    )
    assert [s["employee_id"] for s in por_fecha.json()] == [luis.id]


def test_eliminar_turno_en_borrador(client, db, restaurant):
    emp = make_employee(db)
    schedule_id = make_schedule(client)
    shift_id = add_shift(client, schedule_id, emp.id, local("2026-11-09", 12), local("2026-11-09", 16)).json()["id"]

    r = client.delete(f"{PREFIX}/{schedule_id}/shifts/{shift_id}")

    assert r.status_code == 204
    assert client.get(f"{PREFIX}/{schedule_id}/shifts").json() == []


def test_jornada_partida_suma_sus_intervalos(client, db, restaurant):
    emp = make_employee(db)
    schedule_id = make_schedule(client)

    manana = add_shift(
        client, schedule_id, emp.id, local("2026-11-09", 12), local("2026-11-09", 16), "morning"
    )
    tarde = add_shift(
        client, schedule_id, emp.id, local("2026-11-09", 20), local("2026-11-09", 23), "afternoon"
    )

    assert manana.status_code == 201, manana.text
    assert tarde.status_code == 201, tarde.text
    shifts = client.get(f"{PREFIX}/{schedule_id}/shifts").json()
    total_hours = sum(
        (
            datetime.fromisoformat(shift["ends_at"])
            - datetime.fromisoformat(shift["starts_at"])
        ).total_seconds()
        for shift in shifts
    ) / 3600
    assert len(shifts) == 2
    assert total_hours == 7


def test_actualizar_turno_en_borrador(client, db, restaurant):
    emp = make_employee(db)
    schedule_id = make_schedule(client)
    shift = add_shift(
        client, schedule_id, emp.id, local("2026-11-09", 12), local("2026-11-09", 16)
    ).json()

    response = client.patch(
        f"{PREFIX}/{schedule_id}/shifts/{shift['id']}",
        json={
            "starts_at": local("2026-11-09", 13).isoformat(),
            "ends_at": local("2026-11-09", 17).isoformat(),
            "type": "afternoon",
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["starts_at"] == local("2026-11-09", 13).isoformat()
    assert data["ends_at"] == local("2026-11-09", 17).isoformat()
    assert data["type"] == "afternoon"


def test_actualizar_turno_no_se_solapa_consigo_mismo(client, db, restaurant):
    emp = make_employee(db)
    schedule_id = make_schedule(client)
    shift = add_shift(
        client, schedule_id, emp.id, local("2026-11-09", 12), local("2026-11-09", 16)
    ).json()

    response = client.patch(
        f"{PREFIX}/{schedule_id}/shifts/{shift['id']}",
        json={"type": "split"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["type"] == "split"


def test_actualizar_turno_publicado_returns_409(client, db, restaurant):
    emp = make_employee(db)
    schedule_id = make_schedule(client)
    shift = add_shift(
        client, schedule_id, emp.id, local("2026-11-09", 12), local("2026-11-09", 16)
    ).json()
    client.patch(f"{PREFIX}/{schedule_id}/publish")

    response = client.patch(
        f"{PREFIX}/{schedule_id}/shifts/{shift['id']}",
        json={"type": "afternoon"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SCHEDULE_NOT_EDITABLE"


def test_actualizar_turno_con_empleado_inactivo_returns_422(client, db, restaurant):
    emp = make_employee(db)
    schedule_id = make_schedule(client)
    shift = add_shift(
        client, schedule_id, emp.id, local("2026-11-09", 12), local("2026-11-09", 16)
    ).json()
    emp.is_active = False
    db.commit()

    response = client.patch(
        f"{PREFIX}/{schedule_id}/shifts/{shift['id']}",
        json={"type": "afternoon"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "EMPLOYEE_INACTIVE"


def test_actualizar_turno_fuera_del_periodo_returns_422(client, db, restaurant):
    emp = make_employee(db)
    schedule_id = make_schedule(client)
    shift = add_shift(
        client, schedule_id, emp.id, local("2026-11-09", 12), local("2026-11-09", 16)
    ).json()

    response = client.patch(
        f"{PREFIX}/{schedule_id}/shifts/{shift['id']}",
        json={
            "starts_at": local("2026-11-16", 12).isoformat(),
            "ends_at": local("2026-11-16", 16).isoformat(),
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SHIFT_OUTSIDE_PERIOD"


def test_eliminar_turno_en_publicado_returns_409(client, db, restaurant):
    emp = make_employee(db)
    schedule_id = make_schedule(client)
    shift = add_shift(
        client, schedule_id, emp.id, local("2026-11-09", 12), local("2026-11-09", 16)
    ).json()
    client.patch(f"{PREFIX}/{schedule_id}/publish")

    response = client.delete(f"{PREFIX}/{schedule_id}/shifts/{shift['id']}")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SCHEDULE_NOT_EDITABLE"


def test_cuadrante_de_otro_restaurante_no_es_visible(client, db, restaurant):
    db.add(Restaurant(id=2, name="Otro", time_zone="Europe/Madrid"))
    db.commit()
    otro_emp = make_employee(db, restaurant_id=2)
    otro = Schedule(
        restaurant_id=2,
        period_start=date(2026, 11, 9),
        period_end=date(2026, 11, 15),
        responsible_id=otro_emp.id,
        status="draft",
    )
    db.add(otro)
    db.commit()
    db.refresh(otro)

    assert client.get(f"{PREFIX}/{otro.id}").status_code == 404
    assert client.get(f"{PREFIX}/{otro.id}/shifts").status_code == 404


def test_swagger_documenta_los_parametros():
    spec = app.openapi()
    params = spec["paths"]["/api/v1/schedules/{schedule_id}/shifts"]["get"]["parameters"]
    by_name = {p["name"]: p for p in params}

    assert set(by_name) == {"schedule_id", "employee_id", "date_from", "date_to"}
    assert by_name["schedule_id"]["in"] == "path"
    assert by_name["employee_id"]["in"] == "query"
    assert by_name["employee_id"]["description"]
    date_options = by_name["date_from"]["schema"]["anyOf"]
    assert {"type": "string", "format": "date"} in date_options
    assert "409" in spec["paths"]["/api/v1/schedules/{schedule_id}/shifts"]["post"]["responses"]
    assert "422" in spec["paths"]["/api/v1/schedules/{schedule_id}/shifts"]["post"]["responses"]


PROTECTED_SHIFT_REQUESTS = [
    (
        "POST",
        f"{PREFIX}/1/shifts",
        {
            "employee_id": 1,
            "starts_at": "2026-11-09T12:00:00+01:00",
            "ends_at": "2026-11-09T16:00:00+01:00",
        },
    ),
    ("GET", f"{PREFIX}/1/shifts", None),
    ("PATCH", f"{PREFIX}/1/shifts/1", {"type": "afternoon"}),
    ("DELETE", f"{PREFIX}/1/shifts/1", None),
]


@pytest.mark.parametrize("method,url,payload", PROTECTED_SHIFT_REQUESTS)
def test_endpoint_without_schedule_manage_returns_403(
    client, restaurant, user_without_permissions, method, url, payload
):
    response = client.request(method, url, json=payload)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
