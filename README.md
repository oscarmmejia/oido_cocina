<img width="2048" height="2048" alt="Gemini_Generated_Image_rvdkajrvdkajrvdk" src="https://github.com/user-attachments/assets/f43fd916-fd87-4163-b0af-9c01c21ac5f2" />

<p align="center">
  <img src="https://via.placeholder.com/800x160/0a0a0a/FF6600?text=%C2%A1O%C3%8DDO+COCINA!+%E2%80%A2+BYTE+%26+BITE" alt="Oído Cocina Banner" />
</p>

# 🍳 ¡OÍDO COCINA! — ERP de Gestión Operativa para Restaurantes
-----
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-FF6B00?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-121212?style=for-the-badge&logo=fastapi&logoColor=FF6B00" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-FF6B00?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-121212?style=for-the-badge&logo=sqlalchemy&logoColor=FF6B00" alt="SQLAlchemy" />
  <img src="https://img.shields.io/badge/Pydantic-v2-FF6B00?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic" />
  <img src="https://img.shields.io/badge/PyTest-26%20Passed-121212?style=for-the-badge&logo=pytest&logoColor=FF6B00" alt="PyTest" />
  <img src="https://img.shields.io/badge/Metodolog%C3%ADa-SCRUM-FF6B00?style=for-the-badge&logo=jira&logoColor=white" alt="SCRUM" />
</p>




---

## 📖 Índice

- [1. Descripción del Proyecto](#1-descripción-del-proyecto)
- [2. Arquitectura del Sistema](#2-arquitectura-del-sistema)
- [3. Flujo de una Petición](#3-flujo-de-una-petición)
- [4. Modelo de Datos (DER)](#4-modelo-de-datos-der)
- [5. Estructura del Repositorio](#6-estructura-del-repositorio)
- [6. Instalación y Puesta en Marcha](#7-instalación-y-puesta-en-marcha)
- [7. Migraciones y Seeders](#8-migraciones-y-seeders)
- [8. Referencia de la API](#9-referencia-de-la-api)
- [9. Pruebas Automatizadas](#10-pruebas-automatizadas)
- [10. Variables de Entorno](#11-variables-de-entorno)
- [11. Convenciones del Equipo](#12-convenciones-del-equipo)
- [12. Problemas Frecuentes](#13-problemas-frecuentes)
- [13. Equipo de Desarrollo](#15-equipo-de-desarrollo)
- [14. Licencia y Propósito Educativo](#16-licencia-y-propósito-educativo)

---

## 1. Descripción del Proyecto

**¡Oído Cocina!** es una plataforma ERP integral orientada a la gestión
operativa de restaurantes y cocinas profesionales. Resuelve los retos del
sector hostelero mediante un backend robusto, modular y altamente escalable:

- 🥗 **Gestión de Carta y Menús:** Publicación de platos con alérgenos
  estructurados de la UE, colecciones temporales y precios propios
  independientes.
- 📅 **Reservas e Integración:** Control de disponibilidad en tiempo real,
  prevención de *overbooking* e integración multi-canal.
- 🪑 **Distribución Flexible de Sala:** Asignación automática y manual de
  mesas completas e indivisibles para grupos en el restaurante.
- 🔐 **Autenticación y Seguridad (RBAC):** Control de acceso por roles
  (Superadministrador, Administrador, Gerente, Jefe de Cocina, Camarero) y
  separación estricta por local.
- ⏱️ **Horarios y Cuadrantes:** Planificación de jornadas partidas, turnos
  rotativos y descansos de cocina y personal.
- ⚙️ **Cero Configuración Rígida:** Horarios de apertura, tiempos de
  cortesía y reglas parametrizables por base de datos.

*"MVP entregado: autenticación JWT, RBAC con 5 roles y 17 permisos, y CRUD completo sobre carta, reservas, mesas, personal, usuarios y ajustes."*  

## 2. Arquitectura del Sistema

El sistema está diseñado como un **Monolito Modular** estructurado en capas
limpias. La petición HTTP nunca salta capas:

```text
+-----------------------------------------------------------------------+
|                     FastAPI — Routers (app/api)                      |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|              Pydantic — Schemas & Validación (app/schemas)            |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|           Controllers — Lógica de negocio (app/controllers)           |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|            SQLAlchemy ORM — Modelos y transacciones (app/models)      |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                          PostgreSQL 16                                |
+-----------------------------------------------------------------------+
```

**Reglas de la casa:**

- El **kernel** (`app/core/kernel`) concentra el contrato de errores,
  identidad, permisos y seed mínimo: es el acuerdo compartido entre todas
  las historias de usuario.
- Los **módulos de dominio** (`app/modules/...`) no se importan entre sí.
- Los **modelos compartidos** viven en `app/models` y no importan de
  módulos de dominio (hay tests que lo comprueban automáticamente).

## 3. Flujo de una Petición
```text
Petición HTTP del Cliente
          │
          ▼
 FastAPI + Esquemas Pydantic
          │
          ▼
   ┌─ ¿Entrada válida? ─┐
   │ NO                 │ SÍ
   ▼                    ▼
400 / 422        Autenticación y Permisos RBAC
 Bad Request           │
                ┌──────┴──────┐
         DENEGADO        PERMITIDO
                ▼              ▼
         401 / 403      Controller del Módulo
          Forbidden             │
                                ▼
                  SQLAlchemy ORM + Transacción
                                │
                    ┌─ ¿Operación correcta? ─┐
                    │ NO                     │ SÍ
                    ▼                        ▼
          Rollback + 404 / 409 / 500   Commit + 200 / 201 / 204
```


## 4. Modelo de Datos (DER)

La base de datos está organizada en **16 tablas** agrupadas en 5 áreas:

| Área | Tablas |
|------|--------|
| **Seguridad y configuración** | `restaurant`, `opening_hours`, `roles`, `permissions`, `role_permissions`, `users` |
| **Carta** | `categories`, `allergens`, `dishes`, `dish_allergens`, `menu_collections`, `menus`, `menu_dishes` |
| **Mesas y reservas** | `tables`, `table_combinations`, `table_combination_tables`, `reservations`, `reservation_tables`, `reservation_status_history` |
| **Horarios** | `employees`, `schedules`, `work_shifts`, `time_off_requests`, `shift_swap_requests` |
| **Trazabilidad** | `audit_logs`, `price_history` |

**Decisiones clave del diseño:**

- La configuración del restaurante (`courtesy_minutes`, `slot_minutes`,
  `min_break_between_shifts`) vive en la propia tabla `restaurant`.
- Relaciones N:M con **PK compuestas** (`dish_allergens`, `menu_dishes`,
  `role_permissions`): un alérgeno no se puede repetir en un plato.
- **Integridad en la base de datos**, no solo en código: precios ≥ 0,
  rangos de horario coherentes y constraint `EXCLUDE` que impide doble
  reserva de la misma mesa y turnos solapados del mismo empleado.
- Borrado lógico (`is_active`) en lugar de borrado físico: nada se
  destruye, todo se desactiva.

> El DER completo está en `docs/modelo/oido_cocina_er.json` y los cambios
> recogidos en `docs/modelo/cambios-der.md`.



## 5. Estructura del Repositorio

```text
oido_cocina/
├── app/
│   ├── api/                     # Routers: declaran los endpoints (FastAPI)
│   │   ├── dish_routes.py       #   Rutas de platos (interno y carta pública)
│   │   ├── category_routes.py   #   Rutas de categorías
│   │   ├── allergen_routes.py   #   Rutas de alérgenos
│   │   └── test_routes.py       #   Health check
│   ├── controllers/             # Lógica de negocio y transacciones
│   ├── schemas/                 # Validación y serialización (Pydantic)
│   ├── models/                  # Modelos ORM compartidos del dominio
│   ├── core/
│   │   ├── config.py            # Variables de entorno (Pydantic Settings)
│   │   ├── database_connection.py  # Engine, SessionLocal, get_db()
│   │   ├── errors/              # Errores HTTP unificados (legado)
│   │   └── kernel/              # Contrato compartido: errores, identidad,
│   │                            #   permisos y seed mínimo
│   ├── modules/                 # Módulos de dominio
│   │   ├── tables/              #   Mesas (models, schemas, services, routes)
│   │   └── settings/            #   Configuración del restaurante
│   └── database/
│       ├── seed.py              # CLI de seeders
│       └── seeders/             # Catálogos y datos demo (idempotentes)
├── alembic/                     # Migraciones versionadas de PostgreSQL
│   └── versions/
├── tests/
│   ├── test_dish*.py            # Unitarias e integración de la carta
│   ├── test_category.py         # Categorías
│   ├── test_allergen.py         # Catálogo de alérgenos
│   ├── modules/tables/          # Mesas
│   ├── kernel/                  # Contrato congelado del kernel
│   ├── database/                # Migraciones, idempotencia e imports
│   └── features/                # Escenarios Gherkin (.feature)
├── docs/                        # DER, informes e impacto entre ramas
├── .env.example                 # Plantilla de variables de entorno
├── requirements.txt             # Dependencias fijadas
└── README.md
```

## 6. Instalación y Puesta en Marcha

### Prerrequisitos

- **Python** 3.11+
- **PostgreSQL** 16+ (con la extensión `btree_gist`)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/oscarmmejia/oido_cocina.git
cd oido_cocina

# 2. Crear y activar el entorno virtual
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configurar el entorno
cp .env.example .env             # y edita DATABASE_URL con tus credenciales

```bash
cp .env.example .env
```

```bash
# .env
DATABASE_URL=postgresql+psycopg://<usuario>:<clave>@localhost:5432/oido_cocina_car03
TEST_DATABASE_URL=postgresql+psycopg://<usuario>:<clave>@localhost:5432/oido_cocina_test
SECRET_KEY=<valor aleatorio de 48 bytes>
```
```

Generación del valor:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

**Paso 6 · Esquema y datos iniciales** (en este orden):

```bash
python -m alembic upgrade head      # aplica las migraciones versionadas
python -m app.database.seed        # carga catálogos, roles, permisos y datos demo
```

**Paso 7 · Entorno de pruebas.** La base `oido_cocina_test` es desechable y se utiliza únicamente para ejecutar la suite. Antes de lanzarla, su esquema debe estar en la misma versión que el código:

```bash
python -m alembic upgrade head      # sobre oido_cocina_test
```

*Las pruebas vacían y recrean las tablas de esa base en cada ejecución; la base de desarrollo no se ve afectada.*


```


### Explorar la API

| Recurso | URL |
|---------|-----|
| Swagger UI (interactiva) | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |
| Health check | `GET http://127.0.0.1:8000/api/v1/health` |
```

## 7. Migraciones y Seeders

### Migraciones (Alembic)

```bash
alembic current        # ¿en qué revisión está mi base?
alembic upgrade head   # aplicar todos los cambios pendientes
alembic downgrade base # volver atrás (¡destructivo!: borra tablas y datos)
```

> Si tu base se creó con `create_all` (sin historial de Alembic), márcala
> antes de migrar: `alembic stamp <revisión-de-dev>` y después
> `alembic upgrade head`.

### Seeders (datos iniciales)

```bash
python -m app.database.seed              # catálogo + datos demo
python -m app.database.seed --no-demo    # solo catálogo y seguridad
python -m app.database.seed --reset      # limpia datos demo y vuelve a sembrar
```

Son **idempotentes**: se pueden ejecutar tantas veces como haga falta sin
duplicar filas. Cargan, entre otros:

- 🌾 **14 alérgenos** de declaración obligatoria en la Unión Europea
- 🔐 17 permisos y 5 roles (Superadministrador, Administrador, Gerente,
  Jefe de Cocina, Camarero)
- 🪑 6 mesas (incluida una de barra)
- 🍽️ 3 categorías, 5 platos, 2 colecciones y 2 menús
- 👥 5 usuarios y 5 empleados de demostración

## 8. Referencia de la API

| Módulo | Endpoints |
|---|---|
| Autenticación | `POST /auth/login`, `GET /auth/me` |
| Carta | platos (CRUD + estado + carta pública), categorías, alérgenos, **colecciones de menú** |
| Reservas | CRUD + confirmar / sentar / cancelar / completar, historial de estados, mesas y combinaciones |
| Personal | empleados (CRUD + activar), **cuadrantes y turnos** |
| Usuarios | listar, crear, **editar**, **cambiar rol**, **activar/inactivar** |
| Ajustes | `GET/PATCH /settings` |

> Prefijo base: `/api/v1`. Ejemplos con la carta de platos.

### Salud

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado de la aplicación y la base de datos |

### Carta — platos (interno)

| Método | Ruta | Descripción | Respuesta |
|--------|------|-------------|-----------|
| POST | `/dishes/` | Crear plato con categoría y alérgenos | 201 |
| GET | `/dishes/` | Listar platos del restaurante | 200 |
| GET | `/dishes/{id}` | Detalle con sus alérgenos | 200 |
| PATCH | `/dishes/{id}` | Editar campos y reemplazar alérgenos | 200 |
| PATCH | `/dishes/{id}/deactivate` | Baja lógica (409 si ya estaba inactivo) | 200 |
| PATCH | `/dishes/{id}/status` | Cambiar publicación / disponibilidad | 200 |

### Carta pública (cliente)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/dishes/public` | Carta paginada con filtros `?category_id=&allergen_id=&is_available=&page=&page_size=` |
| GET | `/dishes/public/{id}` | Detalle público de un plato |

### Categorías y alérgenos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST | `/categories/` | Listar y crear categorías |
| GET/PATCH | `/categories/{id}` | Consultar y editar |
| GET | `/allergens/` | Catálogo de 14 alérgenos UE |

### Ejemplo rápido

```bash
# Crear un plato
curl -X POST "http://127.0.0.1:8000/api/v1/dishes/?restaurant_id=1" \
  -H "Content-Type: application/json" \
  -d '{"name": "Croquetas de jamón", "price": 7.50,
       "category_id": 1, "allergen_ids": [1, 3]}'

# Consultar la carta pública
curl "http://127.0.0.1:8000/api/v1/dishes/public?restaurant_id=1&page=1"
```

**Códigos de error habituales:**

| Código | Significado |
|--------|-------------|
| 404 | El recurso no existe o es de otro restaurante |
| 409 | Conflicto (duplicado, ya desactivado, cuadrante con conflictos) |
| 422 | Datos inválidos (precio negativo, página 0, campos a `null`) |

## 9. Pruebas Automatizadas

```bash
source .venv/Scripts/activate   # imprescindible: si no, ModuleNotFoundError
pytest -q                        # resumen
python -m pytest -v              # detalle
```

**Estado actual: 639 pruebas ✅**

| Tipo | Ficheros | Qué cubren |
|------|----------|------------|
| Unitarias | `test_dish.py`, `test_category.py`, `test_allergen.py` | Validaciones y reglas de negocio |
| Carta pública | `test_dish_public.py` | Filtros, paginación y ocultación |
| Integración | `test_dish_integration.py` | Transacciones reales: o se guarda todo o nada |
| Kernel | `kernel/test_kernel_stubs.py` | Contrato congelado de identidad y permisos |
| Base de datos | `database/*` | Migraciones, idempotencia de seeders e imports sin ciclos |

**Regla del equipo:** cada funcionalidad nueva se entrega con sus pruebas
automatizadas **y** sus escenarios Gherkin en `tests/features/*.feature`
(lenguaje natural entendible por negocio).

## 10. Variables de Entorno

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+psycopg://usuario:clave@localhost:5432/oido_cocina` | Conexión a PostgreSQL (**obligatoria**) |
| `AUTH_STUBS_ENABLED` | `true` | Permisos en modo stub temporal (se retira con HU-AUT-05) |
| `SEED_ON_STARTUP` | `false` | Si es `true`, siembra datos en cada arranque |
| `SECRET_KEY` | **obligatoria** | Clave de 48 bytes para firmar los tokens de sesión. La aplicación no se inicia sin ella |

## 11. Convenciones del Equipo

- **Commits en inglés** con [Conventional Commits](https://www.conventionalcommits.org/):
  `feat:`, `fix:`, `test:`, `style:`, `docs:`, `refactor:`.
- **Arquitectura por capas**: la petición nunca salta capas
  (API → Schemas → Controllers → Models).
- **ORM sin SQL crudo**: toda consulta pasa por SQLAlchemy.
- **Borrado lógico, nunca físico**: se desactiva (`is_active = false`).
- **`tests/conftest.py` es kernel**: no se toca sin acuerdo del equipo.
- **Historias en Jira**: cada HU con sus ramas `feature/HU-XXX-...` → `dev`,
  revisada por otra persona antes de fusionar.
- **Identificadores en inglés**, comentarios de negocio en español.

## 12. Problemas Frecuentes

| Error | Causa | Solución |
|-------|-------|----------|
| `ModuleNotFoundError: fastapi` | Entorno virtual sin activar | `source .venv/Scripts/activate` |
| 422 al usar `?page=0` | El límite es `page >= 1` | Usa `?page=1` |
| `relation "..." does not exist` | Base sin migrar | `alembic upgrade head` |
| Falta la extensión `btree_gist` | PostgreSQL sin la extensión | `CREATE EXTENSION IF NOT EXISTS btree_gist;` |
| Puerto 8000 ocupado | Otro proceso usando el puerto | `uvicorn app.main:app --reload --port 8001` |


## 13. Equipo de Desarrollo

Proyecto diseñado y desarrollado por el equipo **Byte & Bite**:

<table align="center">
  <tr>
    <td align="center" width="160">
      <a href="https://github.com/apariciodiazpatricia-cell">
        <img src="https://github.com/apariciodiazpatricia-cell.png" width="90px" style="border-radius: 50%;" alt="Patricia Aparicio Díaz"/><br />
        <sub><b>Patricia Aparicio Díaz</b></sub>
      </a><br />
      <small>Backend Developer</small>
    </td>
    <td align="center" width="160">
      <a href="https://github.com/mjrr39sevilla">
        <img src="https://github.com/mjrr39sevilla.png" width="90px" style="border-radius: 50%;" alt="María José Rodríguez Ramos"/><br />
        <sub><b>Mª José Rodríguez</b></sub>
      </a><br />
      <small>Backend Developer</small>
    </td>
    <td align="center" width="160">
      <a href="https://github.com/oscarmmejia">
        <img src="https://github.com/oscarmmejia.png" width="90px" style="border-radius: 50%;" alt="Óscar Mejía"/><br />
        <sub><b>Óscar Mejía</b></sub>
      </a><br />
      <small>Backend Developer</small>
    </td>
    <td align="center" width="160">
      <a href="https://github.com/Mltiformacionjose">
        <img src="https://github.com/Mltiformacionjose.png" width="90px" style="border-radius: 50%;" alt="José Loero Nielez"/><br />
        <sub><b>José Loero</b></sub>
      </a><br />
      <small>Backend Developer</small>
    </td>
    <td align="center" width="160">
      <a href="https://github.com/Willfredy742">
        <img src="https://github.com/Willfredy742.png" width="90px" style="border-radius: 50%;" alt="Wilfredy Salcedo"/><br />
        <sub><b>Wilfredy Salcedo</b></sub>
      </a><br />
      <small>Backend Developer</small>
    </td>
    <td align="center" width="160">
      <a href="https://github.com/El-Jesule">
        <img src="https://github.com/El-Jesule.png" width="90px" style="border-radius: 50%;" alt="Jesús"/><br />
        <sub><b>Jesús</b></sub>
      </a><br />
      <small>Backend Developer</small>
    </td>
  </tr>
</table>

---

## 14. Licencia y Propósito Educativo

**Licencia:** Sin licencia — proyecto de uso exclusivamente educativo.
© 2026 Byte & Bite. Todos los derechos reservados.

- **Naturaleza del Proyecto:** desarrollado en el marco del programa
  formativo de **Full Stack Web Development**, con fines académicos y de
  experimentación tecnológica.
- **Ámbito de Aplicación:** **Oído Cocina** opera como entorno simulado de
  un ERP para el sector de la restauración. Su arquitectura, modelos de
  datos e integraciones están diseñados para validar competencias
  avanzadas en ingeniería de software y desarrollo backend.
- **Uso No Comercial:** las funcionalidades tienen carácter demostrativo y
  formativo, reflejando las buenas prácticas del equipo **Byte & Bite**
  en metodologías ágiles, control de calidad y diseño escalable.

---
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:FF8800,100:FF6B00&height=50&section=header&reversal=true" width="100%" />
</p>
