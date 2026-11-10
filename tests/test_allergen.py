from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database_connection import Base
from app.database.seeders.catalog import seed_allergens, EU_ALLERGENS
from app.models.allergen_model import Allergen
from app.controllers.allergen_controller import get_all_allergens
from app.api.allergen_routes import list_allergens


def test_seed_allergens_creates_exactly_14_items():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()

    try:
        result = seed_allergens(session)
        assert len(result) == 14
        assert session.query(Allergen).count() == 14

        seeded_codes = {a.code for a in session.query(Allergen).all()}
        expected_codes = {item["code"] for item in EU_ALLERGENS}
        assert seeded_codes == expected_codes

        second_run = seed_allergens(session)
        assert len(second_run) == 14
        assert session.query(Allergen).count() == 14
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_get_all_allergens_controller():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()

    try:
        seed_allergens(session)
        allergens = get_all_allergens(session)

        assert len(allergens) == 14
        assert allergens[0].code == "GLUTEN"
        assert allergens[0].name == "Cereales que contienen gluten"
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_list_allergens_route_handler():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()

    try:
        seed_allergens(session)
        response = list_allergens(db=session)

        assert len(response) == 14
        assert response[0].code == "GLUTEN"
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
