EJEMPLO HÍBRIDO FHIR. EQUIPO 2

Archivo
FHIR_44895843_hibrido_Equipo2.json

Procedencia
Los seis recursos originales se conservaron tal como aparecen en
intercambio/recibidos/Lautaro/FHIR_44895843_35734835_daSilva.json.
Incluyen a Bart Simpson, Julius Hibbert, tres observaciones y una prescripción.

El Equipo 2 agregó el ServiceRequest sr-equipo2-hibrido-bart-1, con código
local E2-HIB-01. La solicitud y su asociación a ese paciente y profesional
se generaron para la demostración académica. El recurso incluye etiquetas,
origen y nota que identifican esta procedencia. La plantilla de partida fue
nuestro FHIR_ServiceRequest_demostracion_local_Equipo2.json.

El archivo reúne siete recursos. Patient, Practitioner, MedicationRequest,
tres Observation y un ServiceRequest. Los valores recibidos se conservan
para reproducir el intercambio y pertenecen al ejemplo académico.

Comprobación realizada
Se utilizó el flujo de análisis y confirmación de la aplicación, con una
cuenta administradora y el origen "Demostración híbrida Equipo 2 / Lautaro".
Se probaron dos bases temporales.

1. Receptor vacío. Se importó el híbrido completo y después se reimportó.
2. Receptor con el original. Se importó primero el archivo de Lautaro y luego
   el híbrido, usando el mismo origen de importación para ambos archivos.
   Se agregó únicamente la práctica E2-HIB-01, vinculada a Bart y Julius.

El análisis y la cancelación conservaron los datos. La reimportación produjo
cero altas en ambos escenarios. SQLite pasó integridad y claves foráneas.

Para reproducir desde FHIR
Usar una base de demostración con acceso administrador. Seleccionar el archivo
híbrido, indicar el origen utilizado en el ensayo, analizar el lote y revisar
el JSON y sus acciones antes de confirmar. Repetir con el mismo origen permite
comprobar el control de duplicados.

Advertencias conservadas
Las observaciones recibidas carecen de profesional informado. Ese responsable
queda desconocido. Las fechas originales carecen de zona horaria y el importador
las interpreta como UTC. El profesional carece de código de titulación y se
registra con especialidad no informada. Estas advertencias quedan en el resultado.

Alcance académico
Este ejemplo acredita el funcionamiento técnico del lote híbrido. El
ServiceRequest tiene procedencia sintética del Equipo 2. La evaluación del
requisito de recepción de una práctica externa corresponde a la cátedra.

Resultados y huellas
evidencias/integrador-fhir/verificacion_hibrido.json
