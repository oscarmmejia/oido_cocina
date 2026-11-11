from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.kernel.errors import AppError
from app.models import DiningTable
from app.modules.tables.schemas.table import TableCreate, TableUpdate

UNIQUE_NUMBER_CONSTRAINT = "uq_table_restaurant_number"


def _number_taken() -> AppError:
    return AppError("TABLE_NUMBER_TAKEN", "Ya existe una mesa con ese número", 409)


def _is_duplicate_number(error: IntegrityError) -> bool:
    """Solo el índice único de número es un 409; otra violación se propaga."""
    diag = getattr(error.orig, "diag", None)
    return getattr(diag, "constraint_name", None) == UNIQUE_NUMBER_CONSTRAINT


def list_tables(db: Session, restaurant_id: int) -> list[DiningTable]:
    return list(
        db.scalars(
            select(DiningTable)
            .where(DiningTable.restaurant_id == restaurant_id)
            .order_by(DiningTable.number)
        )
    )


def create_table(
    db: Session, restaurant_id: int, payload: TableCreate
) -> DiningTable:
    data = payload.model_dump(mode="json")
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
        raise AppError("TABLE_NOT_FOUND", "No existe la mesa", 404)
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
        raise AppError(
            "VALIDATION_ERROR",
            "max_capacity no puede ser menor que min_capacity",
            422,
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
