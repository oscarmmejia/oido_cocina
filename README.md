# Oído Cocina

Backend (FastAPI + PostgreSQL) para la gestión de restaurantes.

## Puesta en marcha de la base de datos

Desde la raíz del proyecto:

1. Crear el entorno e instalar dependencias:
   `python -m venv .venv && .venv\Scripts\activate` (Windows) o `source .venv/bin/activate`,
   y después `pip install -r requirements.txt`.
2. Copiar `.env.example` a `.env` y rellenar `DATABASE_URL` (formato `postgresql+psycopg://...`)
   y `SEED_DEMO_PASSWORD`. El `.env` no se sube al repositorio.
3. Crear las tablas: `alembic upgrade head`.
4. Cargar los datos de demostración: `python -m app.database.seeders`.
   Se puede ejecutar varias veces: no duplica datos.
5. Volver a una base vacía: `alembic downgrade base`.

## Migraciones

- Toda modificación de estructura se hace con una migración versionada, nunca a mano:
  `alembic revision --autogenerate -m "descripcion"`. Revisar siempre el resultado antes de aplicarlo.
- `alembic check` indica si los modelos y la base de datos han dejado de coincidir.

## Seeders (`app/database/seeders/`)

| Módulo | Carga |
|---|---|
| `restaurant.py` | Restaurante demo, su configuración y sus horarios |
| `access.py` | Los 5 roles del briefing y un usuario demo por rol |
| `dishes.py` | Los 14 alérgenos de la UE y las categorías iniciales |

Cada fila se inserta solo si no existe, usando su clave natural
(código de alérgeno, nombre de rol, email, restaurante + nombre de categoría...).

## Tests

`python -m pytest` (necesita la base migrada con `alembic upgrade head`). Cada test se revierte al terminar.
Las pruebas de base de datos están en `tests/database/`; `test_seeders_idempotency.py` comprueba que ejecutar
los seeders dos veces deja el mismo estado (conteos y contenido de las filas).
