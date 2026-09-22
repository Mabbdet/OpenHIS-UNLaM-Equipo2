# Entrega 5 — Cierre del Sprint 3

Fuente: `C:/Users/Ale/Downloads/Sist-Info-Salud-5.pdf`, entregables de páginas 89–90 y ejemplos de módulos/XML. Responsable: Alejandro. Incremento desarrollado en `develop-Entrega5`, desde `develop` en `8a12cfc`.

## Matriz de requisitos y verificación

| Requisito | Implementación | Verificación / evidencia |
|---|---|---|
| Bajas lógicas y reactivación de las cuatro entidades | `datos.py`: operaciones explícitas sobre `activo`; accesos anteriores compatibles | Ciclos de alta, baja y reactivación conservan ID y contenido; ocho capturas |
| Cambios manuales sin cascada (p. 90) | Cada operación cambia una sola fila | Prueba de conservación de signos/prescripciones al cambiar fichas relacionadas |
| Migración sin pérdida de información | `esquema.py`: columnas faltantes, conservación de estados e índices | Migración repetida, integridad y comparación contra respaldo de Entrega 4 |
| Consultas por estado y DNI | `activos=True/False/None`; búsqueda de activos e inactivos | Pruebas de filtros, unicidad global e historial completo |
| Intervenciones nuevas con fichas activas | Selectores filtrados y validación al guardar | Rechazo de paciente/profesional inactivo |
| Cuatro módulos independientes | Los cuatro archivos `*_def_app.pyw` | Apertura y callbacks reales de los cuatro formularios |
| Menú común | `OpenHIS_app.pyw`, `menu_app.py` | Apertura de los cinco módulos sobre el mismo repositorio |
| XML del ejemplo docente | `exportaciones.py`: metadatos, paciente, profesional, fármaco, diagnóstico opcional, dosificación y administración | XML parseable, caracteres especiales, estados y vista previa real |
| HTML imprimible | Detalle completo, estado y estilos de impresión | Escape de contenido y revisión estática con MuPDF; navegador pendiente |
| Archivos únicos y errores de escritura | Carpetas respecto de raíz, timestamp/UUID y creación exclusiva | Exportaciones sucesivas no reemplazan archivos; un error conserva la receta |
| Evidencias y reflexión | Bitácora, `evidencias/entrega5/` y reflexión de dos párrafos | Ocho capturas de altas/bajas, XML, HTML y conservación de capturas previas |

## Reglas de conservación

Pacientes y profesionales inactivos siguen siendo consultables. No puede crearse otra ficha con el mismo DNI o matrícula; se recupera mediante Reactivar. La baja muestra cuántos signos y prescripciones se conservarán. No se modifican sus estados automáticamente.

Anular o reactivar signos y prescripciones conserva los datos, la fecha y el profesional original. Puede reactivarse una intervención aunque sus fichas relacionadas estén inactivas; el detalle indica esos estados. Las altas nuevas exigen ambas fichas activas. No se agrega edición de mediciones ni de prescripciones.

El formato XML académico utiliza `Prescription`, versión `1.0` y `http://openhis.unlam.edu.ar/fhir`. Ese nombre no acredita interoperabilidad HL7 FHIR. Los documentos identifican su carácter académico y no afirman validez normativa. El campo `activo` no constituye una auditoría completa: falta identificar al autor de cada cambio.

## Base y evidencias entregadas

Se registraron y dieron de baja individualmente los siguientes datos ficticios mediante los formularios reales:

| Entidad | ID | Identificación | Estado final |
|---|---|---|---|
| Paciente | 6 | Camila Prueba E5, DNI 50123505 | Inactivo |
| Profesional | 7 | Julián Prueba E5, matrícula DEMO-E5-505 | Inactivo |
| Signos vitales | 4 | Paciente 6, profesional 7 | Anulado |
| Prescripción | 8 | Paciente 6, profesional 7 | Anulada |

Los PNG `01`–`04` muestran altas y `05`–`08` bajas. El `09` es la vista previa XML real. El `10` es un renderizado estático del HTML mediante MuPDF, identificado como tal; no es una captura de navegador. Los registros tienen fechas automáticas UTC; las exportaciones incluyen la zona horaria local. No se dedujeron fechas de trabajo de las celdas heredadas de Scrum.

Los ejemplos generados están en `recetas/receta_8_20260921_232829_418332_7f1f2a7d.xml` y `reportes/reporte_8_20260921_232850_308783_e9e27ad1.html`. La base final conserva los registros anteriores y agrega un registro inactivo por entidad.

## Alcance de la verificación

Se aprobaron 66 pruebas de pytest sin omisiones. La apertura del menú y las cuatro interfaces se comprobó; los flujos de alta, baja y reactivación usan callbacks reales con bases temporales. Las ocho capturas documentan altas y bajas sobre la base entregada.

El navegador integrado rechazó la URL local del HTML por su política de seguridad. Se revisó el contenido completo con un renderizador estático sin navegación ni ejecución de scripts. Queda pendiente comprobar la apariencia e impresión en el navegador del usuario. MuPDF utiliza otro motor de estilos y su imagen no acredita el diseño exacto de Chrome/Edge.

Scrum conserva fechas, estados, fórmulas y evidencias previas. La referencia rota heredada `HU-UNLaM!I20` permanece fuera del alcance de esta entrega. Las capturas anteriores a Entrega 4 siguen siendo un pendiente histórico. FHIR real, importación, autenticación, auditoría de accesos y validación oficial de matrícula quedan fuera del incremento.
