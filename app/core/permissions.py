from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionSpec:
    name: str
    description: str


PERMISSIONS: tuple[PermissionSpec, ...] = (
    PermissionSpec("category:manage", "Gestionar categorías de la carta"),
    PermissionSpec("dish:create", "Crear platos"),
    PermissionSpec("dish:update", "Editar platos"),
    PermissionSpec("dish:deactivate", "Activar o desactivar platos"),
    PermissionSpec("menu:create", "Crear colecciones y menús"),
    PermissionSpec("menu:update", "Editar colecciones y menús"),
    PermissionSpec("menu:updatePrice", "Cambiar precios de menús"),
    PermissionSpec("reservation:assign", "Asignar mesas y reservas"),
    PermissionSpec("settings:update", "Editar la configuración del restaurante"),
    PermissionSpec("user:manage", "Gestionar usuarios"),
    PermissionSpec("table:manage", "Gestionar mesas"),
    PermissionSpec("employee:manage", "Gestionar empleados"),
    PermissionSpec("schedule:manage", "Gestionar cuadrantes"),
    PermissionSpec("schedule:publish", "Publicar cuadrantes"),
    PermissionSpec("timeoff:approve", "Aprobar ausencias"),
    PermissionSpec("report:view", "Consultar informes"),
    PermissionSpec("audit:view", "Consultar la auditoría"),
)

PERMISSION_NAMES = frozenset(item.name for item in PERMISSIONS)

ROLE_SUPERADMIN = "superadministrador"
ROLE_ADMIN = "administrador"
ROLE_MANAGER = "gerente"
ROLE_HEAD_CHEF = "jefe_cocina"
ROLE_WAITER = "camarero"

ROLE_NAMES: tuple[str, ...] = (
    ROLE_SUPERADMIN,
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_HEAD_CHEF,
    ROLE_WAITER,
)

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    ROLE_SUPERADMIN: PERMISSION_NAMES,
    ROLE_ADMIN: PERMISSION_NAMES - {"audit:view"},
    ROLE_MANAGER: frozenset(
        {
            "category:manage",
            "dish:create",
            "dish:update",
            "dish:deactivate",
            "menu:create",
            "menu:update",
            "menu:updatePrice",
            "reservation:assign",
            "settings:update",
            "table:manage",
            "employee:manage",
            "schedule:manage",
            "schedule:publish",
            "timeoff:approve",
            "report:view",
        }
    ),
    ROLE_HEAD_CHEF: frozenset(
        {
            "category:manage",
            "dish:create",
            "dish:update",
            "dish:deactivate",
            "menu:create",
            "menu:update",
            "menu:updatePrice",
            "report:view",
        }
    ),
    ROLE_WAITER: frozenset(
        {
            "reservation:assign",
            "table:manage",
            "report:view",
        }
    ),
}
