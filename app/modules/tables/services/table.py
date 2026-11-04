from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.shared.models.restaurant import DEMO_RESTAURANT_NAME, Restaurant
from app.modules.tables.models.table import DiningTable
from app.modules.tables.schemas.table import TableCreate, TableUpdate

UNIQUE_NUMBER_CONSTRAINT = "uq_table_restaurant_number"


def _number_taken() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "code": "TABLE_NUMBER_TAKEN",
            "message": "Ya existe una mesa con ese número",
        },
    )


def _is_duplicate_number(error: IntegrityError) -> bool:
    """Solo el índice único de número es un 409; otra violación se propaga."""
    diag = getattr(error.orig, "diag", None)
    return getattr(diag, "constraint_name", None) == UNIQUE_NUMBER_CONSTRAINT


def resolve_restaurant_id(db: Session, requested: int | None) -> int:
    """TEMPORAL: sin autenticación, todo cuelga del restaurante sembrado."""
    if requested is not None:
        if db.scalar(select(Restaurant.id).where(Restaurant.id == requested)) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "RESTAURANT_NOT_FOUND", "message": "No existe el restaurante"},
            )
        return requested

    demo_id = db.scalar(
        select(Restaurant.id).where(Restaurant.name == DEMO_RESTAURANT_NAME)
    )
    if demo_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "BOOTSTRAP_MISSING",
                "message": "Falta ejecutar app.database.bootstrap",
            },
        )
    return demo_id


def list_tables(db: Session, restaurant_id: int) -> list[DiningTable]:
    return list(
        db.scalars(
            select(DiningTable)
            .where(DiningTable.restaurant_id == restaurant_id)
            .order_by(DiningTable.number)
        )
    )


def create_table(db: Session, payload: TableCreate) -> DiningTable:
    restaurant_id = resolve_restaurant_id(db, payload.restaurant_id)
    data = payload.model_dump(exclude={"restaurant_id"}, mode="json")
    table = DiningTable(restaurant_id=restaurant_id, **data)
    db.add(table)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if _is_duplicate_number(error):
            raise _number_taken() from error
        raise

    db.refresh(table)
    return table


def get_table(db: Session, table_id: int, restaurant_id: int) -> DiningTable:
    table = db.get(DiningTable, table_id)
    if table is None or table.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TABLE_NOT_FOUND", "message": "No existe la mesa"},
        )
    return table


def update_table(
    db: Session, table_id: int, restaurant_id: int, payload: TableUpdate
) -> DiningTable:
    table = get_table(db, table_id, restaurant_id)
    changes = payload.model_dump(exclude_unset=True, mode="json")

    # La validación cruzada no puede vivir en Pydantic: el payload es parcial y el rango
    # válido depende de la fila guardada.
    min_capacity = changes.get("min_capacity", table.min_capacity)
    max_capacity = changes.get("max_capacity", table.max_capacity)
    if max_capacity < min_capacity:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=[
                {
                    "loc": ["body", "max_capacity"],
                    "msg": "max_capacity no puede ser menor que min_capacity",
                    "type": "value_error",
                }
            ],
        )

    for field, value in changes.items():
        setattr(table, field, value)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if _is_duplicate_number(error):
            raise _number_taken() from error
        raise

    db.refresh(table)
    return table
