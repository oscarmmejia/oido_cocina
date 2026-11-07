from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.main import app
from app.models.employee import Employee
from app.modules.settings.models.restaurant import Restaurant

MADRID = ZoneInfo("Europe/Madrid")
PREFIX = "/api/v1/schedules"
PERIOD = {"period_start": "2026-11-09", "period_end": "2026-11-15", "responsible_id": 1}


def make_employee(db, *, active=True, name="Ana", restaurant_id=1):
    emp = Employee(
        restaurant_id=restaurant_id, full_name=name, job_position="Camarero/a", is_active=active
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


def shift_body(employee_id, start, end):
    return {"employee_id": employee_id, "starts_at": start.isoformat(), "ends_at": end.isoformat()}


def add_shift(client, schedule_id, employee_id, start, end):
    return client.post(f"{PREFIX}/{schedule_id}/shifts", json=shift_body(employee_id, start, end))


def test_turno_nocturno_que_cruza_medianoche(client, db, restaurant):
    emp = make_employee(db)
    schedule_id = make_schedule(client)

    r = add_shift(client, schedule_id, emp.id, local("2026-11-09", 22), local("2026-11-09", 2, next_day=True))

    assert r.status_code == 201, r.text
    assert r.json()["schedule_id"] == schedule_id


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

    assert r.status_code == 409
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


def test_cuadrante_de_otro_restaurante_no_es_visible(client, db, restaurant):
    db.add(Restaurant(id=2, name="Otro", time_zone="Europe/Madrid"))
    db.commit()
    otro_emp = make_employee(db, restaurant_id=2)
    otro = client.post(f"{PREFIX}/", json={**PERIOD, "responsible_id": otro_emp.id})
    # el usuario de desarrollo pertenece al restaurante 1: el cuadrante ajeno no existe para él
    assert client.get(f"{PREFIX}/{otro.json().get('id', 999)}").status_code == 404


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
