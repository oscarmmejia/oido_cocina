from concurrent.futures import ThreadPoolExecutor
from datetime import time
from threading import Event
from time import monotonic, sleep

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database_connection import engine
from app.core.kernel.errors import AppError
from app.models import Restaurant
from app.modules.settings.schemas import RestaurantSettingsUpdate
from app.modules.settings.services.restaurant_service import update_restaurant_settings


def test_concurrent_updates_revalidate_latest_settings_before_writing(db):
    assert engine.url.database == "oido_cocina_test"
    assert engine.url.host in ("localhost", "127.0.0.1")

    restaurant = Restaurant(
        name="Concurrencia de settings",
        time_zone="Europe/Madrid",
        open_time=time(12),
        kitchen_close_time=time(22),
        close_time=time(23),
    )
    db.add(restaurant)
    db.flush()
    restaurant_id = restaurant.id
    db.commit()

    snapshot_loaded = Event()
    first_locked = Event()
    second_started = Event()
    release_first = Event()
    backend_pids = {}

    def update_closing():
        with Session(bind=engine, autoflush=False) as session:
            assert snapshot_loaded.wait(5)
            backend_pids["first"] = session.scalar(text("SELECT pg_backend_pid()"))
            session.get(Restaurant, restaurant_id, with_for_update=True)
            first_locked.set()
            assert release_first.wait(10)
            update_restaurant_settings(
                session, restaurant_id, RestaurantSettingsUpdate(close_time=time(22, 30))
            )

    def update_kitchen():
        with Session(bind=engine, autoflush=False) as session:
            session.execute(text("SET LOCAL lock_timeout = '10s'"))
            backend_pids["second"] = session.scalar(text("SELECT pg_backend_pid()"))
            cached = session.get(Restaurant, restaurant_id)
            assert cached.close_time == time(23)
            snapshot_loaded.set()
            assert first_locked.wait(5)
            second_started.set()
            try:
                update_restaurant_settings(
                    session,
                    restaurant_id,
                    RestaurantSettingsUpdate(
                        kitchen_close_time=time(22, 45), slot_minutes=30
                    ),
                )
            except AppError as error:
                assert cached.close_time == time(22, 30)
                assert cached.kitchen_close_time == time(22)
                assert cached.slot_minutes == 60
                assert cached not in session.dirty
                return error.status_code, error.code
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(update_closing)
        second = executor.submit(update_kitchen)
        try:
            assert first_locked.wait(5)
            assert second_started.wait(5)
            deadline = monotonic() + 5
            blocked = False
            with engine.connect() as observer:
                while monotonic() < deadline:
                    blocked = observer.scalar(
                        text("SELECT :first = ANY(pg_blocking_pids(:second))"),
                        backend_pids,
                    )
                    if blocked:
                        break
                    sleep(0.02)
            assert blocked, "La segunda transacción debe esperar a la primera"
        finally:
            release_first.set()
        first.result(timeout=10)
        assert second.result(timeout=10) == (422, "VALIDATION_ERROR")

    with Session(bind=engine) as reader:
        stored = reader.get(Restaurant, restaurant_id)
        assert stored.close_time == time(22, 30)
        assert stored.kitchen_close_time == time(22)
        assert stored.slot_minutes == 60
