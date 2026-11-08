# Oído Cocina

Backend (FastAPI + PostgreSQL) para la gestión de restaurantes: carta y menús, mesas y reservas,
usuarios y permisos, configuración por restaurante y personal y horarios.

> **Estado:** Sprint 1. Está hecha la base de datos (HU-AUT-02): migraciones versionadas, seeders
> idempotentes y sus tests. Hay además un esqueleto de API (`/api/v1/health`), un formato de error común y una
> identidad **provisional** para desarrollo. La autenticación real y el resto de módulos llegan en las siguientes historias.

## Requisitos

- Python 3.12 o superior
- PostgreSQL (probado con la versión 16)
- Un cliente para ver los datos, por ejemplo pgAdmin o la herramienta Database de PyCharm

## Puesta en marcha

Todos los comandos se ejecutan desde la raíz del proyecto, donde está `alembic.ini`.

### 1. Crear la base de datos (una sola vez)

En pgAdmin: clic derecho en la base `postgres` → **Query Tool**, y ejecutar **por separado**:

```sql
CREATE USER oido WITH PASSWORD 'tu_contraseña_local';
CREATE DATABASE oido_cocina OWNER oido;
```

### 2. Entorno e dependencias

```
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS
pip install -r requirements.txt
```

### 3. Variables de entorno

Copiar `.env.example` a `.env` y rellenarlo. **El `.env` nunca se sube al repositorio.**

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | Conexión a PostgreSQL. Formato: `postgresql+psycopg://usuario:contraseña@localhost:5432/oido_cocina` |
| `SEED_DEMO_PASSWORD` | Contraseña que tendrán los usuarios de demostración. Solo para desarrollo |
| `AUTH_STUBS_ENABLED` | Opcional (por defecto `false`). Actívala solo en desarrollo local para usar la identidad provisional. **Temporal:** se elimina con HU-AUT-04. Nunca debe estar activa en producción |

Si la contraseña de la base de datos contiene símbolos como `@`, `:`, `/` o `#`, hay que codificarlos en la URL
(por ejemplo `@` se escribe `%40`).

### 4. Crear las tablas y cargar los datos

```
alembic upgrade head
python -m app.database.seeders
```

El seeder se puede ejecutar todas las veces que se quiera: no duplica datos. La segunda ejecución debe
mostrar `0 inserted` en todas las tablas.

### 5. Comprobar que funciona

En pgAdmin, refrescar `oido_cocina` y abrir **Schemas → public → Tables**: deben aparecer 11 tablas
(las 10 del modelo más `alembic_version`).

```sql
SELECT r.name AS rol, u.email, u.restaurant_id
FROM users u JOIN roles r ON r.id = u.role_id
ORDER BY r.id;                    -- 5 filas, una por rol

SELECT count(*) FROM allergens;   -- 14
```

## Estructura (parte de base de datos)

```
alembic.ini                       Configuración de Alembic (la URL no va aquí)
app/
  main.py                         Aplicación FastAPI (prefijo /api/v1)
  api/, controllers/, schemas/    Esqueleto de la API (por ahora solo /health)
  core/
    config.py                     Settings desde variables de entorno (.env)
    database_connection.py        Engine y sesiones (dependencia get_db)
    security.py                   hash_password / verify_password (Argon2id)
    errors/                       Formato de error común, códigos y manejadores (único sistema de errores)
    kernel/                       Identidad y permisos PROVISIONALES (HU-AUT-04 y HU-AUT-05)
  database/
    base.py                       Base declarativa única, convención de nombres y TimestampMixin
    migrations/                   Único historial de Alembic: entorno y versiones
    seeders/                      Datos de demostración (idempotentes)
  models/                         Modelos SQLAlchemy (users, dishes) y reexportación de los demás
  modules/
    settings/models/              Restaurante, configuración y horarios
tests/
  api/, core/, kernel/            Tests de la API, errores, configuración y stubs
  database/                       Tests de migraciones y seeders
  test_restaurant_settings.py     Una sola configuración por restaurante
```

Hay **un único historial de Alembic** (`app/database/migrations/`) y **una única `Base`** (`app/database/base.py`).
No crear otro directorio `alembic/` ni otra `Base`: dos historiales sobre la misma base de datos se bloquean entre sí.

## Modelo de datos

Diez tablas, agrupadas por módulo:

| Módulo | Tablas |
|---|---|
| `app/modules/settings/models/` | `restaurants`, `restaurant_settings`, `opening_hours` |
| `app/models/users.py` | `roles`, `permissions`, `role_permissions`, `users`, `audit_logs` |
| `app/models/dishes.py` | `allergens`, `categories` |

Los modelos nuevos se importan desde `app.models`, que reexporta todos y es lo que lee Alembic.

Convenciones:

- Nombres en `snake_case`. Todas las tablas llevan `created_at` y `updated_at` (con zona horaria),
  salvo `role_permissions` y `audit_logs`, que solo tiene `created_at` porque no se modifica.
- Las restricciones tienen nombres deterministas (`pk_`, `fk_`, `uq_`, `ck_`, `ix_`), así las migraciones
  son estables y el `downgrade` puede borrarlas por nombre.
- Baja lógica con `is_active` en lugar de borrar.
- `users.restaurant_id` puede ser nulo: el superadministrador y los clientes no pertenecen a un solo restaurante.
- Nada de configuración fija en el código: cortesía, duración de franja, descansos y horarios viven en
  `restaurant_settings` y `opening_hours`.
- `permissions` y `role_permissions` existen pero están vacías: se rellenarán con la matriz de permisos
  en las historias de autenticación y permisos.

Las demás tablas (platos, menús, mesas, reservas, personal...) llegan con la migración de cada módulo.

## Migraciones

Toda modificación de estructura se hace con una migración versionada, nunca a mano.

| Comando | Para qué |
|---|---|
| `alembic upgrade head` | Aplicar todas las migraciones |
| `alembic downgrade base` | Volver a una base vacía (deja solo `alembic_version`) |
| `alembic current` | Ver la versión aplicada |
| `alembic check` | Comprobar que los modelos y la base de datos coinciden |
| `alembic revision --autogenerate -m "descripcion"` | Generar una migración nueva a partir de los modelos |

Después de autogenerar, **revisar siempre el archivo** antes de aplicarlo, y probar también el `downgrade`.
Los modelos nuevos deben importarse en `app/models/__init__.py` para que Alembic los vea.

> **Historial residual.** `alembic.ini` apunta únicamente a `app/database/migrations/`. El directorio
> `alembic/` de la raíz llegó con la fusión de `epic/authentication`, no está referenciado y su `env.py`
> no es ejecutable con el código actual. Se conserva de forma temporal porque otras ramas del equipo
> todavía lo usan; no debe contener migraciones nuevas ni usarse para generar revisiones.

## Seeders (`app/database/seeders/`)

Se ejecutan con `python -m app.database.seeders`, después de `alembic upgrade head`.

| Módulo | Carga |
|---|---|
| `restaurant.py` | Restaurante «Oído Cocina Demo», su configuración y 14 horarios (7 días × mañana y tarde) |
| `access.py` | Los 5 roles del briefing y un usuario demo por rol |
| `dishes.py` | Los 14 alérgenos de la UE y las categorías Entrantes, Primeros, Segundos, Bebidas y Postres |
| `runner.py` | Ejecuta todo en orden de dependencias y en una sola transacción |

**Idempotencia.** Cada fila se inserta solo si no existe, buscándola por su clave natural: código del alérgeno,
nombre del rol, email del usuario, restaurante + nombre de la categoría... Las filas existentes no se modifican
ni se vuelven a cifrar.

**Usuarios de demostración.** La contraseña de todos es la de `SEED_DEMO_PASSWORD` y se guarda cifrada con Argon2id.
Solo sirven para desarrollo.

| Rol | Email | Restaurante |
|---|---|---|
| `superadmin` | demo-superadmin@example.com | ninguno |
| `admin` | demo-admin@example.com | demo |
| `chef` | demo-chef@example.com | demo |
| `staff` | demo-staff@example.com | demo |
| `customer` | demo-customer@example.com | ninguno |

Si falta `SEED_DEMO_PASSWORD` y hay usuarios por crear, el seeder aborta sin guardar nada.

Los valores del restaurante demo son datos de ejemplo. En particular, el descanso mínimo entre turnos (720 minutos)
debe validarse con el convenio aplicable antes de darlo por bueno.

## Tests

```
python -m pytest
```

Necesitan la base migrada (`alembic upgrade head`) y usan la `DATABASE_URL` del `.env`, así que conviene que
apunte a la base local de desarrollo. Cada test se revierte al terminar y deja los datos como estaban. Si la base está
configurada pero sin migrar, fallan con un mensaje claro.

| Archivo | Comprueba |
|---|---|
| `tests/database/test_seeders_idempotency.py` | Ejecutar los seeders dos veces deja el mismo estado: mismos conteos, inserción de 0 filas en la segunda ejecución y contenido de las filas sin cambios |
| `tests/database/test_seeded_data.py` | Los 14 alérgenos, las categorías, el restaurante demo con su configuración y 14 horarios, un usuario por rol, contraseñas cifradas y el aborto si falta la contraseña |
| `tests/database/test_models.py` | Metadatos: 10 tablas, claves primarias y foráneas y relaciones del esquema normalizado |
| `tests/database/test_migrations.py` | Un único historial lineal; el SQL offline de `upgrade` crea las 10 tablas y el de `downgrade` las elimina |
| `tests/test_restaurant.py` | `Restaurant` solo guarda identidad y aplica los valores por defecto de la base de datos |
| `tests/test_restaurant_settings.py` | Una sola configuración por restaurante, valores por defecto, checks y relación con el restaurante |
| `tests/core/test_errors.py` | Formato de error común: 409, 422, 404 y 500 sin detalles internos |
| `tests/core/test_config.py` | Si falta `DATABASE_URL`, el programa termina con un mensaje claro |
| `tests/api/test_health.py` | `/api/v1/health` responde 200 y, si la base falla, 503 con el formato común y sin filtrar detalles |
| `tests/kernel/test_kernel_stubs.py` | Las firmas de la identidad provisional no cambian |

## Problemas frecuentes

| Síntoma | Causa probable |
|---|---|
| `Connection refused` | El servicio de PostgreSQL no está arrancado |
| `password authentication failed` | Usuario o contraseña distintos en `.env` y en PostgreSQL |
| `database "oido_cocina" does not exist` | Falta crear la base de datos (paso 1) |
| `ERROR de configuración: falta o no es válida la variable DATABASE_URL` | No existe `.env`, está vacío o no estás en la raíz del proyecto |
| `Can't locate revision identified by ...` | La base se creó con otro historial de Alembic. Recrearla: `DROP DATABASE` y `CREATE DATABASE`, y `alembic upgrade head` |
| `requires the httpx2 package` | Dependencias desactualizadas: `pip install -r requirements.txt` |
| `No module named 'argon2'` | Dependencias sin instalar: `pip install -r requirements.txt` |
| El seeder indica que falta `SEED_DEMO_PASSWORD` | Falta esa variable en `.env` |
| Los tests fallan con «database is not migrated» | Falta `alembic upgrade head` |