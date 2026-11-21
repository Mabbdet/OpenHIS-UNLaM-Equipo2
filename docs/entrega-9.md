# Entrega 9 — Sprint 5

Fuente principal: `Sist-Info-Salud-9.pdf`, páginas 4–6 (HU-08/09/10), 7–14 (consulta y FHIR), 15–21 (DICOM y evidencias). Se utilizó `Practico_Integrador_FHIR_Semana_11.pdf` como referencia de asociación de pacientes/profesionales y recursos. Rama `develop-Entrega9`, desde `b6a31ab`, con integración local a develop después de verificar. Equipo: Alejandro y Leonel; Scrum Master: Alejandro.

## Requisitos y resultados

| Historia / criterio | Implementación | Evidencia |
|---|---|---|
| HU-08: localizar paciente por DNI/nombre/apellido | Selector de pacientes, incluidos inactivos, con búsqueda | `01_consulta.jpg` |
| HU-08: consolidar intervenciones y medicación | Signos, prescripciones y prácticas con profesional, fechas y estados | Consulta de paciente ficticio HC 3 |
| HU-08: trazabilidad | Acción Q con usuario, paciente y fecha UTC | `04_auditoria.jpg`; tabla Auditoria |
| HU-09: exportar intercambio estructurado | Bundle collection FHIR R4 en JSON y XML | `intercambio/e9_exportado.json` y `.xml` |
| HU-09: importar y asociar recursos | Patient, Practitioner, ServiceRequest, MedicationRequest y Observation | `e9_recibido_sintetico.json`; resultado guardado y captura FHIR |
| HU-09: no duplicar identidades por DNI | Busca activos e inactivos; reutiliza el ID y conserva datos locales | Pruebas con fichas inactivas; paciente existente reutilizado en demostración |
| HU-09: evitar reimportaciones accidentales | Registro por institución, tipo e ID externo; contenido distinto cancela el lote | Reimportación sin altas nuevas |
| HU-09: mediciones repetidas | Compara paciente, fecha UTC normalizada, código y valor | Cinco mediciones exportadas omitidas por ser idénticas a las locales |
| HU-09: registrar operaciones | E al exportar; I al importar; C cuando difieren nombres de una identidad reutilizada | Auditoría y `resultado_intercambio.json` |
| HU-10: JPG/PNG a Secondary Capture | Conversión a gris de 8 bits; escritura DICOM con cabecera y metadatos técnicos | Imagen sintética y `generado.dcm` |
| HU-10: anonimización básica | Reconstruye con lista permitida; elimina privados, secuencias, overlays y texto libre de metadatos | Entrada ficticia identificada y `anonimizado.dcm` |
| HU-10: conservar años y sexo | Año de nacimiento 1984, estudio 2026 y sexo F | `metadatos_anonimizados.json`, captura DICOM |
| HU-10: coherencia de UID y píxeles | Nuevos UID de estudio/serie/instancia; file_meta coincide; píxeles idénticos | `verificacion_dicom.json` y pruebas |
| Scrum y evidencias | Actualizados Sprint 5 y HU-08/09/10; cuatro capturas embebidas | Bitácora desde fila 560 |

## Ejecución

```powershell
python -m pip install -r requirements.txt
python OpenHIS_app.pyw
```

Se mantienen las cuentas ficticias de Entrega 7: `admin / admin123`, `medico_equipo2 / medico123`, `enfermero_equipo2 / enfermero123`, `administrativo_equipo2 / administrativo123`.

Los tres módulos se abren desde el menú autenticado o desde `_Consulta_intervenciones.pyw`, `_Interoperabilidad_FHIR.pyw` y `_Herramientas_Dicom.pyw`. Cada acceso pide login. Intervenciones y DICOM admiten admin/médico/enfermero. FHIR se reserva al administrador, siguiendo el permiso docente de exportar/importar intercambios; administrativo no accede a estos módulos.

FHIR permite registrar una solicitud de práctica con código local documentado, elegir paciente, exportar JSON/XML e importar un archivo indicando su institución de origen. Los archivos de salida se crean de manera exclusiva: no sobrescriben otros archivos. Si falla la auditoría, la importación revierte y una exportación recién escrita se retira.

DICOM permite seleccionar JPG/PNG, informar años y sexo, convertir, anonimizar y consultar metadatos. No sobrescribe el original. Se admite un cuadro con transferencia sin compresión. El patrón de ejemplo tiene 320 × 240 píxeles y no proviene de una radiografía.

## Contrato FHIR soportado

La consigna menciona XML, pero su código de ejemplo trabaja con JSON y solo valida el archivo recibido. Esta implementación acepta ambos formatos y persiste los recursos soportados. El XML usa el namespace oficial y atributos `value` para primitivas; el XML académico de prescripciones de Entrega 5 permanece independiente.

- Bundle `collection`, de 1 a 1000 entradas, hasta 5 MB. IDs y referencias deben ser únicos y resolubles dentro del archivo. No se descargan referencias remotas.
- Patient requiere DNI numérico, nombre, apellido y nacimiento completo. Practitioner nuevo requiere DNI, nombre, apellido y matrícula. La especialidad ausente queda explícitamente no informada; nacimiento ausente queda NULL y género desconocido U. No se inventan datos clínicos. Las altas manuales locales mantienen sus validaciones anteriores.
- ServiceRequest se guarda en Practicas, con código/sistema/descripción, paciente, profesional, fecha y autor. MedicationRequest se asocia a Prescripciones y al catálogo de fármacos. La cantidad, cuando se informa, debe ser un entero positivo compatible con el modelo local. Dosis, vía o frecuencia faltantes se identifican como no informadas; la representación original se conserva en RecursosFHIR.
- Observation admite valores numéricos finitos para presión sistólica/diastólica, frecuencia cardíaca, temperatura y saturación, con los códigos LOINC y unidades usados por la guía. Cada observación escalar nueva se guarda como un registro de signos. No se admiten paneles por componentes, recursos contenidos, Medication como referencia separada ni otros perfiles no implementados.
- Se aceptan referencias relativas o fullUrl, incluso si las entradas están en distinto orden. La identidad local se resuelve por DNI independientemente del system del identifier. Se usa el primer identifier como DNI, según el contrato de los ejemplos; archivos con otra organización deben adaptarse explícitamente.
- Registros inactivos no se duplican ni reactivan al recibir historia externa. Un mismo ID externo con contenido distinto cancela el lote completo. Una matrícula ya utilizada por otro DNI se rechaza. Los registros existentes no se sobrescriben automáticamente.
- Fechas completas y timestamps se normalizan. La aplicación local almacena sus fechas históricas sin zona como UTC; timestamps sin zona recibidos se interpretan también como UTC. Una integración con otro hospital debe acordar esa convención.

Es un subconjunto académico de FHIR R4, con validación de estructura, tipos, referencias y reglas de negocio del perfil soportado. No se ejecutó un validador integral de perfiles FHIR ni se certificó conformidad con guías nacionales. Los fullUrl de exportación usan un dominio ficticio `.example.invalid`.

## Demostración y archivos

La demostración exporta las intervenciones del paciente ficticio Ana López, HC 3. El archivo recibido sintético reutiliza ese paciente y describe un profesional externo diferente, sin nacimiento ni género informados. La primera importación creó una especialidad explícitamente no informada, un profesional, una práctica, un fármaco de origen externo y una prescripción. Las cinco mediciones ya existían y se omitieron. La repetición no creó registros. El resumen está en `evidencias/entrega9/resultado_intercambio.json`.

`02_fhir.jpg` muestra ese resumen real, guardado durante la primera ejecución y su repetición. La pantalla ejecutó además la reimportación para verificar el mismo comportamiento. `01_consulta.jpg` muestra las intervenciones locales y externas. `04_auditoria.jpg` muestra Q/I/E con autor y fecha UTC.

El DICOM generado se conserva intacto. Una copia de prueba, `entrada_identificada_ficticia.dcm`, agrega nombre, identificador, fechas completas y un tag privado ficticios para probar la anonimización. `anonimizado.dcm` deriva de esa copia. La comparación confirma píxeles idénticos, privados eliminados, UID nuevos y conservación de 1984/2026/F.

Los valores 01/01 de fechas DICOM representan solamente el año. Los píxeles no se modifican: nombres o identificadores impresos dentro de la imagen requieren revisión manual. La salida es Secondary Capture y la anonimización es básica; no es un procedimiento clínico certificado. Los tags técnicos se conservan para interpretar los píxeles y todas las secuencias externas se excluyen para evitar referencias originales o identificadores anidados.

La práctica de Semana 11 también solicita intercambio por correo con personas asignadas. Esta entrega prueba el intercambio local con una institución sintética; no se enviaron correos ni se presenta esa parte de la práctica posterior como realizada.

## Verificación y conservación

**121 pruebas aprobadas, ninguna omitida.** Se verificaron JSON/XML, importación/reimportación, referencias rotas y duplicadas, identidades inactivas, conflictos de matrícula, profesional sin datos opcionales, números/unidades/fechas inválidos, XML con DTD rechazado, permisos, rollback por error de auditoría, GUI de los tres módulos y anonimización con identificadores anidados/privados. Las 96 pruebas del incremento anterior siguen pasando; su matriz de menú incorpora los módulos nuevos.

```powershell
.\.venv\Scripts\python.exe -m pytest -q -rs -p no:cacheprovider
```

La migración amplía Profesionales para admitir datos externos incompletos y añade Practicas/RecursosFHIR y la acción Q. Se comparan todas las columnas anteriores contra el respaldo de Entrega 7, y se verifican integridad y claves foráneas. Scrum conserva pestañas, fórmulas e imágenes previas y añade cuatro capturas. La referencia rota histórica de `HU-UNLaM!I20` permanece documentada.

Referencias técnicas: [FHIR R4 Bundle](https://hl7.org/fhir/R4/bundle.html), [representación XML](https://hl7.org/fhir/R4/xml.html), [MedicationRequest](https://hl7.org/fhir/R4/medicationrequest.html) y [pydicom FileDataset](https://pydicom.github.io/pydicom/stable/reference/generated/pydicom.dataset.FileDataset.html).
