from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.core.kernel.identity import CurrentUser
from app.core.kernel.permissions import require_permission
from app.modules.tables.schemas.table import TableCreate, TableRead, TableUpdate
from app.modules.tables.services import table as table_service

router = APIRouter(prefix="/tables", tags=["tables"])

FORBIDDEN_RESPONSE = {
    403: {"description": "El usuario no tiene el permiso table:manage."}
}


@router.get(
    "",
    response_model=list[TableRead],
    summary="Listar mesas",
    description="Devuelve las mesas del restaurante autenticado, ordenadas por número.",
    responses={**FORBIDDEN_RESPONSE},
)
def list_tables(
    user: CurrentUser = Depends(require_permission("table:manage")),
    db: Session = Depends(get_db),
) -> list[TableRead]:
    return table_service.list_tables(db, user.restaurant_id)


@router.get(
    "/{table_id}",
    response_model=TableRead,
    summary="Consultar una mesa",
    description="Devuelve una mesa del restaurante autenticado por su identificador.",
    responses={
        **FORBIDDEN_RESPONSE,
        404: {"description": "No existe la mesa o pertenece a otro restaurante."},
    },
)
def get_table(
    table_id: int,
    user: CurrentUser = Depends(require_permission("table:manage")),
    db: Session = Depends(get_db),
) -> TableRead:
    return table_service.get_table(db, table_id, user.restaurant_id)


@router.post(
    "",
    response_model=TableRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una mesa",
    description=(
        "Crea una mesa en el restaurante autenticado. El número debe ser único dentro "
        "del restaurante, la capacidad mínima debe ser al menos 1 y la capacidad máxima "
        "no puede ser menor que la mínima."
    ),
    responses={
        **FORBIDDEN_RESPONSE,
        409: {"description": "Ya existe una mesa con ese número en el restaurante."},
        422: {"description": "Los datos de la mesa no son válidos."},
    },
)
def create_table(
    payload: TableCreate,
    user: CurrentUser = Depends(require_permission("table:manage")),
    db: Session = Depends(get_db),
) -> TableRead:
    return table_service.create_table(db, user.restaurant_id, payload)


@router.patch(
    "/{table_id}",
    response_model=TableRead,
    summary="Actualizar una mesa",
    description=(
        "Actualiza parcialmente una mesa. Si se modifican las capacidades, el rango "
        "resultante debe seguir siendo válido y el número no puede repetirse dentro "
        "del restaurante."
    ),
    responses={
        **FORBIDDEN_RESPONSE,
        404: {"description": "No existe la mesa o pertenece a otro restaurante."},
        409: {"description": "Ya existe otra mesa con ese número en el restaurante."},
        422: {"description": "Los datos enviados no son válidos."},
    },
)
def update_table(
    table_id: int,
    payload: TableUpdate,
    user: CurrentUser = Depends(require_permission("table:manage")),
    db: Session = Depends(get_db),
) -> TableRead:
    return table_service.update_table(db, table_id, user.restaurant_id, payload)


@router.post(
    "/{table_id}/enable",
    response_model=TableRead,
    summary="Habilitar una mesa",
    description=(
        "Marca la mesa como habilitada. Una mesa habilitada puede recibir reservas nuevas. "
        "La operación es idempotente: habilitar una mesa ya habilitada devuelve el mismo estado."
    ),
    responses={
        **FORBIDDEN_RESPONSE,
        404: {"description": "No existe la mesa o pertenece a otro restaurante."},
    },
)
def enable_table(
    table_id: int,
    user: CurrentUser = Depends(require_permission("table:manage")),
    db: Session = Depends(get_db),
) -> TableRead:
    return table_service.enable_table(db, table_id, user.restaurant_id)


@router.post(
    "/{table_id}/disable",
    response_model=TableRead,
    summary="Inhabilitar una mesa",
    description=(
        "Marca la mesa como inhabilitada para que no reciba reservas nuevas. "
        "No se reasigna automáticamente ninguna reserva existente. "
        "La operación es idempotente: inhabilitar una mesa ya inhabilitada devuelve el mismo estado."
    ),
    responses={
        **FORBIDDEN_RESPONSE,
        404: {"description": "No existe la mesa o pertenece a otro restaurante."},
    },
)
def disable_table(
    table_id: int,
    user: CurrentUser = Depends(require_permission("table:manage")),
    db: Session = Depends(get_db),
) -> TableRead:
    return table_service.disable_table(db, table_id, user.restaurant_id)
