# Base de OICO-61: listado y creación de usuarios

Implementación parcial de HU-AUT-06. Incluye esquemas Pydantic y servicios de
listado paginado y creación sobre los modelos compartidos `User` y `Role`.
No añade modelos, tablas ni migraciones. El POST existente de `app/api/users.py`
consume este servicio; el listado HTTP y su ubicación definitiva en las rutas
del módulo siguen pendientes de OICO-61.

## Contrato de los servicios

- `list_users(db, restaurant_id, pagination)` devuelve `UserPage`, ordenado por ID
  y limitado al restaurante indicado. Página inicial 1, tamaño inicial 20 y máximo 100.
- `create_user(db, restaurant_id, payload)` devuelve `UserRead`. Requiere un rol
  existente del mismo restaurante y rechaza el rol compartido de superadministrador.
- El llamante debe obtener `restaurant_id` de la identidad autenticada del servidor
  y exigir `user:manage` en ambas operaciones. Los servicios no autentican ni
  autorizan peticiones y no deben exponerse directamente sin esas dependencias.
- La contraseña utiliza el helper compartido `app.core.passwords.hash_password`.
  Las respuestas solo contienen campos públicos. No se modifica el módulo de login.
- El índice compartido `uq_users_email_lower` establece la unicidad global del
  correo sin distinguir mayúsculas. La creación convierte esa colisión en un error
  409 genérico y revierte la transacción. Otros errores de integridad se propagan.

## Dependencias pendientes de integración

1. La devolución de `require_permission` se corrigió localmente con autorización
   explícita del usuario, tras coordinarse con Patri y Jesús. Las tres pruebas
   existentes del kernel pasan y la aplicación vuelve a cargar. La corrección
   está guardada en el commit `bde50c0`, incluido en esta entrega.
2. La rama del PR #20 integra la identidad JWT y los permisos reales del rol;
   no utiliza el usuario provisional en producción. Falta su revisión y fusión.
3. El POST `/api/v1/users` del PR #20 delega en este servicio, sin duplicar
   su implementación. Su autenticación y sus respuestas 201/409/403 están
   cubiertas por pruebas HTTP con usuarios persistidos y JWT reales.
4. La dependencia `email-validator==2.3.0`, necesaria para `EmailStr`, ya se instaló
   en `.venv` con autorización del usuario y se declaró en `requirements.txt`.
5. Una prueba HTTP crea un usuario mediante este servicio y verifica que puede
   iniciar sesión con el helper compartido. GET `/users` todavía está pendiente.

## Verificación

Pruebas preparadas en `tests/modules/users/`: validación de entrada, campos
protegidos, respuestas sin secretos, creación, duplicados, rollback, roles y
paginación por restaurante. Los casos con `Mock` verifican traducción de errores;
no representan una prueba de concurrencia real.

`tests/features/users.feature` describe escenarios de aceptación HTTP futuros.
Es documentación Gherkin y no un conjunto de pruebas ejecutadas automáticamente.

Se verificaron la sintaxis de los archivos y la conexión exclusiva a
`oido_cocina_test`. Tras corregir la devolución del comprobador de permisos,
las tres pruebas del kernel pasaron. Con `email-validator` instalado, pasaron
las 28 pruebas de esquemas y servicios de usuarios. La preparación de nuestros
tests usa un ID explícito para el segundo restaurante, compatible con la fixture
compartida que inserta el primero sin avanzar su secuencia PostgreSQL.

Después pasaron 350 pruebas en la suite disponible, incluidas las de usuarios,
con cero fallos y cero errores. Se excluyó `tests/database/test_migrations.py`
porque ejecuta Alembic. No se ejecutaron migraciones. Estos resultados validan
la base original de servicios y esquemas. Las correcciones posteriores del
PR #20 superaron 55 pruebas específicas de identidad, permisos y usuarios,
incluyendo el POST registrado. La ejecución global posterior superó 374 pruebas,
con cero fallos y cero errores, excluyendo las pruebas de migraciones.
OICO-61 no está completada: falta su listado HTTP.

## Fuera del alcance de esta base

PATCH de datos y rol, baja lógica, borrado físico, consulta de auditoría y servicio
general de auditoría corresponden a otras subtareas. El rechazo de superadministrador
al crear evita exponer esa operación mientras se implementan los controles completos
de gestión de roles. HU-AUT-06 no queda completada con esta base.
