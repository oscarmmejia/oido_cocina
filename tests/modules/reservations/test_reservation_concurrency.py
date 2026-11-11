"""Prueba de concurrencia de duplicados por contacto (CA4)."""

import pytest

pytest.importorskip(
    "app.models.reservation_model",
    reason="Requiere el esquema compartido de HU-AUT-02",
)

import threading
from datetime import datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from app.core.database_connection import SessionLocal
from app.core.kernel.errors import AppError
from app.models import DiningTable, Reservation, Restaurant
from app.modules.reservations.repositories import reservation as reservation_repo
from app.modules.reservations.schemas.reservation import ReservationCreate
from app.modules.reservations.services.creation import create_reservation

TZ = ZoneInfo("Europe/Madrid")
START = datetime(2026, 1, 10, 20, 0, tzinfo=TZ)


def _table(db, restaurant, *, number: int) -> DiningTable:
    table = DiningTable(
        restaurant_id=restaurant.id,
        number=number,
        min_capacity=1,
        max_capacity=4,
        location="interior",
        is_active=True,
        adjustable_capacity=False,
    )
    db.add(table)
    db.flush()
    return table


def _payload(table_id: int, email: str) -> ReservationCreate:
    return ReservationCreate(
        customer_name="Cliente",
        phone="600000001",
        email=email,
        party_size=2,
        start_at=START,
        table_ids=[table_id],
    )


def test_concurrent_duplicate_with_different_tables_and_emails(
    db,
    restaurant,
    monkeypatch,
):
    restaurant.open_time = time(20, 0)
    restaurant.close_time = time(23, 0)
    restaurant.day_of_week = None
    restaurant.period = "afternoon"
    table_a = _table(db, restaurant, number=1)
    table_b = _table(db, restaurant, number=2)
    db.commit()

    restaurant_id = restaurant.id
    table_a_id = table_a.id
    table_b_id = table_b.id

    a_ready = threading.Event()
    b_started = threading.Event()
    release_a = threading.Event()
    results: list[tuple[str, object]] = []
    results_lock = threading.Lock()

    original_add_reservation = reservation_repo.add_reservation
    original_acquire_locks = reservation_repo.acquire_advisory_locks

    def delayed_add_reservation(db_session, reservation):
        if reservation.email == "a@example.com":
            a_ready.set()
            release_a.wait(timeout=10)
        return original_add_reservation(db_session, reservation)

    def tracking_acquire_locks(db_session, restaurant_id_arg, keys):
        if any("b@example.com" in key for key in keys):
            b_started.set()
        return original_acquire_locks(
            db_session,
            restaurant_id_arg,
            keys,
        )

    monkeypatch.setattr(
        reservation_repo,
        "add_reservation",
        delayed_add_reservation,
    )
    monkeypatch.setattr(
        reservation_repo,
        "acquire_advisory_locks",
        tracking_acquire_locks,
    )

    def run(email: str, table_id: int) -> None:
        session = SessionLocal()
        try:
            current_restaurant = session.get(Restaurant, restaurant_id)
            detail = create_reservation(
                session,
                current_restaurant,
                _payload(table_id, email),
            )
            with results_lock:
                results.append(("ok", detail.reservation.id))
        except AppError as error:
            with results_lock:
                results.append(("error", error.code))
        except Exception as error:
            with results_lock:
                results.append(("unexpected", repr(error)))
        finally:
            session.close()

    thread_a = threading.Thread(
        target=run,
        args=("a@example.com", table_a_id),
    )
    thread_b: threading.Thread | None = None
    try:
        thread_a.start()
        assert a_ready.wait(
            timeout=10
        ), "La primera petición no llegó a insertar"

        thread_b = threading.Thread(
            target=run,
            args=("b@example.com", table_b_id),
        )
        thread_b.start()
        assert b_started.wait(
            timeout=10
        ), "La segunda petición no intentó bloquear"
    finally:
        release_a.set()
        thread_a.join(timeout=20)
        if thread_b is not None:
            thread_b.join(timeout=20)

    assert not thread_a.is_alive()
    assert thread_b is not None
    assert not thread_b.is_alive()
    assert sum(1 for kind, _ in results if kind == "ok") == 1
    assert ("error", "DUPLICATE_RESERVATION") in results

    with SessionLocal() as session:
        assert (
            session.scalar(
                select(func.count())
                .select_from(Reservation)
                .where(Reservation.phone == "600000001")
            )
            == 1
        )
