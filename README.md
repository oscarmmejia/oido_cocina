<img width="2048" height="2048" alt="Gemini_Generated_Image_rvdkajrvdkajrvdk" src="https://github.com/user-attachments/assets/f43fd916-fd87-4163-b0af-9c01c21ac5f2" />
```
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
- [2. Arquitectura del Sistema & Monolito Modular](#2-arquitectura-del-sistema--monolito-modular)
- [3. Flujo General de Ejecución (Backend)](#3-flujo-general-de-ejecución-backend)
- [4. Modelo Relacional de Base de Datos (DER)](#4-modelo-relacional-de-base-de-datos-der)
- [5. Estructura del Repositorio](#5-estructura-del-repositorio)
- [6. Instalación y Despliegue en Local](#6-instalación-y-despliegue-en-local)
- [7. Batería de Pruebas (PyTest)](#7-batería-de-pruebas-pytest)
- [8. Estado de Desarrollo & Estrategia de Entrega](#8-estado-de-desarrollo--estrategia-de-entrega)
- [9. Equipo de Desarrollo](#9-equipo-de-desarrollo)

---

## 1. Descripción del Proyecto
**¡Oído Cocina!** es una plataforma ERP integral orientada a la gestión operativa de restaurantes y cocinas profesionales. Resuelve los retos del sector hostelero mediante un backend robusto, modular y altamente escalable:
- 🥗 **Gestión de Carta y Menús:** Publicación de platos con alérgenos estructurados de la UE, colecciones temporales y precios propios independientes.
- 📅 **Reservas e Integración:** Control de disponibilidad en tiempo real, prevención de *overbooking* e integración multi-canal.
- 🪑 **Distribución Flexible de Sala:** Asignación automática y manual de mesas completas e indivisibles para grupos en el restaurante.
- 🔐 **Autenticación y Seguridad (RBAC):** Control de acceso por roles (Superadmin, Gerente, Chef, Sala, Cliente) y separación estricta por local.
- ⏱️ **Horarios y Cuadrantes:** Planificación de jornadas partidas, turnos rotativos y descansos de cocina y personal.
- ⚙️ **Cero Configuración Rígida:** Horarios, tiempos de cortesía y reglas parametrizadas por base de datos (`restaurant_settings`).

---

## 2. Arquitectura del Sistema & Monolito Modular
El sistema está diseñado como un **Monolito Modular** estructurado en capas limpias:
```text
+-----------------------------------------------------------------------+
|                           FastAPI (Routing)                           |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                       Pydantic (Schemas & Validation)                |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                    Controllers (Business Logic & Auth)                |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                   SQLAlchemy ORM (Data Access & Models)               |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                        PostgreSQL 16 Database                         |
+-----------------------------------------------------------------------+

```
3. Flujo General de Ejecución (Backend)
Representación del flujo de procesamiento de peticiones HTTP en el servidor:
```
flowchart TD
    A[Petición HTTP del Cliente] --> B[FastAPI + Esquemas Pydantic]
    B -->|¿Entrada válida?| C{Validación}
    C -->|No| D[400 / 422 Bad Request]
    C -->|Sí| E[Autenticación & Permisos RBAC]
    E -->|Acceso Denegado| F[401 / 403 Forbidden]
    E -->|Acceso Permitido| G[Servicio / Controlador del Módulo]
    G --> H[SQLAlchemy ORM + Transacción DB]
    H -->|¿Operación correcta?| I{Persistencia}
    I -->|Fallo / Conflicto| J[Rollback + 404 / 409 / 500]
    I -->|Éxito| K[Commit + 200 / 201 / 204 JSON Response]
```
4. Modelo Relacional de Base de Datos (DER)
La base de datos PostgreSQL está organizada en 5 columnas lógicas (Left to Right):

Catálogos Base: restaurants, roles, allergens.

Configuración Local: restaurant_settings, opening_hours, tables, users.

Carta y Personal: categories, dishes, employees.

Colecciones y Reservas: menu_collections, menus, reservations, schedules.

Relaciones N:M e Historial: menu_dishes, dish_allergens, reservation_status_history, work_shifts, audit_logs.

5. Estructura del Repositorio
```
oido_cocina/
├── app/
│   ├── api/                    # Routers y declaración de endpoints (FastAPI)
│   │   ├── dish_routes.py      # Rutas del CRUD de Platos
│   │   └── test_routes.py      # Endpoints de salud (Health Check)
│   ├── controllers/            # Lógica de negocio y transacciones
│   │   ├── dish_controller.py  # Operaciones CRUD de platos y alérgenos
│   │   └── test_controller.py  # Controlador de diagnóstico de base de datos
│   ├── core/                   # Configuración central y kernel del ERP
│   │   ├── config.py           # Gestión de variables de entorno (Pydantic Settings)
│   │   ├── database_connection.py # Engine, SessionLocal y get_db()
│   │   └── kernel/             # Contrato de errores, identity y stubs temporales
│   ├── models/                 # Modelos de dominio ORM (SQLAlchemy)
│   │   ├── dish_model.py       # Modelo Dish (tabla 'dishes')
│   │   └── dish_allergen_model.py # Tabla intermedia 'dish_allergens'
│   ├── schemas/                # Validación y serialización DTO (Pydantic)
│   │   ├── dish_schema.py      # DishCreate, DishUpdate, DishResponse
│   │   └── test_schema.py      # HealthResponse
│   └── main.py                 # Punto de entrada de la app FastAPI
├── tests/                      # Suite automatizada de pruebas
│   ├── test_dish.py            # 20 pruebas unitarias de lógica y esquemas
│   ├── test_dish_integration.py # 4 pruebas de integración con SQLite
│   └── features/               # Escenarios de aceptación Gherkin (dish.feature)
├── .env.example                # Plantilla de configuración de variables
├── .gitignore                  # Exclusiones de Git
├── README.md                   # Documentación principal
└── requirements.txt            # Lista de dependencias fijadas del proyecto
```
6. Instalación y Despliegue en Local
Prerrequisitos
Python: 3.11+

PostgreSQL: 16+

Pasos de Configuración
Clonar el repositorio:
```
git clone [https://github.com/oscarmmejia/oido_cocina.git](https://github.com/oscarmmejia/oido_cocina.git)
cd oido_cocina
```
Crear y activar el entorno virtual:
```
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```
Instalar dependencias:
```
pip install --upgrade pip
pip install -r requirements.txt
```
Configurar el entorno:
```
cp .env.example .env
```
(Edita .env para ajustar la conexión a PostgreSQL).

Arrancar el servidor de desarrollo:
```
uvicorn app.main:app --reload
```
Explorar la documentación interactiva:

Swagger UI: http://127.0.0.1:8000/docs

ReDoc: http://127.0.0.1:8000/redoc

---

## 7. Batería de Pruebas (PyTest)
Ejecuta la suite automatizada con el siguiente comando:
`python -m pytest -v`

**Resumen del Estado de Pruebas:**
- **Pruebas Unitarias** (`tests/test_dish.py`): 20 pruebas — ✅ **PASSED**
- **Pruebas de Integración** (`tests/test_dish_integration.py`): 4 pruebas — ✅ **PASSED**
- **Kernel Stubs** (`tests/kernel/test_kernel_stubs.py`): 2 pruebas — ✅ **PASSED**
- **TOTAL:** 26 pruebas — ✅ **100% OK**

---

## 8. Estado de Desarrollo & Estrategia de Entrega
Actualmente, el equipo se encuentra evaluando de forma activa la mejor ruta de trabajo e integración funcional para abordar la presentación y el cierre del alcance requerido. Se prioriza la solidez técnica, la cobertura de pruebas automatizadas y la arquitectura limpia sobre la velocidad de entrega, garantizando que cada módulo integrado cumpla con los estándares de calidad definidos en el briefing maestro del restaurante.

---

## 9. Equipo de Desarrollo
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

-----
---

### 🏛️ Propósito Educativo e Institucional

* **Naturaleza del Proyecto**: Este software ha sido desarrollado en el marco del programa formativo de **Full Stack Web Development**, concebido y ejecutado con estrictos fines académicos y de experimentación tecnológica.
* **Ámbito de Aplicación**: **Oído Cocina** opera como un entorno simulado de planificación de recursos empresariales (ERP) para el sector de la restauración. Su arquitectura, modelos de datos e integraciones están diseñados para validar competencias avanzadas en ingeniería de software, arquitectura backend y desarrollo de interfaces.
* **Uso No Comercial**: Las funcionalidades implementadas tienen un carácter puramente demostrativo y formativo, reflejando las buenas prácticas del equipo de desarrollo **Byte & Bite** en la aplicación de metodologías ágiles, control de calidad y diseño de sistemas escalables.


---
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:FF8800,100:FF6B00&height=50§ion=header&reversal=true" width="100%" />
</p>
