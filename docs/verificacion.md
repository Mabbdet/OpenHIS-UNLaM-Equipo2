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

Pendientes académicos: contrastar PDFs originales, completar integrantes/roles y obtener las capturas requeridas para su incorporación en Planilla Scrum → Bitácora. La integración del profesional en signos vitales está diferida a Sprint 3 conforme a la planilla. Estos pendientes no se consideran resueltos por la aprobación de tests o por los merges.
