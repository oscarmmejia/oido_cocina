import pytest

from app.core.kernel.identity import DEV_RESTAURANT_ID, CurrentUser, get_current_user
from app.main import app

VALID_TABLE = {
    "number": 5,
    "min_capacity": 2,
    "max_capacity": 4,
    "location": "interior",
}

PROTECTED_REQUESTS = [
    ("GET", "/api/v1/tables", None),
    ("POST", "/api/v1/tables", VALID_TABLE),
    ("GET", "/api/v1/tables/9999", None),
    ("PATCH", "/api/v1/tables/9999", {"number": 7}),
    ("POST", "/api/v1/tables/9999/enable", None),
    ("POST", "/api/v1/tables/9999/disable", None),
]


@pytest.fixture
def user_without_permissions():
    def override() -> CurrentUser:
        return CurrentUser(
            id=2,
            restaurant_id=DEV_RESTAURANT_ID,
            email="sin-permisos@example.com",
            role="viewer",
            permissions=set(),
        )

    app.dependency_overrides[get_current_user] = override
    yield
    app.dependency_overrides.pop(get_current_user, None)


def create_table(client, payload=None):
    return client.post("/api/v1/tables", json=payload or VALID_TABLE)


def list_tables(client):
    return client.get("/api/v1/tables")


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


def test_create_table_with_bar_location_returns_201(client, restaurant):
    response = create_table(client, {**VALID_TABLE, "location": "bar"})

    assert response.status_code == 201
    assert response.json()["location"] == "bar"


def test_update_table_to_bar_location_returns_200(client, restaurant):
    table_id = create_table(client).json()["id"]

    response = client.patch(f"/api/v1/tables/{table_id}", json={"location": "bar"})

    assert response.status_code == 200
    assert response.json()["location"] == "bar"


def test_create_duplicate_number_in_same_restaurant_returns_409(client, restaurant):
    assert create_table(client).status_code == 201

    response = create_table(client, {**VALID_TABLE, "min_capacity": 1, "max_capacity": 1})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TABLE_NUMBER_TAKEN"


def test_list_tables_returns_created_tables(client, restaurant):
    create_table(client)

    response = list_tables(client)

    assert response.status_code == 200
    assert [table["number"] for table in response.json()] == [VALID_TABLE["number"]]


def test_get_table_returns_200(client, restaurant):
    created = create_table(client).json()

    response = client.get(f"/api/v1/tables/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["number"] == VALID_TABLE["number"]
    assert body["restaurant_id"] == restaurant.id


def test_get_missing_table_returns_404(client, restaurant):
    response = client.get("/api/v1/tables/9999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TABLE_NOT_FOUND"


@pytest.mark.parametrize("method,url,payload", PROTECTED_REQUESTS)
def test_endpoint_without_table_manage_returns_403(
    client, restaurant, user_without_permissions, method, url, payload
):
    response = client.request(method, url, json=payload)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_update_table_returns_200(client, restaurant):
    table_id = create_table(client).json()["id"]

    response = client.patch(
        f"/api/v1/tables/{table_id}",
        json={"min_capacity": 3, "max_capacity": 6, "adjustable_capacity": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["min_capacity"] == 3
    assert body["max_capacity"] == 6
    assert body["adjustable_capacity"] is True


def test_update_missing_table_returns_404(client, restaurant):
    response = client.patch("/api/v1/tables/9999", json={"number": 7})

    assert response.status_code == 404


def test_update_capacity_outside_saved_range_returns_422(client, restaurant):
    table_id = create_table(client).json()["id"]

    response = client.patch(f"/api/v1/tables/{table_id}", json={"min_capacity": 10})

    assert response.status_code == 422


def test_update_to_existing_number_returns_409(client, restaurant):
    create_table(client, {**VALID_TABLE, "number": 1})
    second_id = create_table(client, {**VALID_TABLE, "number": 2}).json()["id"]

    response = client.patch(f"/api/v1/tables/{second_id}", json={"number": 1})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TABLE_NUMBER_TAKEN"


def test_create_table_with_equal_capacities_returns_201(client, restaurant):
    response = create_table(client, {**VALID_TABLE, "min_capacity": 4, "max_capacity": 4})

    assert response.status_code == 201


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

    response = client.patch(f"/api/v1/tables/{table_id}", json=body)

    assert response.status_code == 422


def test_update_with_invalid_location_returns_422(client, restaurant):
    table_id = create_table(client).json()["id"]

    response = client.patch(f"/api/v1/tables/{table_id}", json={"location": "terraza"})

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


def change_table_status(client, table_id, action):
    return client.post(f"/api/v1/tables/{table_id}/{action}")


def test_disable_table_returns_200_and_deactivates(client, restaurant):
    table_id = create_table(client).json()["id"]

    response = change_table_status(client, table_id, "disable")

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert list_tables(client).json()[0]["is_active"] is False


def test_enable_table_returns_200_and_reactivates(client, restaurant):
    table_id = create_table(client).json()["id"]
    assert change_table_status(client, table_id, "disable").status_code == 200

    response = change_table_status(client, table_id, "enable")

    assert response.status_code == 200
    assert response.json()["is_active"] is True
    assert list_tables(client).json()[0]["is_active"] is True


@pytest.mark.parametrize("action", ["enable", "disable"])
def test_repeated_status_change_is_idempotent(client, restaurant, action):
    table_id = create_table(client).json()["id"]

    first = change_table_status(client, table_id, action)
    second = change_table_status(client, table_id, action)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["is_active"] == second.json()["is_active"]


@pytest.mark.parametrize("action", ["enable", "disable"])
def test_status_change_missing_table_returns_404(client, restaurant, action):
    response = change_table_status(client, 9999, action)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TABLE_NOT_FOUND"
