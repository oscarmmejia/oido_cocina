from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.seeders._helpers import insert_if_missing
from app.models import OpeningHours, Restaurant, RestaurantSettings

DEMO_RESTAURANT_NAME = "Oído Cocina Demo"
DEMO_TIMEZONE = "Europe/Madrid"

# Demo values only. Real restaurants configure their own through the settings module.
DEMO_SETTINGS = {
    "courtesy_minutes": 5,
    "slot_minutes": 60,
    "default_reservation_minutes": 60,
    "min_break_between_shifts": 720,  # minutes; demo value, to be validated against the labour agreement
}

# (period, open, close, kitchen close). Periods follow the briefing: morning/afternoon.
DEMO_PERIODS = [
    ("morning", time(13, 0), time(16, 0), time(15, 30)),
    ("afternoon", time(20, 0), time(23, 30), time(23, 0)),
]
WEEK_DAYS = range(1, 8)  # 1=Monday .. 7=Sunday


def seed_demo_restaurant(session: Session) -> tuple[int, dict[str, int]]:
    """Create the demo restaurant, its settings and its opening hours if missing.

    Returns the restaurant id and how many rows were inserted per table.
    """
    inserted = {"restaurants": 0, "restaurant_settings": 0, "opening_hours": 0}

    restaurant_id = session.scalar(
        select(Restaurant.id).where(Restaurant.name == DEMO_RESTAURANT_NAME)
    )
    if restaurant_id is None:
        restaurant = Restaurant(name=DEMO_RESTAURANT_NAME, timezone=DEMO_TIMEZONE)
        session.add(restaurant)
        session.flush()
        restaurant_id = restaurant.id
        inserted["restaurants"] = 1

    inserted["restaurant_settings"] = insert_if_missing(
        session,
        RestaurantSettings,
        [{"restaurant_id": restaurant_id, **DEMO_SETTINGS}],
        natural_key=["restaurant_id"],
    )

    hours = [
        {
            "restaurant_id": restaurant_id,
            "day_of_week": day,
            "period": period,
            "open_time": open_time,
            "close_time": close_time,
            "kitchen_close_time": kitchen_close_time,
        }
        for day in WEEK_DAYS
        for period, open_time, close_time, kitchen_close_time in DEMO_PERIODS
    ]
    inserted["opening_hours"] = insert_if_missing(
        session, OpeningHours, hours, natural_key=["restaurant_id", "day_of_week", "period"]
    )
    return restaurant_id, inserted
