from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.core.security import require_permission
from app.modules.tables.schemas.table import TableCreate, TableRead, TableUpdate
from app.modules.tables.services import table as table_service

router = APIRouter(
    prefix="/tables",
    tags=["tables"],
    dependencies=[Depends(require_permission("table:manage"))],
)


@router.get("", response_model=list[TableRead])
def list_tables(
    restaurant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TableRead]:
    restaurant = table_service.resolve_restaurant_id(db, restaurant_id)
    return table_service.list_tables(db, restaurant)


@router.post("", response_model=TableRead, status_code=status.HTTP_201_CREATED)
def create_table(payload: TableCreate, db: Session = Depends(get_db)) -> TableRead:
    return table_service.create_table(db, payload)


@router.patch("/{table_id}", response_model=TableRead)
def update_table(
    table_id: int, payload: TableUpdate, db: Session = Depends(get_db)
) -> TableRead:
    restaurant = table_service.resolve_restaurant_id(db, None)
    return table_service.update_table(db, table_id, restaurant, payload)
