from app.models import Restaurant


def test_create_restaurant(session):
    restaurant = Restaurant(
        name="Mi restaurante",
        timezone="Europe/Madrid",
        is_active=True,
    )

    session.add(restaurant)
    session.flush()

    assert restaurant.id is not None
    assert restaurant.name == "Mi restaurante"
    assert restaurant.timezone == "Europe/Madrid"
    assert restaurant.is_active is True