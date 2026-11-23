# Verificación de los incrementos

## Cierre de evidencias del 22/11/2026

El comprobante del correo de intercambio FHIR está incorporado en la Bitácora desde la fila 1456. La impresión del HTML de la entrega 5 está acreditada con un PDF de dos páginas A4 y la captura del diálogo de impresión desde la fila 1480. La planilla conserva 42 imágenes, las fórmulas verificadas y los responsables de las tareas.

El ejemplo `intercambio/hibrido/FHIR_44895843_hibrido_Equipo2.json` conserva los seis recursos originales del archivo de Bart Simpson recibido de Lautaro y agrega un ServiceRequest sintético del Equipo 2. Se ejecutó el flujo `preparar_importacion` / `confirmar_importacion` en dos bases temporales autenticadas, una vacía y otra con el archivo original importado previamente. El análisis y la cancelación conservaron los datos. En la segunda base la confirmación agregó únicamente una práctica, asociada a Bart Simpson y Julius Hibbert. La reimportación produjo cero altas y conservó las filas clínicas en ambos escenarios. SQLite pasó integridad y claves foráneas. Resultados, advertencias y hashes en `evidencias/integrador-fhir/verificacion_hibrido.json`.

La verificación del ejemplo corresponde al contrato de importación de la aplicación. Los recursos recibidos conservan las advertencias de fechas sin zona, mediciones sin profesional informado y titulaciones sin código. La procedencia del ServiceRequest queda identificada como generación sintética del Equipo 2. El resumen del ensayo figura en la Bitácora desde la fila 1508.

Los resultados de las pruebas y los conteos que figuran en los apartados siguientes corresponden al cierre de cada incremento.

## Entrega final — Turnero web opcional

Verificación del 21/11/2026: **204 pruebas aprobadas, ninguna omitida**. Regresión completa de 202 casos en 236,18 s y dos casos adicionales de habilitación/revocación desde escritorio en 7,41 s, sin cambios posteriores al código de producción. Comandos: `.venv/Scripts/python.exe -m pytest -q -rs -p no:cacheprovider` y `.venv/Scripts/python.exe -m pytest tests/test_acceso_web_gui.py -q -rs -p no:cacheprovider`.

Los casos nuevos comprueban aislamiento entre pacientes, campos manipulados, competencia entre reserva web y telefónica, reprogramación atómica, cancelación de recordatorios, CSRF, logout, vencimiento, revocación al renovar clave o dar de baja fichas, cuenta técnica desactivada, permisos de emisión de claves y migración del esquema antiguo conservando relaciones y secuencia. Se ejecutaron los callbacks reales del escritorio para habilitar y revocar acceso. JavaScript pasó la comprobación de sintaxis de Node.

Prueba real del navegador sobre una copia ficticia: ingreso, búsqueda, reserva a las 08:00, confirmación, reprogramación a las 08:30, cancelación con motivo y salida. Se conserva el turno original y su vínculo con el nuevo. SQLite: integridad `ok`, sin violaciones de claves foráneas. El SHA-256 de la base principal coincide con el respaldo anterior a este incremento. La vista móvil de 390 px no produjo desborde horizontal. Cuatro capturas contienen solo el portal y se guardan en `evidencias/turnero-web/`, junto con `verificacion.json`.

Alcance e instrucciones en `docs/turnero-web.txt`. Revisión del 22/11 en `develop-revisionFinal` sobre la base `2fda27e`. La suite completa pasó en una ejecución (204 pruebas). La Bitácora conserva las 29 imágenes previas y agrega 11 de las entregas 2, 3 y final. Se verificaron las 23 historias, los 10 sprints, las fórmulas y el reparto de 30 tareas. La hoja Revisión identifica las fuentes y los pendientes documentales.

## Entrega 10 — Visor DICOM y confirmación FHIR

**142 pruebas aprobadas, ninguna omitida**, en 97,25 s, con `.venv/Scripts/python.exe -m pytest -q -rs -p no:cacheprovider`. Incluye las 121 anteriores y 21 nuevas: análisis sin escritura, cancelación/confirmación gráfica, archivo/base/permisos modificados, agrupación y contradicciones de Observations, dosis estructuradas y reutilización de fármacos, píxeles 8/16 bits, signed, MONOCHROME1, endian y RGB planar, archivos sin imagen/comprimidos y metadatos con secuencias.

Demostración real: `verificacion_preanalisis.json` prueba SHA-256 idéntico de Salud.db antes/después de analizar; la confirmación creó un SignosVitales y cuatro referencias externas, reutilizando paciente/profesional. El visor mantuvo intacto el DICOM y registró Q con usuario autenticado. Se revisaron las cuatro capturas y sus vistas dentro de Scrum. El callback gráfico de confirmación se probó con respuesta negativa y afirmativa; la captura del resultado muestra el resumen real guardado por la demostración.

Comparación con el respaldo previo: todos los registros y valores anteriores siguen presentes, salvo la actualización esperada de Usuarios.ultimo_acceso. SQLite: integridad `ok` y ninguna violación de claves foráneas. Base final: 6 pacientes, 8 profesionales, 5 signos, 9 prescripciones, 2 prácticas y 11 referencias FHIR. Scrum conserva hojas, fórmulas, combinaciones y veinte imágenes previas; agrega cuatro imágenes y el cierre de Entrega 10. La referencia rota histórica HU-UNLaM!I20 permanece fuera del incremento. Evidencias en `evidencias/entrega10/`; límites en `docs/entrega-10.md`.

## Entrega 9 — Intervenciones, FHIR y DICOM

**121 pruebas aprobadas, ninguna omitida**, con `.venv/Scripts/python.exe -m pytest -q -rs -p no:cacheprovider`. Incluye 96 pruebas anteriores con la matriz de permisos ampliada, y 25 casos nuevos: ida/vuelta JSON/XML, persistencia y asociaciones, DNI inactivos, profesional externo incompleto, reimportaciones, duplicación de Observation, errores de formato/referencias/fechas/unidades, XML hostil, permisos y rollback si falla auditoría.

Se ejecutaron los callbacks reales de consulta, registro de práctica, exportación/importación FHIR, conversión DICOM, anonimización y lectura de metadatos. DICOM conserva el hash de píxeles, regenera estudio/serie/instancia y elimina privados y secuencias. Se revisaron las cuatro capturas de las interfaces y las evidencias embebidas en Scrum.

Base comparada con el respaldo anterior: ningún valor preexistente de pacientes, profesionales, signos, prescripciones, catálogos o auditoría fue sobrescrito. Las cuentas se conservan; su último acceso se actualizó al utilizarlas. Se agregaron una especialidad no informada, un profesional externo, un fármaco externo, una prescripción y dos prácticas (local y recibida). Integridad SQLite `ok`, sin violaciones de claves foráneas. Trabajo iniciado el 20 y cerrado el 21/11/2026 (Argentina); auditoría UTC.

## Entrega 7 — Seguridad y auditoría

Ejecución del 20/11/2026 (Argentina): **96 pruebas aprobadas, ninguna omitida**, con `.venv/Scripts/python.exe -m pytest -q -rs -p no:cacheprovider`. Incluye regresión, los cuatro roles, login válido e inválido, bajas y reactivación de usuarios, último admin, revocación entre instancias, hash con sal y migración desde SHA-256, autoría, valores anteriores/nuevos y rollback ante fallo de auditoría. El menú de Entrega 5 se prueba con una sesión de administrador.

Se comprobó el formulario real de alta de usuario, filtros de auditoría, apertura de módulos por rol, modificación/baja de los tres catálogos y ciclo real de login/logout en las ocho entradas del menú. El acceso antiguo al historial conserva sus permisos. Las capturas de Usuarios y Auditoría se revisaron visualmente. Scrum conserva sus 14 imágenes y agrega dos, sin cambiar las fórmulas existentes; `HU-UNLaM!I20` sigue con su referencia rota histórica.

La base entregada conserva los registros clínicos y sus estados anteriores; agrega cuatro cuentas ficticias (admin y tres usuarios nuevos de roles distintos), auditoría y una especialidad ficticia inactiva para demostrar A/M/B. Integridad SQLite: `ok`, sin infracciones de claves foráneas. La auditoría guarda UTC.

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
| Revisión visual | Menú, cuatro módulos y vista previa XML revisados. HTML revisado con MuPDF y, el 22/11/2026, PDF de impresión desde navegador comprobado visualmente en sus dos páginas A4. PDF y captura del diálogo en `evidencias/entrega5/`; Bitácora desde 1480. |
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

El equipo está integrado por Alejandro y Leonel, con el primero como Scrum Master. La asociación al profesional en signos quedó implementada en la entrega 4. Reportes/XML y FHIR se incorporaron en los incrementos 5, 9 y 10. La revisión final agregó las capturas de las entregas 2 y 3. La validación de vigencia de matrícula requiere un registro institucional y permanece como limitación del alcance.
