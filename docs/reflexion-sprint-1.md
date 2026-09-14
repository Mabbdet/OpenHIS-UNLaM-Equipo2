# Reflexión — Sprint 1

El módulo centraliza la identificación de pacientes del Hospital Universitario San Justo: permite registrar sus datos y recuperar una ficha por DNI. La restricción de unicidad evita registrar dos fichas con el mismo DNI y el número de Historia Clínica identifica cada registro dentro del sistema. Esto contribuye a reducir duplicaciones y facilita localizar información administrativa; no resuelve por sí solo todas las posibles inconsistencias de identidad.

Una identificación consistente es una base para intercambiar información clínica entre sistemas. FHIR representa datos del paciente mediante el recurso Patient; una futura integración deberá definir cómo mapear los identificadores y los datos de esta aplicación. El Sprint 1 no implementa FHIR: organiza información de pacientes y prepara una base sobre la que podría desarrollarse esa interoperabilidad.
