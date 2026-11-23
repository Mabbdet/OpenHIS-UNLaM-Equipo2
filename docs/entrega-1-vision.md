# OpenHIS-UNLaM — Documento de Visión

Documento de Visión del Equipo 2, actualizado al cierre de la entrega final el 22/11/2026. La formulación inicial parte de la guía del repositorio y la plantilla Scrum. Las matrices de las entregas 4, 5, 7, 9 y 10 y la hoja Revisión de Scrum registran las fuentes utilizadas en cada incremento.

## Institución y problema

El Hospital Universitario San Justo es una institución ficticia de mediana complejidad con actividad asistencial, docente y de investigación. Comprende guardia, consultorios externos, diagnóstico por imágenes, laboratorio, farmacia, quirófanos, internación, terapia intensiva y enfermería.

Sus sistemas independientes fragmentan la información entre admisión, turnos, laboratorio, imágenes, farmacia, internación y facturación. Esto favorece pacientes duplicados, errores de identificación, historias incompletas y demoras para recuperar antecedentes y resultados.

## Objetivo y alcance actual

Construir incrementalmente un sistema hospitalario educativo que centralice procesos administrativos y clínicos. El alcance implementado comprende gestión de pacientes y profesionales, signos vitales, prescripciones, catálogos, seguridad y auditoría, intercambio FHIR, herramientas DICOM, agenda profesional, turnero telefónico, recordatorios locales e historia clínica electrónica. El portal web de pacientes amplía la gestión de turnos. Desde la entrega 5, las bajas son lógicas y reversibles y conservan las intervenciones.

El escritorio utiliza los roles de administrador, administrativo, médico y enfermero, con permisos específicos. El paciente dispone de acceso individual al portal para gestionar sus turnos. La asignación de camas pertenece a la visión conceptual del hospital y queda fuera del alcance implementado.

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
| 1 | Gestión de pacientes | HU-01 a HU-03 implementadas. |
| 2 | Gestión de profesionales e intervenciones | HU-04 a HU-10 implementadas, incluidos catálogos, prescripciones, seguridad, consulta, FHIR y DICOM. |
| 3 | Agenda, turnos e HCE | HU-11 a HU-23 implementadas en la entrega final. El portal web es una ampliación opcional. |
| 4 | Seguridad y autenticación, eje conceptual | Cubierto por HU-07 y los permisos de los módulos posteriores. |
| 5 | Historia clínica electrónica, eje conceptual | Cubierto por HU-19 a HU-23. |
| 6 | Imágenes médicas / DICOM, eje conceptual | Cubierto por HU-10 y las herramientas de las entregas 9 y 10. |
| 7 | Interoperabilidad / HL7 / SNOMED, eje conceptual | Intercambio FHIR y catálogo de terminología incorporados. |
| 8 | Inteligencia artificial, eje conceptual | Trabajo independiente de OpenHIS, informado como realizado por Alejandro. |

La numeración consolidada de las 23 historias figura en Scrum. HU-07 corresponde a seguridad, HU-09 a FHIR y HU-11 a HU-23 a agenda, turnos e HCE. Los recordatorios implementados se preparan en una cola local.

## Historias y aceptación del alcance actual

| HU | Historia | Criterios recogidos en la guía |
|---|---|---|
| HU-01 | Como administrativo, quiero registrar un nuevo paciente con sus datos personales para crear su ficha en el sistema. | Datos personales y contacto/cobertura; DNI no duplicado; número de HC único. El esquema incorpora apellido, sexo y fecha de nacimiento. |
| HU-02 | Como administrativo, quiero buscar un paciente por DNI para acceder rápidamente a su ficha. | Búsqueda por DNI en menos de dos segundos; nombre completo, número de HC y detalle. |
| HU-03 | Como médico, quiero registrar el motivo de consulta y los signos vitales del paciente en la admisión. | Presión arterial, frecuencia cardíaca, temperatura, motivo, fecha/hora automática y asociación al médico. La evolución incluye saturación e historial. La asociación al profesional se implementó en la entrega 4. |

## Incrementos

- Entrega 1: visión y planificación.
- Entrega 2 / Sprint 1: HU-01 y HU-02 por consola, Python y SQLite.
- Entrega 3 / Sprint 2: Tkinter, CRUD de pacientes, HU-03 e historial.
- Entregas 4 y 5 / Sprint 3. Profesionales, tablas maestras, prescripciones, bajas lógicas y reportes XML/HTML.
- Entrega 7 / Sprint 4. Autenticación, permisos y auditoría.
- Entregas 9 y 10 / Sprint 5. Intervenciones, intercambio FHIR, preanálisis y herramientas DICOM.
- Entrega final / Sprints 6 a 10. Agenda, turnero telefónico, recordatorios e HCE, con ampliación opcional del portal web.

La planificación detallada figura en `PLAN_PROYECTO.md`. El Equipo 2 está integrado por Alejandro, Scrum Master y desarrollador, y Leonel, desarrollador. Ambos comparten implementación, documentación y pruebas. La planilla Scrum identifica al responsable de cada tarea. Mg. Bioing. María Susana Burioni figura como Product Owner.

## Supuestos y límites

- Se utilizan datos ficticios para desarrollo, demostración y pruebas.
- La HC es el `id` autoincremental del paciente en esta etapa.
- Patient y Observation son referencias conceptuales a FHIR. Las primeras tres entregas no implementan intercambio FHIR.
- El formato final, plataforma, vencimientos y criterios no reproducidos en las fuentes disponibles quedan pendientes.
- Las evidencias deben proceder de ejecuciones reales y la planilla debe reflejar los objetivos de los sprints.
