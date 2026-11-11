# Informe de impacto — HU-AUT-02

## Esquema de datos completo, modelos compartidos y seeders

| Campo | Valor |
|---|---|
| Fecha | 2026-11-10 |
| Estado | Implementado y verificado. |
| Commits | `e2bcca7`, `6b025f5`, `52acb9a`, `a1016d2`, `627b9fb`, `76d7118`, `5d431e9`, `b13fb10`, `60223d1` |
| Migración final | `314792047285` (single head) |
| Pruebas | `100 passed` |
| Historia | HU-AUT-02 — OICO-35 |
| Alcance | 25 tablas, modelos compartidos, migraciones Alembic, seeders idempotentes y pruebas |
| Fuentes Jira | `scripts/jira/backups/jira-backlog-post-20261106.json` y `docs/backlog/matriz-fusion.md` |
| Fuentes Git | `git log --all`, `git diff dev...rama`, `git blame` |
| Autor del informe | Equipo HU-AUT-02 |

> Este documento es una foto del estado del repositorio y del backlog en la fecha indicada.
> Las líneas de código de las ramas sin fusionar se refieren a la punta de cada rama.
> Las líneas del código ya integrado se refieren a `dev` (`2354db1`).
> Al terminar la implementación se actualizarán las líneas que hayan cambiado.

---

## 1. Resumen ejecutivo

HU-AUT-02 materializa el esquema completo que consumen todas las historias funcionales. El cambio no es aislado: toca modelos que hoy viven dentro de módulos, migraciones que ya están en `dev`, y ramas de trabajo abiertas de otras personas.

### 1.1. Decisiones cerradas

| Tema | Decisión |
|---|---|
| `restaurant_settings` | **No existe.** La configuración vive en `restaurant`: `courtesy_minutes`, `slot_minutes`, `min_break_between_shifts`. |
| `opening_hours` | **No existe.** Los cinco campos de horario viven en `restaurant`: `day_of_week`, `period`, `open_time`, `close_time` y `kitchen_close_time`. |
| `price_history` | **Sí existe.** Historial dedicado de precios de platos y menús. No se sustituye por `audit_logs`. |
| `work_shifts` | Se mantiene el nombre `work_shifts`. No se renombra a `shifts`. |
| Tablas añadidas | Se mantienen: `permissions`, `role_permissions`, `table_combinations`, `table_combination_tables`, `reservation_tables`, `reservation_status_history`, `time_off_requests`, `shift_swap_requests`. |
| Carta | Se normaliza a snake_case: `categories`, `allergens`, `dishes`, `dish_allergens`. |
| Roles | Un rol por usuario (`users.role_id`). No hay tabla `user_role`. |
| Permisos | Catálogo único de permisos con nombre. |

### 1.2. Número final de tablas: 25

| Área | Tablas | Total |
|---|---|---|
| Seguridad y configuración | `restaurant`, `roles`, `permissions`, `role_permissions`, `users` | 5 |
| Carta | `categories`, `allergens`, `dishes`, `dish_allergens`, `menu_collections`, `menus`, `menu_dishes` | 7 |
| Mesas y reservas | `tables`, `table_combinations`, `table_combination_tables`, `reservations`, `reservation_tables`, `reservation_status_history` | 6 |
| Horarios | `employees`, `schedules`, `work_shifts`, `time_off_requests`, `shift_swap_requests` | 5 |
| Trazabilidad | `audit_logs`, `price_history` | 2 |
| **Total** | | **25** |

### 1.3. Impactos críticos detectados

1. **Hay dos implementaciones de HU-AUT-02.** La rama antigua de Jose Loero Nielez (`Mltiformacionjose`) y la rama actual de Jesús González Gómez. Hay que decidir cuál es la canónica antes de fusionar.
2. **Willfredy Sacedo ya tiene ramas con `users`, `roles` y `permissions`.** Sus migraciones chocan de frente con las de esta historia.
3. **PR #16 de Oscar Mauricio Mejía queda compatible sin cambios**: los cinco campos de horario siguen en `restaurant` y su servicio los lee con `getattr`.
4. **María José Rodríguez Ramos tiene un modelo `Employee` sin FK a `users`.** Nuestra tabla `employees` lo reemplaza.
5. **Patricia Aparicio Díaz tiene SQL crudo con `"Category"`, `"Allergen"` y `"restaurantId"`.** El renombrado lo rompe.
6. **`price_history` se mantiene**, así que HU-CAR-11 no hay que redefinirla sobre `audit_logs`.
7. **La tabla de turnos es `work_shifts`**, no `shifts`. Todo código de HOR debe usar el nombre final.
8. **La ubicación `bar` se añade a `tables`**. Hoy el enum de la API solo acepta `interior` y `exterior`.

---

## 2. Inventario de cambios

### 2.1. Modelos compartidos

Nueva estructura prevista:

```text
app/models/
  __init__.py
  mixins.py
  enums.py
  restaurant_model.py    # Restaurant (incluye horario)
  security_model.py      # Role, Permission, RolePermission, User
  allergen_model.py      # actualizado
  category_model.py      # actualizado
  dish_model.py          # actualizado
  dish_allergen_model.py # actualizado
  menu_model.py          # MenuCollection, Menu, MenuDish
  table_model.py         # DiningTable, TableCombination, TableCombinationTable
  reservation_model.py   # Reservation, ReservationTable, ReservationStatusHistory
  schedule_model.py      # Employee, Schedule, WorkShift, TimeOffRequest, ShiftSwapRequest
  audit_model.py         # AuditLog, PriceHistory
```

Reglas:

- Ningún modelo importa modelos de `app.modules`.
- Las relaciones usan nombres en cadena para evitar ciclos.
- `app/models/__init__.py` importa todos los modelos para que Alembic los registre.
- Se eliminan los modelos internos de módulos:
  - `app/modules/settings/models/restaurant.py`
  - `app/modules/tables/models/table.py`
- Se actualizan todos los imports afectados.

### 2.2. Migraciones

Todas cuelgan de `0e939a1815c3` (cabeza actual de `dev`). Se escriben a mano: autogenerate no detecta renombrados de tablas ni columnas.

| Migración | Contenido | Depende de |
|---|---|---|
| M1 `security_config` | `restaurant` definitivo, `roles`, `permissions`, `role_permissions`, `users`. Mantiene los cinco campos de horario en `restaurant`. | `0e939a1815c3` |
| M2 `menu_schema` | Renombra `Allergen`→`allergens`, `Category`→`categories`, `Dish`→`dishes`, `DishAllergen`→`dish_allergens`; renombra columnas; añade FKs, índices y timestamps; crea `menu_collections`, `menus`, `menu_dishes`. | M1 |
| M3 `tables_reservations` | Crea `tables` (hoy no tiene migración), `table_combinations`, `table_combination_tables`, `reservations`, `reservation_tables`, `reservation_status_history`. | M1, M2 |
| M4 `schedules_audit_price` | Crea `employees`, `schedules`, `work_shifts`, `time_off_requests`, `shift_swap_requests`, `audit_logs`, `price_history`. | M1, M2 |
| M5 `critical_constraints` | `btree_gist`, `EXCLUDE` de reservas por mesa, `EXCLUDE` de turnos por empleado, índice único parcial de reservas duplicadas y checks/indexes restantes. | M3, M4 |
| M6 `default_work_shift_type` | Añade `server_default = 'morning'` a `work_shifts.type`. | M5 |

Cada migración debe tener `downgrade` completo y probado.

### 2.3. Seeders

```text
app/database/seeders/
  __init__.py       # seed_all(), seed_minimum()
  catalog.py        # ALLERGENS, PERMISSIONS, ROLES, CATEGORIES
  security.py       # restaurante con horario, roles, permisos, usuarios, empleados
  demo.py           # mesas, platos, colecciones y menús
app/database/seed.py  # CLI: python -m app.database.seed --demo
```

- `app/core/kernel/seed.py` delega en `seed_minimum()`.
- `seed_demo.py` se conserva como envoltorio del nuevo CLI, sin duplicar lógica.
- No se usa `Base.metadata.create_all` en los seeders.

Datos del seeder mínimo (`seed_minimum`):

- 14 alérgenos UE.
- Permisos del briefing.
- 5 roles: `superadministrador`, `administrador`, `gerente`, `jefe_cocina`, `camarero`.
- Restaurante demo con horario por defecto.
- Categorías iniciales.

Datos demo (`seed_demo`):

- Un usuario por rol y sus empleados.
- Mesas, platos, colecciones y menús.

`--no-demo` no crea usuarios ni datos de negocio. Los seeders son create-only: no sobrescriben datos existentes.

### 2.4. Pruebas

Nuevas:

- `tests/database/test_migrations.py`
- `tests/database/test_seed_idempotent.py`
- `tests/database/test_constraints.py`
- `tests/database/test_imports.py`
- `tests/features/schema.feature` (escenarios Gherkin de la HU)

Actualizadas:

- `tests/conftest.py`
- `tests/test_restaurant.py`
- `tests/modules/tables/test_tables.py`
- `tests/kernel/test_kernel_stubs.py`
- Tests de carta que importan modelos (`tests/test_dish.py`, `tests/test_dish_integration.py`).

---

## 3. Impacto por persona

### 3.1. Jose Loero Nielez — `Mltiformacionjose`

**Jira**

- `HU-AUT-02` (OICO-35), asignada a Jose Loero Nielez.
- Subtareas `ST-AUT-02.1` a `ST-AUT-02.4` (OICO-36 a OICO-39).
- `HU-GES-04` (OICO-18).

**GitHub**

- Rama: `origin/HU-AUT-02-·-Migraciones-versionadas-y-seeders-idempotentes`.
- Punta: `8bfb518`.
- Autor de la rama: `Mltiformacionjose <multiformacionjose@gmail.com>`.

**Qué contiene**

| Archivo | Líneas | Contenido |
|---|---|---|
| `app/database/migrations/versions/0001_base_schema.py` | 22–136 | Esquema base con `allergens`, `permissions`, `restaurants`, `roles`, `categories`, `opening_hours`, `restaurant_settings`, `role_permissions`, `users`, `audit_logs`. |
| `app/models/users.py` | 20–75 | `Role`, `Permission`, `RolePermission`, `User`, `AuditLog`. |
| `app/models/dishes.py` | 7–26 | `Allergen` y `Category`. |
| `app/modules/settings/models/restaurant_settings.py` | 12–37 | `RestaurantSettings`, con `default_reservation_minutes`. |
| `app/modules/settings/models/opening_hours.py` | 9–25 | `OpeningHours`. |
| `app/database/seeders/` | — | Seeders de acceso, restaurante, platos y runner. |
| `tests/database/test_seeders_idempotency.py` | — | Pruebas de idempotencia. |

**Qué cambia o le afecta**

- Su rama es una implementación completa y paralela de esta misma historia.
- Usa `restaurants` en plural, mientras `dev` ya usa `restaurant` en singular.
- Crea `restaurant_settings`, que la decisión actual elimina.
- Su `permissions` usa `code`; nuestra decisión usa `name` (pendiente de confirmar).
- Su `users` no tiene `name`, `phone_number`, `token_version` ni `role_id` obligatorio.

**Acción requerida**

1. Decidir con el equipo si su rama se archiva o se reutiliza parcialmente.
2. Si se reutiliza, extraer solo seeders y tests; no fusionar sus migraciones.
3. No mantener dos cadenas de migraciones para HU-AUT-02.

**Riesgo:** alto, por duplicidad de trabajo y de esquema.

---

### 3.2. Jesús González Gómez — rama actual

**Jira**

- `HU-RES-01` (OICO-191), `HU-RES-02` (OICO-196), `HU-RES-04` (OICO-205), `HU-RES-05` (OICO-211), `HU-RES-13` (OICO-264), `HU-RES-14` (OICO-267).
- `HU-GES-03` (OICO-13).

**GitHub**

- Rama actual: `feature/HU-AUT-02-data-schema-shared-models-seeders`, punta `89c4af2`.
- Rama abierta: `origin/feature/HU-RES-01-tables-capacity-unique-number-followup`, punta `05b5985`.

**Archivos afectados**

| Archivo | Líneas | Cambio |
|---|---|---|
| `app/modules/tables/models/table.py` | 6–8, 11–38 | `DiningTable` pasa a `app/models/table_model.py`. Se añade `bar` a las ubicaciones. Columnas del DER: `is_enabled` y `is_capacity_adjustable`. |
| `app/modules/tables/models/__init__.py` | 1–4 | Se elimina; el modelo vive en `app/models`. |
| `app/modules/tables/services/table.py` | 6, 9, 22–87 | Cambia el import. Se mantiene el nombre de constraint `uq_table_restaurant_number`. |
| `app/modules/tables/routes/table.py` | 7–8, 20 y ss. | Revisar imports; sin cambio funcional. |
| `app/modules/tables/schemas/table.py` | 6–8, 16–17, 48–58 | Añadir `bar` a `TableLocation`. `is_active` y `adjustable_capacity` se mantienen en la API. |
| `tests/modules/tables/test_tables.py` | — | Imports y casos de `bar`. |
| `alembic/env.py` | 1–10 | Importar `app.models` completo. |
| `alembic/versions/0e939a1815c3_merge_restaurant_and_menu_heads.py` | 21–28 | Se mantiene como cabeza; las nuevas migraciones cuelgan de aquí. |

**Qué cambia o le afecta**

- La rama followup modifica `routes/table.py`, `services/table.py` y `tests/modules/tables/test_tables.py`; debe rebasarse sobre el nuevo `app/models`.
- La API sigue exponiendo `is_active` y `adjustable_capacity`; solo cambian los nombres físicos de columna.

**Acción requerida**

1. Implementar esta historia en la rama actual.
2. Rebasear la rama followup después de mover el modelo.
3. Añadir `bar` a esquema, modelo y tests.

**Riesgo:** medio.

---

### 3.3. Oscar Mauricio Mejía — `oscarmmejia`

**Jira**

- `HU-AUT-03` (OICO-40) y subtareas OICO-41 a OICO-46 y OICO-282.
- `HU-RES-03` (OICO-200).
- `HU-RES-09` (OICO-230).
- `HU-HOR-10` (OICO-186).

**GitHub**

- Rama fusionada: `origin/feature/HU-AUT-03-Restaurant-configuration-and-opening-hours`, punta `3ce54bc`.
- Rama sin fusionar: `origin/feature/HU-AUT-03-settings-api`, punta `316e66d`.

**Archivos afectados**

| Archivo | Líneas | Cambio |
|---|---|---|
| `app/modules/settings/models/restaurant.py` | 20–52 | El shim reexporta `Restaurant`; los cinco campos de horario siguen en el modelo. |
| `alembic/env.py` | 2 | Importa `app.models`; sin cambio funcional para settings. |
| `app/modules/settings/services/restaurant_service.py` (rama) | 36–71, 86–100 | No requiere cambios: `getattr(restaurant, field)` sigue funcionando. |
| `app/modules/settings/schemas.py` (rama) | 20–24, 37–41 | No requiere cambios: los cinco campos siguen en `Restaurant`. |
| `tests/test_settings_schedule_validation.py` (rama) | — | Sin cambios. |
| `tests/test_settings_schedule_postgres.py` (rama) | — | Sin cambios. |
| `tests/test_settings_update_service.py` (rama) | — | Sin cambios. |
| `tests/test_settings_update_postgres.py` (rama) | — | Sin cambios. |
| `tests/test_settings_service.py` (rama) | — | Sin cambios. |
| `tests/test_settings_schemas.py` (rama) | — | Sin cambios. |

**Qué cambia o le afecta**

- El acuerdo final mantiene los cinco campos de horario dentro de `Restaurant`. PR #16 queda compatible sin cambios.
- No se crea `opening_hours`; no hay migración de horarios ni `AttributeError` en `getattr`.

**Acción requerida**

1. Rebasear `feature/HU-AUT-03-settings-api` solo si hay conflicto de imports.
2. No cambiar el servicio ni los esquemas.

**Riesgo:** bajo. La incompatibilidad anterior queda resuelta por el nuevo acuerdo.

---

### 3.4. Willfredy Sacedo — `Willfredy742`

**Jira**

- `HU-AUT-04` (OICO-47).
- `HU-AUT-05` (OICO-54).
- `HU-AUT-06` (OICO-60).
- `HU-GES-05` (OICO-24).

**GitHub**

- Rama: `origin/feature/HU-AUT-04-secure-login-using-hash-and-token`, punta `b2d47ef`.
- Rama: `origin/feature/HU-AUT-05-granular-roles-and-permissions-`, punta `4799272`.

**Archivos afectados**

| Archivo | Líneas | Cambio |
|---|---|---|
| `app/models/user.py` (rama) | 1–22 | Define `users` con `hashed_password`, sin `name`, `phone_number`, `role_id` ni `token_version`. Debe alinearse con el modelo compartido. |
| `app/core/kernel/identity.py` (rama) | 1–23 | `CurrentUser` y `get_current_user`; usa `role_id == 1` para decidir el rol. Debe usar rol/permisos reales. |
| `app/models/role.py` (rama) | 5–31 | Define `user_role` N:M y `role_permission` en singular. Debe eliminarse `user_role` y usar `role_permissions`. |
| `app/core/permissions.py` (rama) | 1–6 | Catálogo mínimo; debe ampliarse al catálogo del briefing. |
| `alembic/versions/3bad8d950244_create_users_table.py` (rama) | 21–32 | Crea `users` con `hashed_password`. No puede convivir con la migración de esta historia. |
| `alembic/versions/422ec1bfaadf_add_roles_and_permissions_tables.py` (rama) | 23–49 | Crea `roles`, `permissions`, `role_permission` y `user_role`. Debe descartarse o rebasarse. |
| `app/core/security.py` (rama) | — | Hash y JWT. Nuestro seeder debe usar un formato compatible. |
| `app/api/auth.py` (rama) | — | Login y usuario actual. Debe usar el modelo compartido. |

**Qué cambia o le afecta**

- Nuestra `users` tiene `name`, `phone_number`, `role_id`, `token_version` y `password_hash`.
- Su `users` usa `hashed_password`; hay que unificar el nombre de la columna.
- Su `user_role` contradice la decisión de un rol por usuario.
- Su `role_permission` en singular contradice `role_permissions`.
- Su `permissions` usa `name`; la rama de Jose usa `code`. Hay que unificar.
- Su `CurrentUser` no puede decidir el rol comparando `role_id == 1`.

**Acción requerida**

1. Rebasear ambas ramas después de M1.
2. Eliminar sus migraciones de `users`, `roles` y `permissions`; la cadena canónica es la de esta historia.
3. Alinear `password_hash` y el formato de hash con `app/core/security.py`.
4. Cambiar `identity.py` para usar el rol y los permisos reales.
5. Actualizar imports si `User`/`Role` pasan a `app/models/security_model.py`.

**Riesgo:** alto.

---

### 3.5. Patricia Aparicio Díaz — `apariciodiazpatricia-cell` / `PATRI`

**Jira**

- `HU-CAR-01` (OICO-84), `HU-CAR-02` (OICO-89), `HU-CAR-03` (OICO-93), `HU-CAR-04` (OICO-99), `HU-CAR-05` (OICO-104), `HU-CAR-09` (OICO-125), `HU-CAR-11` (OICO-134).

**GitHub**

- Rama fusionada: `origin/feature/HU-CAR-01-categories-per-restaurant`, punta `696d102`.
- Rama fusionada: `origin/feature/HU-CAR-02-dishes-crud-and-public-menu`, PR #18, merge `222adf3`.
- Rama fusionada: `origin/feature/HU-CAR-03CRUD-for-dishes-with-allergens`, punta `dfe6794`.

**Archivos afectados**

| Archivo | Líneas | Cambio |
|---|---|---|
| `app/models/category_model.py` | 8–23 | `__tablename__ = "Category"` pasa a `categories`; `restaurantId` pasa a `restaurant_id`. |
| `app/models/dish_model.py` | 10–63 | `Dish` pasa a `dishes`; `restaurantId`/`categoryId` pasan a snake_case; FK a `categories`. |
| `app/models/allergen_model.py` | 7–26 | `Allergen` pasa a `allergens`. |
| `app/models/dish_allergen_model.py` | 7–20 | `DishAllergen` pasa a `dish_allergens`; `dishId`/`allergenId` pasan a snake_case. |
| `app/controllers/category_controller.py` | 10–45, 94–145 | Consultas ORM sobre `Category`; revisar imports y nombres de atributos. |
| `app/controllers/dish_controller.py` | 25–61, 204–249 | Se conserva la versión ORM de dev; el SQL crudo de nuestra rama se descarta. |
| `alembic/versions/e773e1d3e1e9_create_initial_restaurant_tables.py` | 24–61 | Crea las tablas con los nombres antiguos. La migración M2 las renombra después. |
| `tests/test_category.py` | — | Revisar imports y expectativas. |
| `tests/test_dish.py` | — | Se conserva la versión de dev, ya adaptada al controlador ORM. |
| `tests/test_dish_integration.py` | — | Auto-fusionado: modelos reales + test de categoría desconocida + descripción. |

**Qué cambia o le afecta**

- El renombrado de tablas y columnas rompe el SQL crudo de `dish_controller.py`.
- Los tests de API probablemente sigan pasando porque no exponen nombres de tabla, pero los imports y el SQL sí cambian.
- `price_history` se mantiene, así que HU-CAR-11 queda desbloqueada.
- `price_history` se poblará desde los servicios de cambio de precio; la tabla tiene `entity_type` (`dish`/`menu`), `entity_id`, `old_price`, `new_price`, `changed_by_user_id` y `created_at`.

**Acción requerida**

1. Actualizar los modelos y el SQL crudo en la misma PR o coordinar una PR posterior.
2. Adaptar imports de tests.
3. Confirmar el alcance de HU-CAR-11 con `price_history`.

**Riesgo:** medio-alto, porque su código ya está en `dev`.

#### HU-CAR-02 — ya fusionada en `dev`

- PR #18, merge `222adf3`.
- Archivos:
  - `app/controllers/dish_controller.py` (ORM, menú público y endpoint de estado).
  - `app/api/dish_routes.py`.
  - `app/schemas/dish_schema.py`.
  - `app/controllers/allergen_controller.py`.
  - `app/api/allergen_routes.py`.
  - `app/schemas/allergen_schema.py`.
  - `tests/test_allergen.py`.
  - `tests/test_dish_public.py`.
  - `tests/features/dish.feature`.
  - `tests/test_dish.py`.
  - `tests/test_dish_integration.py`.
- Impacto en HU-AUT-02: se toma el controlador y los tests ORM de dev; no hay cambios en `app/models`; el catálogo de alérgenos se unifica con los nombres oficiales.
- `app/models/*` no tuvo conflicto porque dev no modificó esos archivos.

---

### 3.6. María José Rodríguez Ramos — `mjrr39sevilla`

**Jira**

- `HU-HOR-01` (OICO-142), `HU-HOR-02` (OICO-147), `HU-HOR-03` (OICO-151), `HU-HOR-11` (OICO-259), `HU-HOR-12` (OICO-261).
- `HU-AUT-01` (OICO-30), `HU-AUT-09` (OICO-75), `HU-AUT-11` (OICO-251).

**GitHub**

- Rama sin fusionar: `origin/Feature/HU-HOR-01-employees-and-work-status`, punta `a7f5d2b`.
- Autora: `María José <mjrr39sevilla@gmail.com>`.

**Archivos afectados**

| Archivo | Líneas | Cambio |
|---|---|---|
| `app/models/employee.py` (rama) | 7–16 | `Employee` con `restaurant_id` y `user_id` sin FK. Pasa a `app/models` y añade FK a `users.id`. |
| `app/api/employees.py` (rama) | 1–45 | Router de empleados. Revisar imports y dependencias. |
| `app/controllers/employee_controller.py` (rama) | 5, 9–13 | Importa `app.models.employee`; el TODO del vínculo con usuario desaparece. |
| `alembic/env.py` (rama) | — | Importa el modelo; debe usar `app.models`. |
| `app/core/kernel/seed.py` | 1–12 | Hoy es un placeholder; pasa a sembrar restaurante, roles, usuarios y catálogos. |
| `app/core/kernel/permissions.py` | 8–13 | Stub; se conectará con el catálogo real. |
| `tests/kernel/test_kernel_stubs.py` | 10–24 | Comprueba el stub de permisos; puede necesitar ajustes. |

**Qué cambia o le afecta**

- Nuestra tabla `employees` incluye `user_id` con FK; su modelo lo deja como entero y con TODO.
- La tabla de turnos es `work_shifts`, no `shifts`; HOR-02/HOR-03 deben usar ese nombre.
- `seed_minimum_data` deja de ser un placeholder y crea datos reales; sus tests de kernel pueden verse afectados.

**Acción requerida**

1. Rebasear `Feature/HU-HOR-01-employees-and-work-status` después de M4.
2. Mover `Employee` a `app/models` y añadir la FK a `users`.
3. Alinear `work_shifts` en HOR-02/HOR-03.
4. Revisar tests de kernel y de empleados.

**Riesgo:** medio-alto.

---

### 3.7. Personas afectadas de forma indirecta

Estas historias consumen las tablas nuevas aunque no tengan una rama abierta en este momento:

| Persona | Historias | Dependencia |
|---|---|---|
| Oscar Mauricio Mejía | HU-RES-03, HU-RES-09, HU-HOR-10 | `reservations`, `reservation_tables`, `restaurant.courtesy_minutes`, `restaurant.min_break_between_shifts` |
| Jesús González Gómez | HU-RES-04, HU-RES-05, HU-RES-13, HU-RES-14 | `reservations`, `reservation_tables`, `table_combinations`, `reservation_status_history` |
| Willfredy Sacedo | HU-AUT-06 | `users`, `audit_logs` |
| Patricia Aparicio Díaz | HU-CAR-11 | `price_history` |
| María José Rodríguez Ramos | HU-HOR-02, HU-HOR-03 | `schedules`, `work_shifts` |
| Sin asignar en Jira | HU-RES-06/07/08, HU-HOR-04/05, HU-CAR-06/07/08/10/12, HU-AUT-08 | `reservation_status_history`, `time_off_requests`, `shift_swap_requests`, `menu_collections`, `menus`, `menu_dishes`, `audit_logs` |

Las historias sin asignar deben quedar explícitas en la planificación: alguien tendrá que asumirlas y todas consumen este esquema.

---

## 4. Archivos que se tocan y propietario actual

| Archivo | Propietario actual | Cambio |
|---|---|---|
| `app/modules/settings/models/restaurant.py` | Oscar Mauricio Mejía | Se eliminan las columnas de horario; quedan las de configuración. |
| `app/models/category_model.py` | Patricia Aparicio Díaz | Renombrado a `categories` y snake_case. |
| `app/models/dish_model.py` | Patricia Aparicio Díaz | Renombrado a `dishes` y snake_case. |
| `app/models/allergen_model.py` | Patricia Aparicio Díaz | Renombrado a `allergens`. |
| `app/models/dish_allergen_model.py` | Patricia Aparicio Díaz | Renombrado a `dish_allergens`. |
| `app/controllers/category_controller.py` | Patricia Aparicio Díaz | Revisión de imports y atributos. |
| `app/controllers/dish_controller.py` | Patricia Aparicio Díaz | SQL crudo sustituido por ORM. |
| `alembic/versions/e773e1d3e1e9_create_initial_restaurant_tables.py` | Patricia Aparicio Díaz | Se mantiene; M2 renombra después. |
| `app/modules/tables/models/table.py` | Jesús González Gómez | Se mueve a `app/models/table_model.py`. |
| `app/modules/tables/models/__init__.py` | Jesús González Gómez | Se elimina. |
| `app/modules/tables/services/table.py` | Jesús González Gómez | Cambia el import. |
| `app/modules/tables/routes/table.py` | Jesús González Gómez | Revisión de imports. |
| `app/modules/tables/schemas/table.py` | Jesús González Gómez | Añadir `bar` a `TableLocation`. |
| `tests/modules/tables/test_tables.py` | Jesús González Gómez | Imports y casos de `bar`. |
| `app/core/kernel/seed.py` | María José Rodríguez Ramos | Implementar `seed_minimum_data`. |
| `app/core/kernel/permissions.py` | María José Rodríguez Ramos | Conectar con el catálogo. |
| `app/core/kernel/identity.py` | Willfredy Sacedo | Debe usar rol/permisos reales. |
| `alembic/env.py` | Oscar Mauricio Mejía / Jesús González Gómez | Importar `app.models` completo. |
| `tests/conftest.py` | Kernel | Imports, `btree_gist`, truncado y modelos. |
| `app/main.py` | Varios | Lifespan opcional para `seed_minimum_data`. |
| `seed_demo.py` | Sin seguimiento en git | Se conserva como envoltorio del nuevo CLI. |

---

## 5. Orden de implementación

1. **ST-AUT-02.1** — Revisar y completar Alembic. `alembic/env.py`, `alembic.ini` y cadena de migraciones.
2. **M1** — Seguridad y configuración: `restaurant` con horario, `roles`, `permissions`, `role_permissions`, `users`.
3. **M2** — Carta: normalización y tablas de menús.
4. **M3** — Mesas y reservas.
5. **M4** — Horarios, auditoría y `price_history`.
6. **M5** — Restricciones e índices críticos.
7. **M6** — Default de `work_shifts.type`.
8. **ST-AUT-02.2** — Seeders de categorías y alérgenos.
9. **ST-AUT-02.3** — Seeders de restaurante, usuarios, roles y permisos.
10. **ST-AUT-02.4** — Pruebas de idempotencia y downgrade.
11. Actualizar este informe con las líneas finales y el resultado de las pruebas.

---

## 6. Checklist de coordinación por rama

### `feature/HU-AUT-02-data-schema-shared-models-seeders` (Jesús)

- [x] Implementar M1–M6.
- [x] Mover modelos a `app/models`.
- [x] Adoptar el controlador ORM de dev en la carta.
- [x] Implementar seeders.
- [x] Añadir tests de migración, idempotencia, restricciones e imports.
- [x] Ejecutar `upgrade head`, `downgrade base`, seeders dos veces y `pytest`.

### `origin/HU-AUT-02-·-Migraciones-versionadas-y-seeders-idempotentes` (Jose)

- [ ] Decidir si se archiva o se reutiliza.
- [ ] Extraer solo seeders/tests si aportan.
- [ ] No fusionar sus migraciones.
- [ ] Aclarar la asignación de Jira frente a la rama actual.

### `origin/feature/HU-AUT-03-settings-api` (Oscar)

- [x] Compatible sin cambios: los cinco campos siguen en `Restaurant`.
- [ ] Rebasear solo si aparece un conflicto de imports.

### `origin/feature/HU-AUT-04-secure-login-using-hash-and-token` (Willfredy)

- [ ] Rebasear después de M1.
- [ ] Eliminar la migración `3bad8d950244`.
- [ ] Alinear `password_hash` y el formato de hash.
- [ ] Adaptar `identity.py` y `auth.py`.
- [ ] No duplicar `users`.

### `origin/feature/HU-AUT-05-granular-roles-and-permissions-` (Willfredy)

- [ ] Rebasear después de M1.
- [ ] Eliminar la migración `422ec1bfaadf`.
- [ ] Eliminar `user_role`.
- [ ] Unificar `role_permission` → `role_permissions`.
- [ ] Ampliar el catálogo de permisos.
- [ ] No duplicar `roles`/`permissions`.

### `origin/Feature/HU-HOR-01-employees-and-work-status` (María José)

- [ ] Rebasear después de M4.
- [ ] Mover `Employee` a `app/models`.
- [ ] Añadir FK a `users`.
- [ ] Alinear `work_shifts`.
- [ ] Revisar tests de kernel y empleados.

### `origin/feature/HU-RES-01-tables-capacity-unique-number-followup` (Jesús)

- [ ] Rebasear después de M3.
- [ ] Actualizar imports del modelo.
- [ ] Añadir `bar` a esquemas y tests.
- [ ] Mantener el nombre `uq_table_restaurant_number` o actualizarlo en servicio y migración a la vez.

---

## 7. Riesgos y rollback

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Duplicidad de HU-AUT-02 | Dos esquemas incompatibles | Decidir una rama canónica antes de mergear. |
| Migraciones de `users`/`roles` duplicadas | `alembic upgrade` falla o crea tablas dos veces | Una sola cadena; eliminar migraciones de Willfredy. |
| Columnas de horario en `restaurant` | PR #16 las espera ahí | Se mantienen en `Restaurant`; no hay `opening_hours`. |
| `Employee` sin FK | Inconsistencia con `users` | Rebasear y añadir FK. |
| SQL crudo de carta | Errores en runtime | Sustituir por ORM en la misma PR. |
| `btree_gist` no disponible | M5 falla | Documentar privilegio y verificar en CI. |
| `price_history` polimórfica | Sin FK a `dishes`/`menus` | Validar `entity_type` y `entity_id` en servicio; checks en BD. |
| `work_shifts` vs `shifts` | Código de HOR usa el nombre equivocado | Unificar en `work_shifts`. |
| `bar` no aceptado por la API | Mesas de bar rechazadas | Añadir al enum y tests. |
| Base local desincronizada | `upgrade` falla por tablas creadas con `create_all` | Recrear base o hacer `downgrade base` antes de migrar. |

Rollback:

- `alembic downgrade base` debe dejar solo `alembic_version`.
- La extensión `btree_gist` puede quedarse instalada; no es una tabla ni una restricción huérfana.
- Los seeders no crean esquema; no hay que borrar tablas para revertir datos demo.

---

## 8. Decisiones pendientes

1. **Propiedad de HU-AUT-02:** Jira la asigna a Jose Loero Nielez, pero la rama actual la lleva Jesús González Gómez. Hay que aclarar quién es el owner.
2. **Columna de permisos:** `permissions.name` o `permissions.code`. La rama de Jose usa `code`; la de Willfredy y el texto de la historia usan `name`.
3. **Formato de hash:** alinear con `app/core/security.py` de Willfredy o definir un formato común.
4. **`SEED_ON_STARTUP`:** por defecto `false`; el seeder se ejecuta por CLI.
5. **`price_history.changed_by_user_id`:** nullable para cambios automáticos.
6. **`bar` en `tables`:** confirmar que entra en el alcance de HU-RES-01.
7. **Compatibilidad de imports:** ¿se dejan `app/models/user.py` y `app/models/role.py` como re-export temporales o se actualizan todos los imports de golpe?

---

## Anexo A — Correspondencia Jira ↔ GitHub

| Persona Jira | Autor/a en Git | Ramas relevantes |
|---|---|---|
| Jose Loero Nielez | `Mltiformacionjose <multiformacionjose@gmail.com>` | `HU-AUT-02-·-Migraciones-versionadas-y-seeders-idempotentes` |
| Jesús González Gómez | `Jesús González Gómez <gonzalezgomezjesus16061997@gmail.com>` | `feature/HU-AUT-02-data-schema-shared-models-seeders`, `feature/HU-RES-01-...-followup` |
| Oscar Mauricio Mejía | `oscarmmejia <neo_9615@hotmail.com>` | `feature/HU-AUT-03-settings-api`, `feature/HU-AUT-03-Restaurant-configuration...` |
| Willfredy Sacedo | `Willfredy742 <wilfredy742@gmail.com>` | `feature/HU-AUT-04-secure-login...`, `feature/HU-AUT-05-granular-roles...` |
| Patricia Aparicio Díaz | `apariciodiazpatricia-cell <apariciodiazpatricia@gmail.com>`, `PATRI` | `feature/HU-CAR-01-categories-per-restaurant`, `feature/HU-CAR-03CRUD...` |
| María José Rodríguez Ramos | `María José <mjrr39sevilla@gmail.com>` | `Feature/HU-HOR-01-employees-and-work-status` |

## Anexo B — Historias consumidoras y tablas

| Historia | Persona | Tablas principales |
|---|---|---|
| HU-AUT-03 | Oscar | `restaurant` (incluye horario) |
| HU-AUT-04 | Willfredy | `users` |
| HU-AUT-05 | Willfredy | `roles`, `permissions`, `role_permissions`, `users` |
| HU-AUT-06 | Willfredy | `users`, `audit_logs` |
| HU-CAR-01/02/03/04/05/09/11 | Patricia | `categories`, `allergens`, `dishes`, `dish_allergens`, `price_history` |
| HU-CAR-06/07/08/10/12 | Sin asignar | `menu_collections`, `menus`, `menu_dishes` |
| HU-HOR-01/02/03/11/12 | María José | `employees`, `schedules`, `work_shifts` |
| HU-HOR-04/05 | Sin asignar | `work_shifts`, `time_off_requests`, `shift_swap_requests` |
| HU-RES-01/02/04/05/13/14 | Jesús | `tables`, `table_combinations`, `reservations`, `reservation_tables`, `reservation_status_history` |
| HU-RES-03/09 | Oscar | `reservations`, `reservation_tables`, `restaurant` |
| HU-RES-06/07/08 | Sin asignar | `reservation_status_history`, `reservation_tables` |
| HU-RES-11/12 | Sin asignar | `reservations`, `tables`, `table_combinations` |

---

## Anexo C — Comprobaciones realizadas

- `git merge-base --is-ancestor` para distinguir ramas fusionadas y sin fusionar.
- `git diff dev...rama` para listar archivos de cada rama.
- `git blame` para atribuir líneas de código del esquema actual.
- Lectura del snapshot de Jira `jira-backlog-post-20261106.json`.
- Lectura de `docs/backlog/matriz-fusion.md`.

Resultado al cerrar la implementación:

- `alembic upgrade head` desde base vacía: correcto.
- `alembic downgrade base`: correcto; solo queda `alembic_version`.
- Seeders ejecutados dos veces: conteos estables.
- `pytest`: 100 pruebas superadas.
- Base de desarrollo recreada, migrada a `314792047285` y sembrada.
- Esquema final: 25 tablas; `opening_hours` no existe.
- Permisos finales: 17; roles finales: 5; alérgenos: 14.
- HU-CAR-02 (PR #18) integrada en `dev`; su controlador ORM y sus tests se conservan.
- Se mantienen `price_history`, `work_shifts` y el horario dentro de `restaurant`.
