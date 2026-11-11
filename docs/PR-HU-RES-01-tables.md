# feat(tables): CRUD de mesas con consulta, habilitación y 403 real

## Resumen

Avanza HU-RES-01 con la gestión de mesas individuales sobre `dev` y HU-AUT-02 ya integrada:

- Añade la consulta individual de una mesa.
- Expone la habilitación e inhabilitación como operaciones explícitas e idempotentes.
- Permite inhabilitar mediante `PATCH {"is_active": false}`, alternativa REST al endpoint de acción.
- Aplica el permiso `table:manage` y devuelve `403` cuando falta.
- Refuerza el aislamiento por restaurante en todas las consultas.
- Documenta todos los endpoints de mesas en OpenAPI, incluida la respuesta `403`.
- Cubre con pruebas los códigos `200`, `201`, `403`, `404`, `409` y `422`.

Esta entrega es **parcial**: no incluye combinaciones de mesas ni el aviso de reservas futuras afectadas.

## Cambios

### API de mesas

- `GET /api/v1/tables`: listado ordenado por número y limitado al restaurante autenticado.
- `GET /api/v1/tables/{table_id}`: consulta individual o `404`.
- `POST /api/v1/tables`: creación con validación de número único y rango de capacidad.
- `PATCH /api/v1/tables/{table_id}`: edición parcial, incluido `is_active`.
- `POST /api/v1/tables/{table_id}/enable`: habilitación idempotente.
- `POST /api/v1/tables/{table_id}/disable`: inhabilitación idempotente.

Las operaciones de estado devuelven siempre `200` con el estado resultante. No devuelven `400`, `409` ni `204` cuando la mesa ya está en el estado solicitado.

### Seguridad y aislamiento

- `require_permission` comprueba `"*"` o el permiso exacto.
- Si el usuario no tiene `table:manage`, responde `403 FORBIDDEN`.
- El permiso `table:manage` ya existe en el catálogo integrado con HU-AUT-02.
- `get_table` filtra por `id` y `restaurant_id` en la misma consulta SQL, evitando accesos cruzados entre restaurantes.
- Consulta, edición, habilitación e inhabilitación de una mesa ajena devuelven `404` y no modifican sus datos.

### Pruebas

- Consulta individual: `200` y `404`.
- `403` para los seis endpoints protegidos.
- Permiso exacto `table:manage` sin `"*"`: los seis endpoints funcionan.
- Acceso cruzado entre restaurantes: `404` y datos intactos.
- Habilitación, inhabilitación e idempotencia.
- `PATCH {"is_active": false}` y `PATCH {"is_active": true}`.
- Ubicación `bar` en creación y edición.
- Test de kernel para permiso ausente.

## Verificación

```text
.venv\Scripts\python.exe -m pytest -q
131 passed
```

La respuesta `403` aparece documentada en OpenAPI para los seis endpoints de mesas.

## Fuera de alcance

- Combinaciones de mesas y validaciones CA5–CA8.
- Aviso e impacto sobre reservas futuras, correspondiente a OICO-198 / ST-RES-02.2.
- Reasignación automática de reservas al inhabilitar una mesa.

Cuando se aborde OICO-198, el aviso deberá cubrir tanto `POST /disable` como `PATCH {"is_active": false}`, incluir reservas de mesas individuales y de combinaciones, y conservarlas sin reasignación automática. Para desacoplar ambos dominios, se propone que el servicio de mesas emita un evento interno `TableDisabledEvent` al que pueda suscribirse Reservas.

## Notas de integración

- Rama rebasada sobre `dev`, que ya incluye HU-AUT-02 y los últimos merges de horarios.
- Sin migraciones nuevas en esta rama: el esquema de mesas, `bar` y las columnas físicas `is_enabled` / `is_capacity_adjustable` vienen de HU-AUT-02.
- La API mantiene `is_active` y `adjustable_capacity` como nombres públicos.
- El cambio de `require_permission` es compartido con otras ramas. Debe coordinarse con el PR #20 (HU-AUT-05) para no mantener dos implementaciones distintas del checker.

## Puntos de revisión

- El cambio de `require_permission` afecta a todos los módulos que lo usan. En desarrollo el usuario stub mantiene `"*"`, así que no cambia el comportamiento actual; el `403` real depende de completar la integración de identidad de HU-AUT-04/05.
- La autorización completa y la sustitución del stub de identidad no forman parte de este PR.
- HU-RES-01 sigue parcial: este PR no cierra la historia completa.
