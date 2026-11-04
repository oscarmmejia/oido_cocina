import pytest
from sqlalchemy.orm import Session

from app.modules.shared.models.restaurant import Restaurant

PERMISSION_HEADER = "X-Dev-Permissions"
TABLE_MANAGE = {PERMISSION_HEADER: "table:manage"}
NO_TABLE_MANAGE = {PERMISSION_HEADER: "reservation:manage"}

VALID_TABLE = {
    "number": 5,
    "min_capacity": 2,
    "max_capacity": 4,
    "location": "interior",
}


def create_table(client, payload=None, headers=TABLE_MANAGE):
    return client.post("/api/v1/tables", json=payload or VALID_TABLE, headers=headers)


def test_create_table_returns_201(client, restaurant):
    response = create_table(client)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] is not None
    assert body["number"] == VALID_TABLE["number"]
    assert body["restaurant_id"] == restaurant.id
    assert body["is_active"] is True
    assert body["adjustable_capacity"] is False


def test_create_table_with_max_below_min_returns_422(client, restaurant):
    response = create_table(client, {**VALID_TABLE, "min_capacity": 4, "max_capacity": 2})

    assert response.status_code == 422


def test_create_table_with_invalid_location_returns_422(client, restaurant):
    response = create_table(client, {**VALID_TABLE, "location": "terraza"})

    assert response.status_code == 422


def test_create_duplicate_number_in_same_restaurant_returns_409(client, restaurant):
    assert create_table(client).status_code == 201

    response = create_table(client, {**VALID_TABLE, "min_capacity": 1, "max_capacity": 1})

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "TABLE_NUMBER_TAKEN"


def test_same_number_in_another_restaurant_returns_201(client, db: Session, restaurant):
    other = Restaurant(name="Otra Sucursal")
    db.add(other)
    db.commit()
    db.refresh(other)

    assert create_table(client).status_code == 201

    response = create_table(client, {**VALID_TABLE, "restaurant_id": other.id})

    assert response.status_code == 201
    assert response.json()["restaurant_id"] == other.id


def test_list_tables_without_permission_returns_403(client, restaurant):
    response = client.get(
        "/api/v1/tables", headers={PERMISSION_HEADER: "reservation:manage"}
    )

    assert response.status_code == 403


def test_list_tables_returns_created_tables(client, restaurant):
    create_table(client)

    response = client.get("/api/v1/tables", headers=TABLE_MANAGE)

    assert response.status_code == 200
    assert [table["number"] for table in response.json()] == [VALID_TABLE["number"]]


def test_update_table_returns_200(client, restaurant):
    table_id = create_table(client).json()["id"]

    response = client.patch(
        f"/api/v1/tables/{table_id}",
        json={"min_capacity": 3, "max_capacity": 6, "adjustable_capacity": True},
        headers=TABLE_MANAGE,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["min_capacity"] == 3
    assert body["max_capacity"] == 6
    assert body["adjustable_capacity"] is True


def test_update_missing_table_returns_404(client, restaurant):
    response = client.patch(
        "/api/v1/tables/9999", json={"number": 7}, headers=TABLE_MANAGE
    )

    assert response.status_code == 404


def test_update_capacity_outside_saved_range_returns_422(client, restaurant):
    table_id = create_table(client).json()["id"]

    response = client.patch(
        f"/api/v1/tables/{table_id}", json={"min_capacity": 10}, headers=TABLE_MANAGE
    )

    assert response.status_code == 422


def test_update_to_existing_number_returns_409(client, restaurant):
    create_table(client, {**VALID_TABLE, "number": 1})
    second_id = create_table(client, {**VALID_TABLE, "number": 2}).json()["id"]

    response = client.patch(
        f"/api/v1/tables/{second_id}", json={"number": 1}, headers=TABLE_MANAGE
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "TABLE_NUMBER_TAKEN"

def list_tables(client):
    return client.get("/api/v1/tables", headers=TABLE_MANAGE)


def test_create_table_with_equal_capacities_returns_201(client, restaurant):
    response = create_table(client, {**VALID_TABLE, "min_capacity": 4, "max_capacity": 4})

    assert response.status_code == 201


def test_create_table_without_permission_returns_403(client, restaurant):
    response = create_table(client, headers=NO_TABLE_MANAGE)

    assert response.status_code == 403
    assert list_tables(client).json() == []


def test_update_table_without_permission_returns_403(client, restaurant):
    table_id = create_table(client).json()["id"]

    response = client.patch(
        f"/api/v1/tables/{table_id}", json={"number": 9}, headers=NO_TABLE_MANAGE
    )

    assert response.status_code == 403
    assert list_tables(client).json()[0]["number"] == VALID_TABLE["number"]


@pytest.mark.parametrize(
    "body",
    [
        {"number": None},
        {"min_capacity": None},
        {"max_capacity": None},
        {"location": None},
        {"is_active": None},
        {"adjustable_capacity": None},
    ],
)
def test_update_with_explicit_null_returns_422(client, restaurant, body):
    table_id = create_table(client).json()["id"]

    response = client.patch(f"/api/v1/tables/{table_id}", json=body, headers=TABLE_MANAGE)

    assert response.status_code == 422


def test_update_with_invalid_location_returns_422(client, restaurant):
    table_id = create_table(client).json()["id"]

    response = client.patch(
        f"/api/v1/tables/{table_id}", json={"location": "terraza"}, headers=TABLE_MANAGE
    )

    assert response.status_code == 422


def test_rejected_create_is_not_persisted(client, restaurant):
    response = create_table(client, {**VALID_TABLE, "min_capacity": 4, "max_capacity": 2})

    assert response.status_code == 422
    assert list_tables(client).json() == []


def test_rejected_duplicate_is_not_persisted(client, restaurant):
    create_table(client)

    response = create_table(client, {**VALID_TABLE, "min_capacity": 1, "max_capacity": 1})

    assert response.status_code == 409
    assert [table["number"] for table in list_tables(client).json()] == [
        VALID_TABLE["number"]
    ]


def test_bootstrap_is_idempotent(db: Session):
    from app.database.bootstrap import bootstrap

    bootstrap()
    bootstrap()

    demo = db.query(Restaurant).filter(Restaurant.name == "Demo").all()
    assert len(demo) == 1
