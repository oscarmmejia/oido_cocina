from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.core.kernel.identity import CurrentUser
from app.core.kernel.permissions import require_permission
from app.modules.tables.schemas.table import TableCreate, TableRead, TableUpdate
from app.modules.tables.services import table as table_service

router = APIRouter(prefix="/tables", tags=["tables"])


@router.get("", response_model=list[TableRead])
def list_tables(
    user: CurrentUser = Depends(require_permission("table:manage")),
    db: Session = Depends(get_db),
) -> list[TableRead]:
    return table_service.list_tables(db, user.restaurant_id)


@router.post("", response_model=TableRead, status_code=status.HTTP_201_CREATED)
def create_table(
    payload: TableCreate,
    user: CurrentUser = Depends(require_permission("table:manage")),
    db: Session = Depends(get_db),
) -> TableRead:
    return table_service.create_table(db, user.restaurant_id, payload)


@router.patch("/{table_id}", response_model=TableRead)
def update_table(
    table_id: int,
    payload: TableUpdate,
    user: CurrentUser = Depends(require_permission("table:manage")),
    db: Session = Depends(get_db),
) -> TableRead:
    return table_service.update_table(db, table_id, user.restaurant_id, payload)
