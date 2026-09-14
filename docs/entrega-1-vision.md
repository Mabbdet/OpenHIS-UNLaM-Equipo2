# OpenHIS-UNLaM — Documento de Visión

Documento provisional del Equipo 2. Fuentes: guía del repositorio y Planilla-Scrum-Profe.xlsx aportada por el usuario. Pendiente de contraste con los PDFs originales. Integrantes y roles propios del equipo: no informados.

## Institución y problema

El Hospital Universitario San Justo es una institución ficticia de mediana complejidad con actividad asistencial, docente y de investigación. Comprende guardia, consultorios externos, diagnóstico por imágenes, laboratorio, farmacia, quirófanos, internación, terapia intensiva y enfermería.

Sus sistemas independientes fragmentan la información entre admisión, turnos, laboratorio, imágenes, farmacia, internación y facturación. Esto favorece pacientes duplicados, errores de identificación, historias incompletas y demoras para recuperar antecedentes y resultados.

## Objetivo y alcance actual

Construir incrementalmente un sistema hospitalario educativo que centralice procesos administrativos y clínicos. El alcance de implementación actual es Epic 1: registrar y buscar pacientes, registrar motivo de consulta y signos vitales, y consultar su historial. Sprint 2 agrega interfaz gráfica, modificación de datos de contacto/cobertura y baja física con eliminación de signos asociados.

Actores actuales: administrativo y médico. Actores futuros descritos en la planilla: recepcionista y paciente que solicita turnos por web. La asignación de camas aparece en la visión amplia de Epic 1, pero no está desarrollada como funcionalidad de estas entregas.

## Flujo y capas

Flujo conceptual: persona → admisión → paciente → turno → profesional → atención → historia clínica → diagnóstico → tratamiento → estudios → resultados → facturación.

| Capa | Contenido conceptual |
|---|---|
| Gestión administrativa | Pacientes, profesionales, especialidades, turnos, admisión, coberturas, prestaciones y facturación. |
| Clínica asistencial | Consultas, antecedentes, alergias, signos vitales, problemas, diagnósticos, procedimientos, medicación y evolución. |
| Interoperabilidad | Identificadores, terminologías, SNOMED CT, HL7 y FHIR. |
| Tecnologías de salud | DICOM, PACS, laboratorio, dispositivos, IoT e IA. |

## Backlog conceptual

| Epic | Contenido | Tratamiento |
|---|---|---|
| 1 | Gestión de pacientes | HU-01, HU-02 y HU-03: implementación actual. |
| 2 | Gestión de profesionales | La planilla desarrolla HU-04 a HU-08: tablas maestras, profesionales, prescripción, FHIR y consulta de intervenciones. Futuro. |
| 3 | Gestión de turnos | La planilla desarrolla HU-09 a HU-11: agenda, reserva web y SMS. Futuro. |
| 4 | Seguridad y autenticación | Historias por definir según la guía. |
| 5 | Historia clínica electrónica | Historias por definir según la guía. |
| 6 | Imágenes médicas / DICOM | Historias por definir según la guía. |
| 7 | Interoperabilidad / HL7 / SNOMED | Historias por definir y relación con Epic 2 por conciliar. |
| 8 | Inteligencia artificial | Historias por definir según la guía. |

No se reasignan IDs silenciosamente: la guía ubica originalmente HU-07 a HU-09 en turnos; la planilla los organiza de otra manera.

## Historias y aceptación del alcance actual

| HU | Historia | Criterios recogidos en la guía |
|---|---|---|
| HU-01 | Como administrativo, quiero registrar un nuevo paciente con sus datos personales para crear su ficha en el sistema. | Datos personales y contacto/cobertura; DNI no duplicado; número de HC único. El esquema incorpora apellido, sexo y fecha de nacimiento. |
| HU-02 | Como administrativo, quiero buscar un paciente por DNI para acceder rápidamente a su ficha. | Búsqueda por DNI en menos de dos segundos; nombre completo, número de HC y detalle. |
| HU-03 | Como médico, quiero registrar el motivo de consulta y los signos vitales del paciente en la admisión. | Presión arterial, frecuencia cardíaca, temperatura, motivo, fecha/hora automática y asociación al médico. La evolución incluye saturación e historial. La planilla programa la integración del profesional para Sprint 3; queda diferida y debe declararse como tal. |

## Incrementos

- Entrega 1: visión y planificación.
- Entrega 2 / Sprint 1: HU-01 y HU-02 por consola, Python y SQLite.
- Entrega 3 / Sprint 2: Tkinter, CRUD de pacientes, HU-03 e historial.
- Continuidad de la planilla: Sprint 3 profesionales y tablas maestras; Sprint 4 prescripción y FHIR; Sprint 5 consulta de intervenciones; Sprint 6 agenda; Sprint 7 reserva web y SMS.

La planificación detallada y sus estimaciones son propuestas en `PLAN_PROYECTO.md`. La planilla identifica a Mg. Bioing. María Susana Burioni como Product Owner; los nombres de ejemplo no se atribuyen al equipo. Scrum Master y desarrolladores del Equipo 2: pendientes de informar.

## Supuestos y límites

- Se utilizan datos ficticios para desarrollo, demostración y pruebas.
- La HC es el `id` autoincremental del paciente en esta etapa.
- Patient y Observation son referencias conceptuales a FHIR. Las primeras tres entregas no implementan intercambio FHIR.
- El formato final, plataforma, vencimientos y criterios no reproducidos en las fuentes disponibles quedan pendientes.
- Las evidencias deben proceder de ejecuciones reales y la planilla debe reflejar los objetivos de los sprints.
