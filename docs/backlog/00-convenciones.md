# Convenciones del backlog — OÍDO COCINA

Documento de referencia para leer, revisar y mantener el backlog del proyecto.
La fuente única de contenido es `scripts/jira/backlog/`. El resto son artefactos
derivados o herramientas.

## 1. Identificadores

| Nivel | Formato | Ejemplo |
|---|---|---|
| Épica | `EP-NN` | `EP-02` |
| Historia de usuario | `HU-<ÁREA>-NN` | `HU-AUT-04` |
| Subtarea | `ST-<ÁREA>-NN.M` | `ST-AUT-04.3` |

Áreas: `GES` (gestión y documentación), `AUT` (autenticación y plataforma), `CAR` (carta),
`HOR` (horarios), `RES` (reservas).

Las HU de cada área se numeran de forma consecutiva, sin huecos:
`GES-01..06`, `AUT-01..06`, `CAR-01..05`, `HOR-01..04` y `RES-01..05`.

Cada identificador viaja como etiqueta en Jira. El importador lo usa para no
duplicar incidencias: si existe una incidencia con esa etiqueta, la actualiza;
si no, la crea.

## 2. Escala de puntos

Un punto equivale a media jornada de una persona (unas 4 horas de trabajo
efectivo, contando pruebas y revisión).

| Puntos | Significado |
|---|---|
| 1 | Trivial. Menos de una hora. Un esquema, un enum, un caso de prueba puntual. |
| 2 | Acotada. Dos o tres horas. Un endpoint con su prueba. |
| 3 | Techo de una subtarea. Cuatro a seis horas. Un servicio con una regla de negocio y sus pruebas. |

Reglas:

- Una subtarea solo puede valer **1, 2 o 3**. Si necesita más, está mal partida.
- Los puntos de una historia son la **suma directa de sus subtareas**, sin redondeo.
- El máximo de una historia es **34 puntos** y **12 subtareas**.
- Si una historia supera 34 puntos, se parte antes de entrar en el sprint.
- Los puntos de una épica son la suma de sus historias; no se redondean.

## 3. Prioridad

Se mantiene MoSCoW del briefing y se traduce a la prioridad de Jira:

| MoSCoW | Prioridad Jira |
|---|---|
| Must | Highest |
| Should | High |
| Could | Medium |
| Won't | Lowest |

Una historia puede contener subtareas Must, Should y Could. Las subtareas Should/Could
llevan la etiqueta `recortable` para poder posponerlas sin romper la historia.

## 4. Estructura de una historia

Toda historia contiene, en este orden:

1. Relato: «Como \<rol\>, quiero \<acción\>, para \<beneficio\>».
2. `CONTEXTO`: por qué existe, qué problema resuelve.
3. `ALCANCE`: qué entra.
4. `FUERA DE ALCANCE`: qué no entra, explícito.
5. `REQUISITOS`: códigos RF y reglas del briefing que cubre.
6. `ABSORBE`: historias antiguas que integra, si aplica.
7. `DEPENDENCIAS`: solo el kernel (`HU-AUT-01` y `HU-AUT-02`).
8. `RELACIONADO CON`: historias que comparten datos o reglas, sin dependencia de código.
9. `REGLAS DE NEGOCIO`: códigos del briefing (`CAR-01`, `RES-04`, `HOR-02`...).
10. `CRITERIOS DE ACEPTACIÓN`: numerados `CA1`, `CA2`...
11. `ESCENARIOS`: Gherkin en formato Dado / Cuando / Entonces.

## 5. Estructura de una subtarea

1. `QUÉ`: una sola responsabilidad verificable.
2. `DÓNDE`: módulo, capa y archivo previsto.
3. `RELACIONADO CON`: subtareas e historias con las que se acopla.
4. `VERIFICACIÓN`: la prueba concreta que la da por terminada.
5. `RECORTABLE`: solo si es Should/Could y se puede posponer.

Cada subtarea incluye su prueba. No existe la subtarea «escribir tests».

## 6. Sprints y fechas

| Sprint | Inicio | Fin | Contenido |
|---|---|---|---|
| Sprint 1 | 2026-10-29 | 2026-11-05 | Kernel, esquema, documentación y base de seguridad |
| Sprint 2 | 2026-11-06 | 2026-11-12 | Todas las historias funcionales pendientes |

No hay Sprint 3. El Sprint 2 se prioriza por MoSCoW y las subtareas `recortable`
se posponen si el tiempo no alcanza.

## 7. Corte por valor y flujos

El backlog se ordena por valor entregable, no por capas del sistema. Primero el kernel
y el esquema; después las historias funcionales completas.

| Flujo | Módulos |
|---|---|
| `flow-a` | dishes, menus |
| `flow-b` | tables, reservations |
| `flow-c` | users, settings, schedules |
| `flow-docs` | documentación y gestión |

Etiquetas de Jira:

- `EP-xx`, `HU-xx`, `ST-xx`: identificador de la incidencia.
- `flow-a`, `flow-b`, `flow-c`, `flow-docs`: flujo de trabajo al que pertenece.
- `sprint-1`, `sprint-2`: sprint asignado.
- `enabler`: habilitador técnico sin valor visible para el usuario.
- `recortable`: subtarea Should/Could que se puede posponer.
- `absorbida`: etiqueta histórica de una historia integrada en otra. Las incidencias absorbidas se eliminaron de Jira tras la fusión; el mapa queda en `matriz-fusion.md` y en `ABSORBE`.

### Regla de dependencias

- Una historia funcional **solo** puede depender de `HU-AUT-01` (kernel de código) y
  `HU-AUT-02` (esquema y modelos compartidos).
- El esquema completo y los modelos ORM viven en el kernel. Ninguna historia funcional
  crea tablas que otra necesite.
- Ningún módulo importa modelos o servicios internos de otro módulo. Las lecturas
  cruzadas se hacen sobre los modelos compartidos o mediante contratos de lectura.
- `scripts/jira/backlog/__init__.py` falla si una historia declara otra dependencia.

### Decisiones de modelo

- Un usuario tiene **un único rol** (`users.role_id`); los permisos son granulares
  (`roles`, `permissions`, `role_permissions`).
- Una reserva puede ocupar **una o varias mesas** y puede usar una combinación
  configurada. Las mesas independientes suman su capacidad máxima y no venden sillas
  sobrantes.
- Una reserva `pending` bloquea sus mesas hasta `start_at + courtesy_minutes`.
- El precio vive en `dishes` y en `menus`; el historial de precios cubre ambos.
- No hay lista de espera. `HU-RES-10` y sus subtareas están eliminadas.
- La auditoría existe en `audit_logs`, pero es Should/recortable.

## 8. Cómo se ejecuta la importación

```powershell
$env:JIRA_BASE_URL  = "https://gonzalezgomezjesus.atlassian.net"
$env:JIRA_EMAIL     = "correo@ejemplo.com"
$env:JIRA_API_TOKEN = "token"
$env:JIRA_PROJECT_KEY = "OICO"
$env:JIRA_BOARD_ID  = "68"

python scripts/jira/jira_import.py --check
python scripts/jira/jira_import.py --csv docs/backlog/backlog.csv
python scripts/jira/jira_import.py
$env:DRY_RUN = "0"
python scripts/jira/jira_import.py --prune
```

`DRY_RUN` vale `1` por defecto: sin `DRY_RUN=0` el importador no escribe en Jira.

## 9. Definición de hecho

Una incidencia se considera terminada cuando:

- El código está implementado y sus pruebas pasan.
- Los casos límite, permisos y validaciones están cubiertos.
- La migración y el seeder están actualizados, si aplica.
- La Pull Request fue revisada por otra persona e integrada.
- No quedan errores conocidos que incumplan los criterios de aceptación.

## 10. Compactación del backlog

El backlog pasó de 55 historias a 26:

- 29 historias se absorbieron en un agregado completo y se eliminaron de Jira tras la fusión.
- `HU-RES-10` y sus cuatro subtareas se eliminaron por completo.
- `HU-GES-06` se incorporó desde Jira a la fuente local.
- Las HU se renumeraron por área para que no queden huecos: `CAR-01..05`, `HOR-01..04` y `RES-01..05`.
- El mapa completo está en `docs/backlog/matriz-fusion.md`.

## 11. Trazabilidad

Cada historia incluye una sección `REQUISITOS` con los códigos `RF-*` del briefing.
La matriz de `HU-GES-05` contrasta el backlog con esos códigos. Las historias Must
cubren el alcance mínimo; las Should/Could quedan marcadas como recortables.
