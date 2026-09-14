# Verificación de los incrementos

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
