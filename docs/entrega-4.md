# Entrega 4 — Sprint 3 — Epic 2

Responsable: Alejandro (equipo unipersonal). Rama de trabajo: `develop-Entrega4`, creada desde `develop`; integración después de las verificaciones.

Fuente de requisitos: `Guia_Entregas_1_2_3_y_4_OpenHIS_UNLaM.md`, secciones 60–88, y planilla del profesor aportada. El PDF original `Sist-Info-Salud-4.pdf` no está en el repositorio; no se afirma haberlo contrastado.

## Alcance implementado

| Requisito | Implementación | Prueba / evidencia |
|---|---|---|
| HU-04: especialidades | Alta, listado, modificación y desactivación lógica. Código único. Las inactivas conservan sus asociaciones y no admiten nuevas asignaciones. | `tests/test_entrega4.py`; `evidencias/sprint3/01_movimiento_maestra.png`. |
| HU-04: SNOMED local | Alta, listado y búsqueda por término; código único. | Tests de catálogo, duplicado y búsqueda. Los códigos DEMO son ficticios y no son identificadores SNOMED CT oficiales. |
| HU-04: fármacos | Alta y listado con principio activo, presentación, concentración y vía. | Tests de catálogo y duplicado; registros ficticios en la base. |
| HU-05: profesionales | Alta, búsqueda por DNI, detalle/listado, modificación de teléfono/email/especialidad y baja física protegida. DNI y matrícula únicos, especialidad obligatoria. | Tests de CRUD y unicidad; `02_alta_profesional.png`, `03_modificacion_profesional.png`. |
| Profesional en signos vitales | Selector obligatorio, FK real hacia Profesionales, nombre en historial y rechazo de autores inexistentes. | Tests de servicio, FK e integración del formulario; migración histórica verificada. |
| Prescripciones exigidas en E4 | Alta con paciente/profesional/fármaco, SNOMED opcional, dosis/vía/frecuencia; búsqueda por DNI del paciente; detalle; listado; anulación lógica. | Tests de prescripción y relaciones; `04_alta_prescripcion.png`. |
| Datos mínimos | 5 pacientes, 6 profesionales de 6 especialidades y 7 prescripciones ficticias al cerrar esta ejecución; 3 signos con profesional. | Conteos sobre `Salud.db`; incluye datos adicionales generados al capturar las evidencias. |
| Reflexión y Scrum | Reflexión de dos párrafos; Sprint 3 y resultados documentados en copia de la plantilla. | `docs/reflexion-sprint-3.md`, `scrum/Planilla Scrum.xlsx`. |

## Ejecución

Desde la raíz del repositorio:

```powershell
python Pacientes2b_app.pyw
```

La ventana principal incluye botones para Tablas maestras, Profesionales y Prescripciones. También se pueden ejecutar por separado:

```powershell
python Tablas_maestras_app.pyw
python Profesionales_app.pyw
python Prescripcion_app.pyw
```

Todos los módulos comparten `BD/Salud.db`. Los auxiliares `datos.py`, `esquema.py`, `interfaz.py` y `ventanas_clinicas.py` deben incluirse al entregar el código. Se conservan los nombres pedidos en la sección de entregables; no se duplica `Tablas_maestras.pyw` ni se usa el nombre alternativo `prescripciones_app.py`.

## Migración y relaciones

La inicialización crea Especialidades, SnomedCT, Farmacos, Profesionales y Prescripciones con las columnas de la guía. Agrega los cuatro índices pedidos para prescripciones y reconstruye SignosVitales para añadir su FK a Profesionales. Todas las conexiones activan `PRAGMA foreign_keys=ON`.

Los signos históricos mantienen ID, fecha y datos. Si no tenían autor, la migración conserva NULL y los identifica como históricos; no inventa a un profesional. Los nuevos registros exigen autor tanto en el servicio como mediante un trigger de SQLite. La ventana permite seleccionar un registro histórico y asignarle su autor confirmado, sin sobrescribir uno ya existente.

La carga demo completa únicamente el autor de las mediciones ficticias reconocidas que creó la propia demo anterior. La base entregada no tiene signos sin profesional. Para bases externas, los históricos sin autor requieren revisión manual. Antes de la migración se guardó una copia local de trabajo de la base anterior; no forma parte del paquete final.

La baja de profesionales con signos o prescripciones asociados se bloquea para conservar referencias. La baja de un paciente con prescripciones, incluso anuladas, se bloquea por la misma razón. Un paciente sin prescripciones conserva la eliminación conjunta de paciente y signos de Entrega 3. Las prescripciones se anulan mediante `activo=0` y siguen disponibles en el historial.

## Decisiones y límites explícitos

- **Prescripciones en Sprint 3:** se implementan porque la sección de entregables de E4 las exige, aunque HU-06 figure en Sprint 4. No se declara HU-06 completa: reporte/receta XML quedan fuera del incremento actual.
- **Matrícula vigente:** se verifica matrícula obligatoria y única. La fuente no define registro oficial, jurisdicción, API ni procedimiento para comprobar vigencia. La UI lo informa; esa validación real sigue pendiente y no se confunde con unicidad. HU-05 conserva esta salvedad.
- **HU-07 y HU-08:** FHIR/XML, importación externa, autenticación y auditoría de acceso no están implementados.
- **Datos clínicos:** las prescripciones demo utilizan fármacos, dosis y vías explícitamente ficticios. No son indicaciones terapéuticas ni recetas utilizables.
- **Planilla:** se creó una copia de `Planilla-Scrum-Profe.xlsx`, sin sobrescribir Downloads. Se actualizan los objetivos/comentarios de E4, el responsable Alejandro y los resultados/evidencias de Bitácora. Las fechas y estados heredados se conservan; no acreditan fechas reales de ejecución. Tampoco se trasladan automáticamente ediciones que solo se hayan realizado fuera del archivo recibido.
- **Fórmulas previas:** se conserva la referencia rota de `HU-UNLaM!I20` y las sumas preexistentes de la plantilla ajenas a esta implementación; no se usan para certificar avance.

## Verificación

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Pruebas sencillas sobre bases temporales: regresión de pacientes; catálogos; profesionales; validaciones y FK; prescripciones/anulación; bloqueo de bajas; migración; carga demo repetible; apertura de las nuevas ventanas y selector de profesional en signos. Ver `docs/verificacion.md` para el resultado final.

Las cuatro capturas corresponden a operaciones reales de los formularios, con datos ficticios guardados en la base. Están embebidas en Bitácora desde las filas 31, 58, 85 y 112. La captura de alta muestra el registro recién creado; las otras incluyen la confirmación de éxito. Se verificaron los PNG y sus anclajes/archivos embebidos en el XLSX. El renderizador de previsualización omite las imágenes de Excel; esa limitación no elimina las imágenes del archivo exportado.
