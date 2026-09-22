# Verificación de los incrementos

## Entrega 5 / Ampliación y cierre de Sprint 3

| Verificación ejecutada | Resultado |
|---|---|
| `.\.venv\Scripts\python.exe -m pytest -q -rs` | **66 aprobadas en 5,19 s, ninguna omitida**. |
| Ciclos de estado | Alta, baja/anulación y reactivación de las cuatro entidades conservan ID y datos. Estados repetidos e IDs inexistentes producen un aviso. |
| Sin cascada | Cambiar pacientes/profesionales no modifica signos ni prescripciones. Reactivar intervenciones históricas no activa las fichas relacionadas. |
| Consultas y validaciones | Activos/inactivos/todos, búsqueda de inactivos, historial completo, DNI/matrícula únicos y rechazo de nuevas intervenciones con fichas inactivas. |
| Migración repetida | Conservación de estados anulados, fechas, identificadores y relaciones; índices y claves foráneas verificados. |
| GUI | Apertura de menú y cinco módulos; callbacks reales de alta, baja y reactivación con bases temporales. Ocho capturas de altas/bajas sobre datos ficticios de la base entregada. |
| Tkinter | Una raíz por sesión de pytest y ventanas aisladas por prueba evitan las cargas repetidas de Tcl/Tk. La ejecución completa final no omitió ninguna prueba. |
| XML y HTML | XML parseable con diagnóstico opcional y caracteres especiales; HTML escapado; estados activa/anulada, nombres únicos y conservación de receta ante error de escritura. |
| Revisión visual | Menú, cuatro módulos y vista previa XML revisados. HTML completo revisado con MuPDF estático. Apariencia e impresión en navegador pendientes por bloqueo de la herramienta al abrir URL local. |
| Base entregada | 6 pacientes (5 activos), 7 profesionales (6 activos), 4 signos (3 activos), 8 prescripciones (7 activas). Los cuatro registros nuevos quedaron inactivos. |
| Conservación de Entrega 4 | Comparación contra respaldo: todos los valores de las columnas preexistentes y todas las filas anteriores siguen presentes en las siete tablas. |
| Integridad final | `PRAGMA integrity_check`: `ok`. `PRAGMA foreign_key_check`: sin violaciones. Signo 4 y prescripción 8 conservan paciente 6 y profesional 7. |
| Scrum | 14 imágenes embebidas: cuatro anteriores y diez nuevas. Verificados sus hashes, fórmulas, fechas, estados, hojas, combinaciones previas, paneles y validaciones. Cambios de valores limitados a objetivos/comentarios y asignación de HU a sprints. |

La imagen HTML es una revisión estática, no una captura de Chrome/Edge; los motores de estilos difieren. MuPDF se usó únicamente como herramienta local de verificación y no es dependencia de la aplicación. El renderizador de la planilla omite imágenes en su vista previa: se inspeccionaron los PNG y su presencia en el XLSX. Se conserva la referencia rota heredada `HU-UNLaM!I20`, ajena a este incremento.

Los apartados siguientes describen las verificaciones históricas. Las bajas físicas y el límite de historial de las primeras entregas fueron reemplazados por las reglas de Entrega 5.

Entorno de ejecución: Windows, Python 3.14.6, Tk 8.6.15 y pytest 9.1.1. Dependencias de pruebas instaladas en `.venv`.

| Incremento | Verificación ejecutada | Resultado |
|---|---|---|
| Entrega 1 | Revisión de la documentación y `git diff --check`. | Sin errores de formato detectados; visión provisional con pendientes explícitos. |
| Entrega 2 | `python -m pytest -q` desde el entorno virtual. | 9 pruebas aprobadas. |
| Entrega 2 | Ejecución de consola: búsqueda existente e inexistente. | Mensajes y detalle correctos. Una búsqueda en la base de cinco pacientes demoró aproximadamente 0,0006 s en este equipo; no es una prueba de carga. |
| Entrega 3 | `python -m pytest -q` desde el entorno virtual. | 20 pruebas aprobadas, ninguna omitida en este entorno. |
| Entrega 3 | Ejecución de callbacks reales de formularios Tkinter con base temporal y respuestas a cuadros de diálogo controladas. | Alta, rechazo de duplicado, modificación, signos, historial y eliminación conjunta verificados. |
| Entrega 3 | Conteos sobre `BD/Salud.db`. | 5 pacientes; 3 pacientes con signos; 3 registros de signos. |
| Entrega 3 | `PRAGMA integrity_check` y `PRAGMA foreign_key_check`. | `ok` y sin violaciones de claves foráneas. |
| Entrega 3 | Repetición de la carga de demostración. | Sin duplicar pacientes ni signos existentes. |

Las pruebas se centran en comportamientos sencillos y utilizan bases temporales. Las verificaciones de Tk no equivalen a una revisión visual ni a pruebas con usuarios reales.

## Entrega 4 / Sprint 3

| Verificación ejecutada | Resultado |
|---|---|
| `.\.venv\Scripts\python.exe -m pytest -q -rs` | 48 pruebas aprobadas en 3,40 s; ninguna omitida. |
| Catálogos y profesionales | Alta, búsqueda, modificación, desactivación de especialidad, DNI/matrícula únicos y protección de bajas verificados. |
| Prescripciones | Alta, consulta y detalle, anulación lógica, campos obligatorios, fechas y relaciones verificadas. |
| Migración desde el esquema anterior | Conserva ID, fecha y datos de signos; admite corregir autores históricos; nuevos signos exigen profesional válido. |
| Regresión de GUI | Apertura de nuevas ventanas y registro de signos con selector de profesional verificados con bases temporales. |
| Base entregada | 5 pacientes, 6 profesionales de 6 especialidades, 7 prescripciones y 3 signos; ningún signo sin profesional. |
| Integridad de SQLite | `PRAGMA integrity_check`: `ok`; `PRAGMA foreign_key_check`: sin violaciones. |
| Carga demo repetida | No duplica sus cinco profesionales ni sus cinco prescripciones iniciales; conserva los registros adicionales de las evidencias. |
| Evidencias visuales | Cuatro capturas de operaciones reales: movimiento de especialidad, alta y modificación de profesional y alta de prescripción. PNG revisados y embebidos en Bitácora. |
| Planilla Scrum | Objetivo, comentarios y responsable de Sprint 3 actualizados. Se conservan fechas, estados y fórmulas preexistentes ajenas al cambio, incluida una referencia rota heredada en `HU-UNLaM!I20`. |

Los tests usan datos ficticios y bases temporales. Las capturas usan la base demo entregada; sus datos no son indicaciones terapéuticas. El renderizador de Excel omite las imágenes en su previsualización: se revisaron los PNG y se comprobaron sus archivos y anclajes dentro del XLSX exportado.

Alejandro es el único integrante. La asociación al profesional en signos quedó implementada en esta entrega. Continúan pendientes la validación real de vigencia de matrícula, el contraste con los PDFs originales y las capturas de las entregas anteriores. Reportes/XML y FHIR quedan fuera del incremento actual. Los tests y el merge no acreditan esos pendientes.
