# Plan de proyecto — OpenHIS-UNLaM — Equipo 2

Estado: borrador de planificación para revisión del equipo.

## Decisiones posteriores a la planificación inicial

- Alcance actual confirmado por el usuario: Epic 1, HU-01, HU-02 y HU-03.
- Ramas acumulativas solicitadas: `develop-Entrega1` (documentación), `develop-Entrega2` (consola) y `develop-Entrega3` (GUI, CRUD y signos vitales). Cada incremento se verifica y se integra a `develop` antes de iniciar la siguiente rama desde `develop` actualizado. Los pendientes de presentación académica se documentan por separado y no se dan por cumplidos mediante los tests.
- Pruebas sencillas con `pytest`, sobre bases temporales.
- Se revisó `C:/Users/Ale/Downloads/Planilla-Scrum-Profe.xlsx`, ignorando los estados. Su Sprint 3 asigna explícitamente la integración del profesional en signos vitales a HU-04/HU-05; en Sprint 2 se conserva `medico_id` preparado, sin afirmar que exista esa integración.
- La planilla ubica HU-04 a HU-08 en Epic 2 y HU-09 a HU-11 en Epic 3. Se registra la diferencia con la numeración de la guía; no se implementan esas historias ahora.
- El objetivo de Sprint 2 debe explicitar GUI además de signos, motivo, modificación y baja. Los PDFs originales y las fechas efectivas de entrega siguen pendientes de verificación.

El inventario y los pendientes de las secciones siguientes describen la revisión inicial; los archivos y verificaciones de cada rama se detallan en su README.

## 1. Base del plan

Fuente disponible: `Guia_Entregas_1_2_y_3_OpenHIS_UNLaM.md`.

Al revisar el repositorio solo se encontró esa guía, además del directorio Git. No se encontraron los tres PDFs originales, código, base de datos ni Planilla Scrum. Esto describe el repositorio local; puede existir trabajo fuera de él.

Los requisitos enumerados aquí proceden de la guía y quedan pendientes de contraste con los PDFs. Las estimaciones, la distribución del trabajo y la organización de archivos son propuestas del equipo, no exigencias de la cátedra.

Objetivo: completar las tres entregas con documentación, software ejecutable, datos de demostración, pruebas y evidencias trazables.

## 2. Alcance por entrega

| Entrega | Resultado | Condición de cierre según la guía |
|---|---|---|
| 1 — Visión | Documento de Visión y backlog preliminar | Contexto, problema, objetivos, alcance, actores, flujo, cuatro capas, ocho epics, HHUU conocidas y pendientes, sprints e integrantes/roles documentados. |
| 2 — Sprint 1 | Gestión de pacientes por consola | HU-01 y HU-02 funcionando; `Pacientes.py`; `BD/Salud.db` con al menos cinco pacientes; tres capturas en Bitácora; reflexión de dos párrafos. |
| 3 — Sprint 2 | Gestión de pacientes con Tkinter | Tres versiones gráficas funcionando; CRUD completo; HU-03, motivo e historial; al menos cinco pacientes y signos en al menos tres; objetivo de Sprint 2 actualizado; tres capturas en Bitácora y reflexión de dos párrafos. |

Profesionales, turnos, FHIR operativo, SNOMED, DICOM e IA permanecen en el horizonte del producto. Su implementación no integra estas tres entregas según la guía.

## 3. Secuencia de trabajo propuesta

Las horas son esfuerzo total de equipo, no duración calendario ni horas por integrante. Son estimaciones iniciales, sujetas a experiencia con Python/Tkinter y a las consignas originales.

| Hito | Trabajo | Resultado verificable | Dependencia | Esfuerzo |
|---|---|---|---|---|
| H0 — Consignas y organización | Contrastar los tres PDFs, revisar plantilla Scrum, inventariar avances externos y registrar datos faltantes. | Matriz de requisitos con fuente y ambigüedades; responsables iniciales. | Disponibilidad de fuentes. | 2–3 h |
| H1 — Entrega 1 | Redactar visión, alcance, actores, flujo, capas, epics y backlog. | Documento coherente y revisado; propuestas distinguidas de requisitos. | H0 para cierre definitivo. | 4–6 h |
| H2 — Entrega 2 | Preparar SQLite; implementar alta, búsqueda, menú, unicidad de DNI e identificación de HC. | Consola operativa; cinco pacientes ficticios; pruebas y evidencias; reflexión. | H0 y criterios HU-01/HU-02 definidos. | 5–8 h |
| H3 — GUI y CRUD | Construir `Pacientes_app.py` y `Pacientes2_app.pyw`; conservar la consola. | Alta, búsqueda, listado, modificación y eliminación verificadas. | H2. | 5–8 h |
| H4 — Signos vitales | Incorporar `SignosVitales`, motivo, validaciones, historial, doble clic y eliminación conjunta en `Pacientes2b_app.pyw`. | HU-03 verificada, con estado explícito del criterio de asociación al médico. | H3 y resolución de ambigüedad de médico. | 5–8 h |
| H5 — Cierre de Entrega 3 y auditoría | Completar datos, capturas, Bitácora y reflexión; verificar las cuatro aplicaciones y preparar archivos de entrega. | Paquete reproducible y checklist sin pendientes obligatorios. | H1–H4. | 3–5 h |

Total preliminar: **24–38 horas de equipo**. Reservar aproximadamente 20 % para correcciones: **29–46 horas**. No se asignan fechas sin conocer vencimientos y disponibilidad.

La revisión de los PDFs bloquea la validación definitiva de los requisitos, pero permite avanzar con borradores de visión, backlog y matriz de pruebas usando la guía como fuente provisional.

## 4. Backlog inmediato

| ID de tarea | Entrega / vínculo | Trabajo | Prioridad |
|---|---|---|---|
| T01 | Todas | Auditar fuentes y registrar requisitos, ejemplos y puntos no especificados. | P0 |
| T02 | E1 | Documento de Visión, ocho epics y backlog. | P0 |
| T03 | Todas | Preparar Planilla Scrum, objetivos de sprints, tareas y Bitácora. | P0 |
| T04 | E2 / HU-01 | Tabla Pacientes, alta, DNI único y número de HC. | P0 |
| T05 | E2 / HU-02 | Búsqueda por DNI, detalle y paciente inexistente. | P0 |
| T06 | E2 | Datos ficticios, pruebas, tres capturas y reflexión. | P0 |
| T07 | E3 / HU-01 y HU-02 | Primera GUI: registrar, buscar y ver todos. | P0 |
| T08 | E3 / ampliación Sprint 2 | Modificar contacto/cobertura y eliminar paciente. | P0 |
| T09 | E3 / HU-03 | Signos, motivo, fecha/hora, historial y acceso por doble clic. | P0 |
| T10 | E3 / integridad | Eliminar signos y paciente conjuntamente; comprobar ausencia de huérfanos. | P0 |
| T11 | E3 | Datos finales, tres capturas, objetivo actualizado y reflexión. | P0 |
| T12 | Todas | Revisión cruzada y ejecución desde una copia preparada para entregar. | P0 |

P0 identifica trabajo necesario para cerrar el alcance; la secuencia de hitos determina el orden. Estos IDs son tareas internas, no nuevas HHUU atribuidas al docente.

## 5. Organización del equipo propuesta

Definir un responsable y un revisor por tarea. Una persona puede asumir varias funciones según la cantidad de integrantes.

| Función de trabajo | Responsabilidad |
|---|---|
| Coordinación y documentación | Mantener alcance, visión, backlog, objetivos de sprint y pendientes. |
| Datos y lógica | SQLite, altas, búsquedas, actualizaciones, eliminaciones e integridad. |
| Interfaz | Tkinter, formularios, selección de pacientes, mensajes y navegación. |
| Calidad y evidencias | Ejecutar criterios de aceptación, verificar datos y completar Bitácora. |

Estas funciones no sustituyen los roles Scrum que deba documentar el equipo. Nombres y roles quedan pendientes; no se inventan integrantes.

La documentación y los casos de prueba pueden avanzar mientras se desarrolla la consola. El trabajo de GUI comienza cuando esté acordado cómo acceder a los datos. Las capturas se obtienen al aprobar cada funcionalidad, no al final de todo el proyecto.

Cada integrante debe poder explicar el flujo completo: entrada, validación, consulta SQL, resultado y evidencia.

## 6. Decisiones técnicas propuestas

- Mantener Python, SQLite y Tkinter como indica la guía.
- Usar el repositorio actual como raíz del proyecto; no crear otra carpeta OpenHIS-UNLaM anidada sin necesidad.
- Conservar los cuatro puntos de entrada pedidos: `Pacientes.py`, `Pacientes_app.py`, `Pacientes2_app.pyw` y `Pacientes2b_app.pyw`.
- Resolver la ruta de `BD/Salud.db` respecto de los archivos del proyecto, para evitar crear otra base al ejecutar desde una carpeta distinta.
- Usar consultas parametrizadas y la restricción UNIQUE de SQLite para DNI; traducir los errores a mensajes comprensibles.
- Realizar la eliminación de signos y paciente en una misma transacción. La guía describe eliminación explícita desde Python; no atribuirle `ON DELETE CASCADE`.
- Comprobar la integridad referencial en las conexiones y evitar registros de signos para pacientes inexistentes.
- Evaluar un pequeño módulo compartido de acceso a datos para evitar duplicar reglas entre versiones, si las condiciones de entrega permiten archivos auxiliares. Si se usa, incluirlo en el paquete.
- Usar únicamente datos ficticios en la demostración y preparar un paciente adicional para las pruebas de baja. Tras las pruebas deben permanecer al menos cinco pacientes y al menos tres con signos.
- Conservar un estado identificable de cada entrega en Git y mantener las evidencias separadas por sprint.

Estas decisiones son propuestas de implementación; no agregan funcionalidades al alcance académico.

## 7. Pruebas y evidencias

| Entrega | Verificación | Evidencia de cierre |
|---|---|---|
| E1 | Visión y backlog coinciden; alcance implementado separado del futuro. | Documento revisado y matriz de requisitos. |
| E2 | Alta válida genera HC; búsqueda muestra detalle; DNI repetido se rechaza. | Tres capturas de ejecución real insertadas en Bitácora. |
| E2 | Paciente inexistente, persistencia al reiniciar, al menos cinco pacientes y búsqueda menor a dos segundos según HU-02. | Resultado de pruebas; registrar entorno y medición de búsqueda. |
| E3 | Alta, búsqueda, duplicado y listado funcionan en GUI; las versiones anteriores siguen ejecutando. | Matriz de pruebas de regresión. |
| E3 | Modificación de teléfono, email, domicilio y obra social persiste al volver a buscar. | Captura de modificación y comprobación posterior. |
| E3 | Signos asociados al paciente; motivo obligatorio; numéricos validados; fecha/hora automática. | Captura de alta de signos y comprobación en base. |
| E3 | Historial muestra últimos diez registros en orden descendente; botón y doble clic abren el paciente correcto. | Resultado registrado de la prueba. |
| E3 | Eliminar un paciente con signos elimina ambos sin afectar otros pacientes. | Captura y verificación en base de ausencia de paciente y registros asociados. |
| E3 | Al finalizar quedan cinco pacientes como mínimo y signos en tres pacientes como mínimo. | Consulta de conteos y verificación de asociaciones. |

La asociación al médico de HU-03 requiere resolver el punto de la sección siguiente antes de marcar la historia completa.

Formato propuesto para trazabilidad: `fuente/sección → epic → HU o requisito → criterio → tarea → archivo/función → prueba → evidencia → estado`.

Un requisito queda terminado cuando está implementado, probado y documentado con la evidencia correspondiente. Una captura de un mensaje de éxito no reemplaza la comprobación de persistencia o de integridad.

## 8. Pendientes y ambigüedades

| Punto | Estado y tratamiento |
|---|---|
| PDFs originales | No disponibles en el repositorio. Contrastar las afirmaciones de la guía antes de cerrar requisitos. |
| Plantilla Scrum | No disponible. Verificar si existe una planilla provista por la cátedra antes de definir otra estructura. |
| Fechas, plataforma y formato de E1 | No especificados en la fuente disponible. Mantener pendientes y no inventar condiciones. |
| Integrantes y disponibilidad | Pendientes. El calendario y la asignación nominal dependen de estos datos. |
| HU-04 a HU-09 | La guía lista sus IDs, pero no desarrolla sus textos y criterios. Recuperarlos del PDF; no presentarlos como definidos. |
| Epics 4 a 8 | La guía indica HHUU por definir. Distinguir historias propuestas por el equipo de historias tomadas de la consigna. |
| Asociación al médico en HU-03 | El criterio la pide, pero la guía describe `medico_id` como preparación futura. Un campo vacío no demuestra cumplimiento. Revisar el PDF y documentar la solución o el pendiente, sin construir por defecto todo el módulo de profesionales. |
| Baja física o lógica | Plan provisional: eliminación física según la versión final descrita. La baja lógica aparece como alternativa y no se incorpora automáticamente. |
| Tres versiones de GUI | La guía pide entregar las tres. Verificar si deben ser independientes o si se admiten módulos auxiliares compartidos. |
| Validaciones y reglas clínicas | Separar validación de formato numérico de rangos clínicos no especificados. No inventar umbrales médicos. |

## 9. Organización de archivos propuesta

```text
OpenHIS-UNLaM-Equipo2/
├── Guia_Entregas_1_2_y_3_OpenHIS_UNLaM.md
├── PLAN_PROYECTO.md
├── README.md
├── Pacientes.py
├── Pacientes_app.py
├── Pacientes2_app.pyw
├── Pacientes2b_app.pyw
├── BD/
│   └── Salud.db
├── docs/
│   ├── entrega-1-vision.md
│   ├── backlog.md
│   ├── matriz-requisitos-pruebas.md
│   ├── reflexion-sprint-1.md
│   └── reflexion-sprint-2.md
├── scrum/
│   └── Planilla Scrum.xlsx
└── evidencias/
    ├── sprint-1/
    └── sprint-2/
```

La estructura es una propuesta, no un inventario de archivos ya creados. El formato final de la visión se ajustará a la consigna de entrega.

## 10. Orden de inicio

1. Completar el contraste de fuentes y registrar pendientes en la matriz.
2. Preparar el borrador de visión y backlog con fuente explícita para cada requisito.
3. Identificar integrantes, responsables, disponibilidad y vencimientos para convertir hitos en calendario.
4. Preparar Scrum y los casos de aceptación de HU-01 y HU-02.
5. Ejecutar H2 y cerrar la Entrega 2 con sus evidencias antes de evolucionar a la GUI.
