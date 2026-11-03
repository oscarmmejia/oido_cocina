from typing import Annotated, Callable

from fastapi import Header, HTTPException, status

DEV_PERMISSIONS_HEADER = "X-Dev-Permissions"


def require_permission(permission: str) -> Callable[..., str]:
    """Devuelve una dependencia que exige ``permission``.

    TEMPORAL: stub de desarrollo. La cabecera ``X-Dev-Permissions`` ausente deja pasar
    cualquier petición; si está presente, debe incluir el permiso en una lista separada
    por comas. El cuerpo lo sustituye HU-AUT-05 sin tocar ninguna ruta: la firma
    ``require_permission(permission)`` es el contrato.

    Cuando exista autenticación real, sin usuario válido el resultado correcto es 401.
    """

    def dependency(
        x_dev_permissions: Annotated[str | None, Header()] = None,
    ) -> str:
        if x_dev_permissions is None:
            return permission

        granted = {item.strip() for item in x_dev_permissions.split(",") if item.strip()}
        if permission not in granted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Falta el permiso requerido: {permission}",
            )
        return permission

    return dependency
