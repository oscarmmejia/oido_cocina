# Cambios del modelo entidad-relación — Oído Cocina

Este documento acompaña a `docs/modelo/oido_cocina_er.json` y registra las decisiones
del backlog compactado. El JSON es el diagrama base; este documento es la fuente de
las diferencias aprobadas.

## Decisiones de modelo

1. **Un rol por usuario.** `users.role_id` sustituye a la tabla intermedia `user_roles`.
   Los permisos siguen siendo granulares: `roles`, `permissions` y `role_permissions`.
2. **Una reserva puede ocupar una o varias mesas.** Se añaden `reservation_tables`
   (ocupaciones por mesa) y `table_combinations` + `table_combination_tables`.
   `reservations.table_id` desaparece; la mesa se resuelve por ocupaciones.
3. **Sin lista de espera.** Se elimina `waitlist_entries` y el estado `waitlisted`.
   `HU-RES-10` y sus cuatro subtareas se eliminaron de Jira.
4. **Precio en platos y menús.** `dishes.price` y `menus.own_price` son independientes.
   `price_history` cubre ambos con `entity_type` (`dish` o `menu`).
5. **Una reserva `pending` bloquea sus mesas** hasta `start_at + courtesy_minutes`.
6. **La auditoría existe, pero es Should.** `audit_logs` guarda autor, acción, entidad,
   valores anterior/nuevo, resultado y fecha; no guarda secretos.
7. **Configuración separada.** `restaurant_settings` y `opening_hours` son tablas
   propias; no se mezclan con `restaurant`.

## Tablas y campos añadidos o modificados

### Seguridad y configuración

- `users`: `role_id` (FK a `roles`), `email` único, `password_hash`, `is_active`,
  `token_version`, `restaurant_id`, columnas de auditoría.
- `roles`, `permissions`, `role_permissions`: permisos con nombre y relación N:M.
- `restaurant_settings`: cortesía, duración de franja, duración de reserva,
  descanso mínimo entre turnos y descanso semanal.
- `opening_hours`: día, periodo mañana/tarde, apertura, cierre y cierre de cocina.

### Carta

- `categories`: nombre único por restaurante, orden y estado.
- `allergens`: catálogo común con código único y nombre.
- `dishes`: descripción, precio, categoría, `is_active`, `is_published`, `is_available`.
- `dish_allergens`: clave compuesta plato-alérgeno.
- `menu_collections`: nombre, tipo, `valid_from`, `valid_to`, estado.
- `menus`: colección, nombre, `own_price`, `is_active`, `is_available`, `inactive_reason`.
- `menu_dishes`: rol, `is_required`, marca de bebida incluida.

### Mesas y reservas

- `tables`: número único por restaurante, capacidad mínima/máxima, ubicación
  interior/exterior/bar, `is_enabled`, `is_capacity_adjustable`.
- `table_combinations`: capacidad real explícita, rango de uso y estado.
- `table_combination_tables`: mesas integrantes de cada combinación.
- `reservations`: cliente, teléfono, email, comensales, inicio, fin, estado,
  `combination_id`, autor y fecha de creación.
- `reservation_tables`: reserva, mesa, inicio, fin y estado de la ocupación.
- `reservation_status_history`: estado anterior, estado nuevo, autor, fecha y motivo.

### Horarios

- `employees`: restaurante, usuario opcional, nombre, puesto y estado.
- `schedules`: periodo, estado, responsable y fecha de publicación.
- `shifts`: cuadrante, empleado, inicio, fin, tipo y estado.
- `time_off_requests`: empleado, tipo, intervalo, estado, resolución y motivo.
- `shift_swap_requests`: turno origen, turno destino, estado y resolución.

### Trazabilidad

- `audit_logs`: autor, acción, entidad, `entity_id`, valores anterior/nuevo, resultado
  y fecha.
- `price_history`: `entity_type`, `entity_id`, precio anterior, precio nuevo, autor y fecha.

## Restricciones que garantiza la base de datos

- Número de mesa único por restaurante.
- Capacidad mínima ≥ 1 y máxima ≥ mínima.
- Precio de plato y menú ≥ 0.
- Email de usuario único.
- Alérgeno no repetido por plato; plato no repetido por menú.
- EXCLUDE por mesa y rango temporal sobre `reservation_tables` para reservas activas.
- EXCLUDE por empleado y rango temporal sobre `shifts`.
- Índice único parcial para reservas duplicadas por contacto, fecha y estado activo.

## Decisiones pendientes

- Cálculo exacto del descanso semanal y su periodo de referencia.
- Modalidad de reserva pública (invitado, con cuenta o ambas).
- Duración exacta del token y política de rotación.
- Tratamiento de cambios de configuración sobre reservas ya creadas.

Estas decisiones no bloquean el backlog actual: las historias implicadas leen la
configuración y aplican valores por defecto documentados.
