# Cambios de los diagramas de flujo — Oído Cocina

Este documento acompaña a `docs/flujos/oido_cocina_flowchart.json` y registra los
cambios aprobados en el backlog compactado. El JSON conserva el diseño base; este
documento prevalece donde haya contradicción.

## 1. Lista de espera eliminada

- Se elimina la lista de espera del alcance.
- Desaparecen las referencias de las páginas 08, 09, 10, 11, 16 y 21.
- El estado `waitlisted` desaparece de la máquina de estados de la reserva.
- Cuando no hay mesa, la API responde `409` y no ofrece lista de espera.
- El no-show libera las mesas y no promociona ninguna entrada.
- `HU-RES-10` y sus cuatro subtareas se eliminaron de Jira.

## 2. Reservas con una o varias mesas

- Una reserva puede ocupar una mesa individual, una combinación configurada o varias
  mesas independientes.
- Cada mesa se bloquea mediante una ocupación en `reservation_tables`.
- La capacidad de una combinación es la capacidad real configurada, nunca la suma
  automática de sus mesas.
- En varias mesas independientes se usa la suma de capacidades máximas y no se venden
  sillas sobrantes.
- Preferencia de asignación: mesa individual > combinación > varias mesas independientes.
- Todas las mesas se bloquean en orden estable y se liberan juntas.
- Si falla una mesa, se revierte la reserva completa.

## 3. Estados y cortesía

- Estados: `pending`, `confirmed`, `seated`, `completed`, `cancelled`, `noShow`.
- `pending` bloquea la mesa hasta `start_at + courtesy_minutes`; después caduca.
- `confirmed` pasa a `noShow` si no hay llegada tras la cortesía.
- `completed`, `cancelled` y `noShow` liberan todas las mesas.
- Los estados finales son inmutables.
- La llegada simultánea se revalida bajo bloqueo antes de cambiar el estado.

## 4. Carta y menús

- `dishes` y `menus` tienen precio propio; el precio del menú no se deriva de sus platos.
- La cascada de un plato obligatorio inactivo deja el menú no disponible, registra el
  motivo y audita cada menú afectado en una sola transacción.
- La reactivación es manual y se bloquea con `409` si falta un plato obligatorio.
- La bebida incluida se marca en `menu_dishes`.
- Los alérgenos del menú son la unión de los alérgenos de sus platos, sin duplicados.
- El historial de precios cubre platos y menús.

## 5. Seguridad y auditoría

- El sobre de error es `{ "error": { "code", "message" } }`.
- `401` identidad inválida, `403` permiso insuficiente, `404` recurso ajeno o inexistente,
  `409` conflicto de estado, `422` validación.
- Un usuario tiene un solo rol; los permisos se comprueban por nombre.
- El logout y la desactivación incrementan `token_version`; el token anterior devuelve 401.
- La auditoría existe, pero es Should/recortable. No guarda secretos.

## 6. Configuración

- `restaurant_settings` y `opening_hours` son tablas separadas.
- Los descansos entre jornadas y el descanso semanal son configurables.
- Los cambios de configuración no reescriben reservas históricas.

## 7. Referencias

- `docs/modelo/cambios-der.md`: cambios del modelo de datos.
- `docs/backlog/matriz-fusion.md`: historias antiguas y su destino.
- `docs/backlog/00-convenciones.md`: reglas del backlog.
