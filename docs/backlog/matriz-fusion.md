# Matriz de fusión del backlog — Oído Cocina

Documento generado a partir del backup histórico y del estado final de Jira.

## Resumen

| Métrica | Valor |
|---|---|
| Historias antiguas | 55 |
| Historias nuevas | 26 |
| Historias renumeradas | 10 |
| Historias absorbidas | 29 (eliminadas de Jira tras la fusión) |
| Historias eliminadas | 1 (`HU-RES-10`) |
| Historias añadidas | 1 (`HU-GES-06`, ya existía en Jira) |
| Puntos nuevos | 319 |
| Sprint 1 | 7 historias · 36 subtareas · 55 puntos |
| Sprint 2 | 19 historias · 144 subtareas · 264 puntos |
| Incidencias finales en Jira | 211 (5 épicas + 26 HU + 180 ST) |

Las HU de cada área están numeradas de forma consecutiva: `GES-01..06`, `AUT-01..06`, `CAR-01..05`, `HOR-01..04` y `RES-01..05`. Las claves `OICO-xxx` no cambian. Las 29 historias absorbidas se eliminaron de Jira; el mapa histórico queda aquí y en la sección `ABSORBE` de cada HU activa.

## Historias antiguas y su destino

| HU antigua | Clave antigua | Título | Estado en la fusión | Responsable | Destino | Efecto |
|---|---|---|---|---|---|---|
| `HU-GES-01` | `OICO-2` | Briefing funcional y técnico consolidado | Listo | Oscar Mauricio Mejia | `HU-GES-01` | Se mantiene como historia principal |
| `HU-GES-02` | `OICO-7` | Repositorio, ramas y convenciones de trabajo | Listo | Maria Jose Rodríguez Ramos | `HU-GES-02` | Se mantiene como historia principal |
| `HU-GES-03` | `OICO-13` | Modelo entidad-relación | Listo | Jesús González Gómez | `HU-GES-03` | Se mantiene como historia principal |
| `HU-GES-04` | `OICO-18` | Diagramas de flujo de los procesos críticos | Listo | Jose Loero Nielez | `HU-GES-04` | Se mantiene como historia principal |
| `HU-GES-05` | `OICO-24` | Backlog priorizado y trazabilidad de requisitos | Listo | Willfredy Sacedo | `HU-GES-05` | Se mantiene como historia principal |
| `HU-AUT-01` | `OICO-30` | Kernel del backend: estructura, errores y stubs | Listo | Maria Jose Rodríguez Ramos | `HU-AUT-01` | Se mantiene; absorbe `HU-AUT-09`, `HU-AUT-11` |
| `HU-AUT-02` | `OICO-35` | Esquema de datos completo, modelos compartidos y seeders | En curso | Jose Loero Nielez | `HU-AUT-02` | Se mantiene como historia principal |
| `HU-AUT-03` | `OICO-40` | Restaurante, configuración y horarios de apertura | En curso | Oscar Mauricio Mejia | `HU-AUT-03` | Se mantiene como historia principal |
| `HU-AUT-04` | `OICO-47` | Sesión completa: login, perfil, logout y revocación | En curso | Willfredy Sacedo | `HU-AUT-04` | Se mantiene; absorbe `HU-AUT-10` |
| `HU-AUT-05` | `OICO-54` | Roles, permisos y ámbito multi-restaurante | En curso | Willfredy Sacedo | `HU-AUT-05` | Se mantiene; absorbe `HU-AUT-07` |
| `HU-AUT-06` | `OICO-60` | Usuarios y auditoría administrativa | Por hacer | Willfredy Sacedo | `HU-AUT-06` | Se mantiene; absorbe `HU-AUT-08` |
| `HU-AUT-07` | `OICO-66` | Ámbito por restaurante y propiedad del recurso | Listo | — | `HU-AUT-05` | Absorbida en `HU-AUT-05` |
| `HU-AUT-08` | `OICO-70` | Auditoría de acciones administrativas | Listo | — | `HU-AUT-06` | Absorbida en `HU-AUT-06` |
| `HU-AUT-09` | `OICO-75` | Contrato de errores único de la API | Listo | Maria Jose Rodríguez Ramos | `HU-AUT-01` | Absorbida en `HU-AUT-01` |
| `HU-AUT-10` | `OICO-79` | Cierre de sesión y revocación de acceso | Listo | — | `HU-AUT-04` | Absorbida en `HU-AUT-04` |
| `HU-AUT-11` | `OICO-251` | Stubs y contratos del kernel para desbloquear los flujos | Listo | Maria Jose Rodríguez Ramos | `HU-AUT-01` | Absorbida en `HU-AUT-01` |
| `HU-CAR-01` | `OICO-84` | Categorías y catálogo de alérgenos | En curso | Patricia Aparicio Diaz | `HU-CAR-01` | Se mantiene; absorbe `HU-CAR-02` |
| `HU-CAR-02` | `OICO-89` | Catálogo estructurado de alérgenos | Listo | Patricia Aparicio Diaz | `HU-CAR-01` | Absorbida en `HU-CAR-01` |
| `HU-CAR-03` | `OICO-93` | Platos: CRUD, alérgenos, estados y carta pública | En curso | Patricia Aparicio Diaz | `HU-CAR-02` | Renumerada como `HU-CAR-02` |
| `HU-CAR-04` | `OICO-99` | Estados del plato y baja lógica | Listo | Patricia Aparicio Diaz | `HU-CAR-02` | Absorbida en `HU-CAR-02` |
| `HU-CAR-05` | `OICO-104` | Carta pública con filtros | Listo | Patricia Aparicio Diaz | `HU-CAR-02` | Absorbida en `HU-CAR-02` |
| `HU-CAR-06` | `OICO-108` | Colecciones de menú: CRUD y borrado condicionado | Por hacer | — | `HU-CAR-03` | Renumerada como `HU-CAR-03` |
| `HU-CAR-07` | `OICO-113` | Menús: CRUD, precio, composición, alérgenos, ciclo de vida y cascada | Por hacer | — | `HU-CAR-04` | Renumerada como `HU-CAR-04` |
| `HU-CAR-08` | `OICO-119` | Composición del menú y bebida incluida | Listo | — | `HU-CAR-04` | Absorbida en `HU-CAR-04` |
| `HU-CAR-09` | `OICO-125` | Cascada al desactivar un plato | Listo | Patricia Aparicio Diaz | `HU-CAR-04` | Absorbida en `HU-CAR-04` |
| `HU-CAR-10` | `OICO-130` | Inactivar un menú con motivo y reactivarlo | Listo | — | `HU-CAR-04` | Absorbida en `HU-CAR-04` |
| `HU-CAR-11` | `OICO-134` | Historial de precios de platos y menús | Por hacer | Patricia Aparicio Diaz | `HU-CAR-05` | Renumerada como `HU-CAR-05` |
| `HU-CAR-12` | `OICO-138` | Alérgenos agregados del menú | Listo | — | `HU-CAR-04` | Absorbida en `HU-CAR-04` |
| `HU-CAR-13` | `OICO-256` | Eliminar una colección sin menús | Listo | — | `HU-CAR-03` | Absorbida en `HU-CAR-03` |
| `HU-HOR-01` | `OICO-142` | Empleados: CRUD y estado laboral | En revisión | Maria Jose Rodríguez Ramos | `HU-HOR-01` | Se mantiene como historia principal |
| `HU-HOR-02` | `OICO-147` | Cuadrantes y turnos: CRUD, nocturnos, jornada partida y borrado | En curso | Maria Jose Rodríguez Ramos | `HU-HOR-02` | Se mantiene; absorbe `HU-HOR-03`, `HU-HOR-08`, `HU-HOR-11`, `HU-HOR-12` |
| `HU-HOR-03` | `OICO-151` | Turnos, incluidos los nocturnos | Listo | Maria Jose Rodríguez Ramos | `HU-HOR-02` | Absorbida en `HU-HOR-02` |
| `HU-HOR-04` | `OICO-156` | Validación, descansos y publicación de cuadrantes | Por hacer | — | `HU-HOR-03` | Renumerada como `HU-HOR-03` |
| `HU-HOR-05` | `OICO-160` | Ausencias y cambios de turno | Por hacer | — | `HU-HOR-04` | Renumerada como `HU-HOR-04` |
| `HU-HOR-06` | `OICO-166` | Validación previa a la publicación | Listo | — | `HU-HOR-03` | Absorbida en `HU-HOR-03` |
| `HU-HOR-07` | `OICO-172` | Publicación del cuadrante y horario propio | Listo | — | `HU-HOR-03` | Absorbida en `HU-HOR-03` |
| `HU-HOR-08` | `OICO-177` | Jornada partida | Listo | — | `HU-HOR-02` | Absorbida en `HU-HOR-02` |
| `HU-HOR-09` | `OICO-180` | Cambio de turno entre empleados | Listo | — | `HU-HOR-04` | Absorbida en `HU-HOR-04` |
| `HU-HOR-10` | `OICO-186` | Descansos mínimos configurables | Listo | Oscar Mauricio Mejia | `HU-HOR-03` | Absorbida en `HU-HOR-03` |
| `HU-HOR-11` | `OICO-259` | Eliminar un turno del cuadrante | Listo | Maria Jose Rodríguez Ramos | `HU-HOR-02` | Absorbida en `HU-HOR-02` |
| `HU-HOR-12` | `OICO-261` | Eliminar un cuadrante en borrador | Listo | Maria Jose Rodríguez Ramos | `HU-HOR-02` | Absorbida en `HU-HOR-02` |
| `HU-RES-01` | `OICO-191` | Mesas y combinaciones: CRUD, capacidades y habilitación | En curso | Jesús González Gómez | `HU-RES-01` | Se mantiene; absorbe `HU-RES-02` |
| `HU-RES-02` | `OICO-196` | Habilitar e inhabilitar mesas | Listo | Jesús González Gómez | `HU-RES-01` | Absorbida en `HU-RES-01` |
| `HU-RES-03` | `OICO-200` | Disponibilidad, asignación automática e informes | Por hacer | Oscar Mauricio Mejia | `HU-RES-02` | Renumerada como `HU-RES-02` |
| `HU-RES-04` | `OICO-205` | Reservas: CRUD completo, estados, historial, edición y multi-mesa | Por hacer | Jesús González Gómez | `HU-RES-03` | Renumerada como `HU-RES-03` |
| `HU-RES-05` | `OICO-211` | Concurrencia, anti-solapamiento y duplicados multi-mesa | Por hacer | Jesús González Gómez | `HU-RES-04` | Renumerada como `HU-RES-04` |
| `HU-RES-06` | `OICO-218` | Prevención de reservas duplicadas | Listo | — | `HU-RES-04` | Absorbida en `HU-RES-04` |
| `HU-RES-07` | `OICO-221` | Máquina de estados e historial de la reserva | Listo | — | `HU-RES-03` | Absorbida en `HU-RES-03` |
| `HU-RES-08` | `OICO-226` | Transiciones: confirmar, sentar, completar y cancelar | Listo | — | `HU-RES-03` | Absorbida en `HU-RES-03` |
| `HU-RES-09` | `OICO-230` | Cortesía y no-show | Por hacer | Oscar Mauricio Mejia | `HU-RES-05` | Renumerada como `HU-RES-05` |
| `HU-RES-10` | `—` | — | — | — | `—` | **Eliminada** con sus subtareas |
| `HU-RES-11` | `OICO-242` | Informes de ocupación y disponibilidad | Listo | — | `HU-RES-02` | Absorbida en `HU-RES-02` |
| `HU-RES-12` | `OICO-247` | Asignación automática de mesa | Listo | — | `HU-RES-02` | Absorbida en `HU-RES-02` |
| `HU-RES-13` | `OICO-264` | Listado y consulta de reservas | Listo | Jesús González Gómez | `HU-RES-03` | Absorbida en `HU-RES-03` |
| `HU-RES-14` | `OICO-267` | Edición de reserva con revalidación | Listo | Jesús González Gómez | `HU-RES-03` | Absorbida en `HU-RES-03` |

## Historias nuevas

| Épica | HU nueva | Clave Jira | Título | Pts | Sprint | Estado final | Absorbe | Requisitos |
|---|---|---|---|---:|---|---|---|---|
| EP-05 | `HU-GES-01` | `OICO-2` | Briefing funcional y técnico consolidado | 7 | 1 | Listo | — | — |
| EP-05 | `HU-GES-02` | `OICO-7` | Repositorio, ramas y convenciones de trabajo | 6 | 1 | Listo | — | — |
| EP-05 | `HU-GES-03` | `OICO-13` | Modelo entidad-relación | 8 | 1 | Listo | — | — |
| EP-05 | `HU-GES-04` | `OICO-18` | Diagramas de flujo de los procesos críticos | 7 | 1 | Listo | — | — |
| EP-05 | `HU-GES-05` | `OICO-24` | Backlog priorizado y trazabilidad de requisitos | 6 | 1 | Listo | — | — |
| EP-05 | `HU-GES-06` | `OICO-271` | Documentación, presentación y README | 5 | 1 | Listo | — | — |
| EP-02 | `HU-AUT-01` | `OICO-30` | Kernel del backend: estructura, errores y stubs | 16 | 1 | Listo | `HU-AUT-09`, `HU-AUT-11` | RNF-01, RNF-02, RNF-07, RNF-08; AUT-01, AUT-02, AUT-03, AUT-04 |
| EP-02 | `HU-AUT-02` | `OICO-35` | Esquema de datos completo, modelos compartidos y seeders | 21 | 2 | En curso | — | RF-PLA, RF-MEN, RF-MES, RF-RES, RF-CFG, RF-USR, RF-HOR; RNF-04, RNF-07 |
| EP-02 | `HU-AUT-03` | `OICO-40` | Restaurante, configuración y horarios de apertura | 13 | 2 | En curso | — | RF-CFG-01, RF-CFG-02, RF-CFG-03, RF-CFG-04, RF-CFG-05, RF-CFG-06, RF-CFG-07; CFG-01, CFG-02, CFG-03, CFG-04; RES-02 |
| EP-02 | `HU-AUT-04` | `OICO-47` | Sesión completa: login, perfil, logout y revocación | 13 | 2 | En curso | `HU-AUT-10` | RF-USR-07; AUT-01, AUT-02, AUT-03, AUT-04, AUT-05, AUT-06, AUT-07 |
| EP-02 | `HU-AUT-05` | `OICO-54` | Roles, permisos y ámbito multi-restaurante | 11 | 2 | En curso | `HU-AUT-07` | RF-USR-03, RF-USR-04, RF-USR-05; AUT-02, AUT-03, AUT-08 |
| EP-02 | `HU-AUT-06` | `OICO-60` | Usuarios y auditoría administrativa | 14 | 2 | Por hacer | `HU-AUT-08` | RF-USR-01, RF-USR-02, RF-USR-03, RF-USR-06, RF-USR-08, RF-USR-09 |
| EP-04 | `HU-CAR-01` | `OICO-84` | Categorías y catálogo de alérgenos | 8 | 2 | En curso | `HU-CAR-02` | RF-PLA-03, RF-PLA-04; CAR-01, CAR-03, CAR-07, CAR-08 |
| EP-04 | `HU-CAR-02` | `OICO-93` | Platos: CRUD, alérgenos, estados y carta pública | 17 | 2 | Por hacer | `HU-CAR-03`, `HU-CAR-04`, `HU-CAR-05` | RF-PLA-01, RF-PLA-02, RF-PLA-03, RF-PLA-04, RF-PLA-05, RF-PLA-06, RF-PLA-07, RF-PLA-08 |
| EP-04 | `HU-CAR-03` | `OICO-108` | Colecciones de menú: CRUD y borrado condicionado | 6 | 2 | Por hacer | `HU-CAR-06`, `HU-CAR-13` | RF-MEN-06; MEN-06, MEN-08 |
| EP-04 | `HU-CAR-04` | `OICO-113` | Menús: CRUD, precio, composición, alérgenos, ciclo de vida y cascada | 25 | 2 | Por hacer | `HU-CAR-07`, `HU-CAR-08`, `HU-CAR-09`, `HU-CAR-10`, `HU-CAR-12` | RF-MEN-01, RF-MEN-02, RF-MEN-03, RF-MEN-04, RF-MEN-05, RF-MEN-06, RF-MEN-07, RF-MEN-08, RF-MEN-09, RF-MEN-10, RF-MEN-11, RF-MEN-12; MEN-01 a MEN-08; CAR-09 |
| EP-04 | `HU-CAR-05` | `OICO-134` | Historial de precios de platos y menús | 3 | 2 | Por hacer | `HU-CAR-11` | RF-PLA-09; MEN-07, RNF-06 |
| EP-01 | `HU-HOR-01` | `OICO-142` | Empleados: CRUD y estado laboral | 5 | 2 | Listo | — | RF-HOR-01, RF-HOR-05; HOR-01, HOR-03, HOR-12 |
| EP-01 | `HU-HOR-02` | `OICO-147` | Cuadrantes y turnos: CRUD, nocturnos, jornada partida y borrado | 16 | 2 | En curso | `HU-HOR-03`, `HU-HOR-08`, `HU-HOR-11`, `HU-HOR-12` | RF-HOR-02, RF-HOR-03, RF-HOR-05, RF-HOR-11, RF-HOR-12; HOR-01, HOR-02, HOR-03, HOR-08, HOR-11 |
| EP-01 | `HU-HOR-03` | `OICO-156` | Validación, descansos y publicación de cuadrantes | 16 | 2 | Por hacer | `HU-HOR-04`, `HU-HOR-06`, `HU-HOR-07`, `HU-HOR-10` | RF-HOR-04, RF-HOR-08, RF-HOR-09, RF-HOR-10, RF-HOR-13, RF-HOR-14; HOR-04, HOR-06, HOR-07, HOR-09, HOR-11, HOR-12 |
| EP-01 | `HU-HOR-04` | `OICO-160` | Ausencias y cambios de turno | 14 | 2 | Por hacer | `HU-HOR-05`, `HU-HOR-09` | RF-HOR-06, RF-HOR-07, RF-HOR-12; HOR-04, HOR-05, HOR-09, HOR-10 |
| EP-03 | `HU-RES-01` | `OICO-191` | Mesas y combinaciones: CRUD, capacidades y habilitación | 15 | 2 | En curso | `HU-RES-02` | RF-MES-01, RF-MES-02, RF-MES-03, RF-MES-04, RF-MES-05, RF-MES-06, RF-MES-07, RF-CFG-05; MES-01, MES-02, MES-03; COM-01 a COM-07 |
| EP-03 | `HU-RES-02` | `OICO-200` | Disponibilidad, asignación automática e informes | 15 | 2 | Por hacer | `HU-RES-03`, `HU-RES-11`, `HU-RES-12` | RF-RES-08, RF-RES-09, RF-INF-01, RF-INF-02, RF-INF-03, RF-INF-04, RF-RES-19; RES-02, RES-03, RES-05, RES-06, RES-12; COM-02, COM-03, COM-04, COM-07 |
| EP-03 | `HU-RES-03` | `OICO-205` | Reservas: CRUD completo, estados, historial, edición y multi-mesa | 26 | 2 | Por hacer | `HU-RES-04`, `HU-RES-07`, `HU-RES-08`, `HU-RES-13`, `HU-RES-14` | RF-RES-01, RF-RES-02, RF-RES-03, RF-RES-04, RF-RES-05, RF-RES-06, RF-RES-07, RF-RES-13, RF-RES-14, RF-RES-15, RF-RES-18; RES-01 a RES-14; COM-03, COM-05, COM-06 |
| EP-03 | `HU-RES-04` | `OICO-211` | Concurrencia, anti-solapamiento y duplicados multi-mesa | 18 | 2 | Por hacer | `HU-RES-05`, `HU-RES-06` | RF-RES-15; RES-04, RES-05, RES-09, RES-12, RES-13; COM-06 |
| EP-03 | `HU-RES-05` | `OICO-230` | Cortesía y no-show | 8 | 2 | Por hacer | `HU-RES-09` | RF-RES-10, RF-RES-11; RES-10, CFG-04 |

## Eliminación completa de HU-RES-10

| Incidencia | Etiqueta | Título | Estado |
|---|---|---|---|
| `OICO-236` | `HU-RES-10` | Lista de espera | Eliminada |
| `OICO-237` | `ST-RES-10.1` | Crear el modelo WaitlistEntry | Eliminada |
| `OICO-238` | `ST-RES-10.2` | Consulta y alta en lista de espera | Eliminada |
| `OICO-239` | `ST-RES-10.3` | Buscar candidatos compatibles | Eliminada |
| `OICO-240` | `ST-RES-10.4` | Promoción a reserva | Eliminada |

Las cinco incidencias se eliminaron de Jira el 2026-11-06. No quedan restos.
GES-06 se unificó en `OICO-271`; el duplicado `OICO-272` se eliminó.

## Historias listas o en curso que cambian

| HU antigua | Estado en la fusión | Nueva HU | Efecto |
|---|---|---|---|
| `HU-AUT-01` | Listo | `HU-AUT-01` | Se mantiene Listo; absorbe AUT-09 y AUT-11 |
| `HU-AUT-02` | En curso | `HU-AUT-02` | Se amplía al esquema completo; sigue En curso |
| `HU-AUT-03` | En curso | `HU-AUT-03` | Sin cambio; sigue En curso |
| `HU-AUT-04` | En curso | `HU-AUT-04` | Se reabre a En curso; absorbe AUT-10 y token_version |
| `HU-AUT-05` | En curso | `HU-AUT-05` | Se reabre a En curso; un rol por usuario |
| `HU-CAR-01` | En curso | `HU-CAR-01` | Se reabre a En curso; absorbe CAR-02 |
| `HU-CAR-03` | En curso | `HU-CAR-02` | Se reabre y se renumera como CAR-02; absorbe CAR-04 y CAR-05 |
| `HU-HOR-01` | En revisión | `HU-HOR-01` | Sin cambio; pasa a Listo |
| `HU-HOR-02` | En curso | `HU-HOR-02` | Sin cambio; absorbe HOR-03, HOR-08, HOR-11 y HOR-12 |
| `HU-RES-01` | En curso | `HU-RES-01` | Se reabre a En curso; combinaciones y multi-mesa |
| `HU-GES-03` | Listo | `HU-GES-03` | Se amplía el DER; solo documentación |
| `HU-GES-04` | Listo | `HU-GES-04` | Se elimina la lista de espera del flujo; solo documentación |
| `HU-GES-06` | Listo | `HU-GES-06` | Se incorpora a la fuente local; sigue Listo |
| `HU-RES-10` | — | `—` | Eliminada por completo con sus cuatro subtareas |

## Reparto sugerido por squads

| Squad | Épicas | Personas actuales |
|---|---|---|
| A | Carta (EP-04) + Horarios (EP-01) | Patricia, Maria Jose, Jose Loero |
| B | Reservas e informes (EP-03) | Jesús, Oscar, Willfredy |
| Transversal | Plataforma, usuarios, permisos y configuración (EP-02) | Willfredy + Jose Loero en Sprint 1 |

## Validación

- `python scripts/jira/jira_import.py --check` pasa.
- `python scripts/jira/jira_import.py --csv docs/backlog/backlog.csv` genera 211 filas.
- `python scripts/jira/verificar_sync.py` devuelve 0 problemas.
- Jira: 5 épicas, 26 HU y 180 subtareas.
