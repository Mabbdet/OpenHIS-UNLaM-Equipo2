# Entrega 10 — Cierre técnico del Epic 2

Fuente: `Sist-Info-Salud-10.pdf`, páginas 7–18 (herramientas DICOM), 19–27 (FHIR), 42–45 (aceptación y evidencias). Rama `develop-Entrega10`, desde `0b31f12`. Equipo: Alejandro y Leonel; Scrum Master: Alejandro. Trabajo del 21/11/2026 (Argentina).

## Resultado

| Requisito | Implementación | Verificación |
|---|---|---|
| DICOM integrado al menú por rol | `DICOMVisorApp`, con conversión, anonimización y tercera pestaña Visor DICOM | Apertura con los permisos existentes |
| Vincular datos de pacientes/profesionales | Selectores consultan la base; campos editables para identificación, nacimiento, sexo, fechas/horas, solicitante/realizador e institución | DICOM generado desde la ficha ficticia HC 3 |
| Metadatos completos | Incluye file_meta y dataset; recorre secuencias; abrevia valores largos y representa bytes por su longitud | Pruebas con secuencias, identificadores anidados y valores largos |
| Vista previa básica | Escala de grises 8/16 bits, signed y BitsStored; endian little/big; MONOCHROME1; RGB 8 intercalado/planar | Pruebas numéricas de píxeles y captura con patrón sintético |
| Formato no admitido | Conserva metadatos y muestra motivo cuando no hay imagen, está comprimida o usa representación no soportada | Pruebas de cada caso |
| Última visualización | Acción Q con usuario, ruta y resultado del preview; no agrega atributos al DICOM | Hash de archivo intacto y auditoría real |
| Análisis FHIR sin escritura | `preparar_importacion`: backup SQLite en memoria y simulación allí | SHA-256 de Salud.db idéntico antes/después |
| JSON y resumen revisables | Muestra documento y acciones previstas; bloquea el botón de confirmación si falla el análisis | Captura de preanálisis y pruebas de referencias/dosis inválidas |
| Confirmación explícita | Botón separado y diálogo; cancelar conserva la base | Prueba del callback real con respuesta negativa y afirmativa |
| Plan vigente | Verifica hash del archivo y huella de datos relevantes bajo bloqueo de escritura | Cambio de archivo, base o permiso impide confirmar |
| Importación atómica | Un único lote con auditoría y rollback | Pruebas previas y nuevas |
| Observations agrupadas | Paciente, fecha UTC, profesional y estado; valores incompatibles se rechazan | Cuatro mediciones nuevas en un único SignosVitales |
| Fármacos y dosificación | Busca por código y luego nombre; admite dosis estructurada, vía codificada y timing.repeat | Prueba sin duplicar catálogo |
| Carpetas pedidas | `IMAGENES/RX/DICOM` | Imagen sintética y archivos DICOM de ejemplo |
| Evidencias | Cuatro capturas embebidas en Scrum, archivos y reflexión | Bitácora desde fila 720 |

## Uso

```powershell
python -m pip install -r requirements.txt
python OpenHIS_app.pyw
```

Se conservan las cuentas y permisos anteriores. El administrador entra a FHIR; admin, médico y enfermero pueden usar DICOM. Las entradas independientes `_Interoperabilidad_FHIR.pyw`, `_Herramientas_DICOM_Visor.pyw` y el acceso anterior `_Herramientas_Dicom.pyw` llegan a las versiones actuales mediante login. Se adaptó la implementación compartida; no es necesario mantener una copia ejecutable vieja con prefijo `xxx`.

En FHIR, seleccionar un archivo mediante **Analizar y mostrar**, revisar el resumen y el JSON y después pulsar **Confirmar e importar a Salud.db**. La respuesta negativa al diálogo no escribe. Cambiar el origen invalida el plan. Si cambia el archivo o la base relevante, se exige analizar otra vez. Los cambios del log de auditoría o del último acceso, por sí solos, no invalidan el plan.

En DICOM, la primera pestaña permite completar metadatos o traerlos de fichas existentes; la segunda conserva la anonimización básica y la tercera muestra el archivo. Los campos desconocidos permanecen vacíos. El nombre y DNI vinculados hacen que la conversión se marque como no anonimizada; la copia anonimizada conserva solo años/sexo y atributos técnicos según Entrega 9.

El visor no requiere NumPy, no decodifica compresiones y admite un cuadro de hasta 16 millones de píxeles. Ajusta el rango de grises de 16 bits para inspección; no es una herramienta diagnóstica ni aplica calibración clínica. Los píxeles y metadatos originales no se modifican. La anonimización sigue siendo básica y requiere revisar identificadores incrustados en píxeles.

## Intercambio y compatibilidad

Se mantienen JSON y XML, ServiceRequest, la reutilización de DNI incluso inactivos y el control de reimportaciones. La simulación usa el mismo importador sobre una copia en memoria, de modo que errores de asociaciones, matrícula, obligatoriedad y restricciones SQLite se detectan antes de confirmar. La confirmación vuelve a validar el estado y ejecuta la importación real dentro de una transacción.

Las mediciones se agrupan por paciente, profesional, fecha normalizada y estado. Se conserva el vínculo de cada recurso externo con la fila correspondiente. Si una medición ya existe con el mismo paciente, fecha, código y valor, se reutiliza; los valores nuevos se agrupan sin sobrescribir registros históricos. Dos valores diferentes para el mismo campo dentro de un grupo bloquean el lote.

El esquema de Entrega 9 ya admite profesionales externos con nacimiento/género desconocidos. Se conserva esa representación explícita en lugar de inventar datos o recuperar la restricción anterior del ejemplo docente. La dosis ausente se rechaza; dosis estructurada, ruta por coding y frecuencia estructurada se traducen al modelo local. El alcance FHIR continúa siendo académico y limitado a los recursos/mapeos documentados en Entrega 9.

## Evidencias y base entregada

`intercambio/e10_recibido_sintetico.json` contiene cuatro Observations para un paciente y profesional ficticios existentes. En el preanálisis se comprobó que el archivo SQLite real no cambió; los hashes están en `evidencias/entrega10/verificacion_preanalisis.json`. Al confirmar se creó un SignosVitales con presión 121/81, pulso 75 y temperatura 36,7, asociado al paciente HC 3 y profesional 3. El resultado está en `resultado_importacion.json`.

`01_preanalisis.jpg` captura el análisis real, sin escritura. `02_importacion.jpg` muestra el resumen real guardado después de confirmar la demostración. `03_visor.jpg` muestra metadatos e imagen; `04_auditoria.jpg` muestra I/E/Q con usuario autenticado. El callback gráfico de confirmación se probó por separado con ambas respuestas.

La imagen artificial está en `IMAGENES/RX/imagen_sintetica_e10.png`. `e10_vinculado.dcm` contiene metadatos de la ficha ficticia seleccionada; `e10_anonimizado.dcm` es su copia anonimizada. El texto completo del visor y la comprobación de archivo intacto están en `evidencias/entrega10/`. No se usaron imágenes ni datos clínicos reales.

## Verificación y estado de Git

**142 pruebas aprobadas, ninguna omitida**, incluidas las 121 anteriores y 21 nuevas. Comando: `.venv/Scripts/python.exe -m pytest -q -rs -p no:cacheprovider`. Incluyen análisis sin escritura, cancelación, confirmación, planes obsoletos, agrupación y conflictos, fármacos/dosis, formatos de píxeles y GUI. La base conserva los registros preexistentes y pasa integridad y claves foráneas; solo agrega el signo agrupado, sus cuatro referencias externas y auditoría de las operaciones. Las cuentas utilizadas actualizan su último acceso.

Antes de iniciar esta entrega se publicaron `develop-Entrega5`, `develop-Entrega7`, `develop-Entrega9` y `develop` en el remoto del proyecto. Los tres commits figuran a nombre de Ale, sin trailers de coautoría. Entrega 10 se integra localmente después de verificar; su publicación no se realiza automáticamente. Las correcciones anteriores sin commit y los archivos Arduino se conservan.

Al cerrar la entrega 10, Scrum conservó las veinte imágenes anteriores y agregó cuatro. La revisión final del 22/11/2026 concilió las fórmulas, las 23 historias y los 10 sprints. La entrega final implementó agenda profesional, turnero telefónico, recordatorios e HCE, y agregó el portal web opcional de pacientes. Sus evidencias están en `evidencias/entrega-final/`, `evidencias/turnero-web/` y la Bitácora.

Referencias técnicas: [SQLite backup](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup), [píxeles DICOM con pydicom](https://pydicom.github.io/pydicom/stable/guides/user/working_with_pixel_data.html), [Pillow Image](https://pillow.readthedocs.io/en/stable/reference/Image.html).
