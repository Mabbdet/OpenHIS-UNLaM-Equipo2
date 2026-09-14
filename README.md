# OpenHIS-UNLaM — Equipo 2

Sistema de información hospitalaria educativo desarrollado por Alejandro. Alcance actual: pacientes (HU-01 a HU-03), tablas maestras (HU-04), profesionales (HU-05, con vigencia real de matrícula pendiente) y prescripciones exigidas en Entrega 4 (avance parcial de HU-06).

## Ramas por entrega

Las ramas son acumulativas y locales. Cada incremento se verifica, se integra a `develop` y recién entonces se crea la siguiente rama desde `develop`. No se publica automáticamente en el remoto.

| Rama | Incremento |
|---|---|
| `develop` | Integra las entregas verificadas. |
| `develop-Entrega1` | Documento de Visión y plan de proyecto. |
| `develop-Entrega2` | Consola para HU-01/HU-02, SQLite y pruebas simples con pytest. |
| `develop-Entrega3` | Versiones gráficas, CRUD completo, HU-03 e historial. |
| `develop-Entrega4` | Tablas maestras, profesionales, autor de signos vitales, prescripciones y evidencias del Sprint 3. |

## Ejecución

Requiere Python 3.10 o posterior. La aplicación usa solamente la biblioteca estándar.

```powershell
python cargar_demo.py
python Pacientes.py
python Pacientes_app.py
python Pacientes2_app.pyw
python Pacientes2b_app.pyw
```

`Pacientes.py` conserva la consola; `Pacientes_app.py` permite alta, búsqueda y listado; `Pacientes2_app.pyw` agrega modificación y baja; `Pacientes2b_app.pyw` agrega signos vitales, historial y acceso a Tablas maestras, Profesionales y Prescripciones. Esta última es el punto de entrada principal actual. Con Python configurado en Windows, la extensión `.pyw` permite abrirla sin consola.

`BD/Salud.db` incluye cinco pacientes ficticios, signos con profesional en tres de ellos, seis profesionales de seis especialidades y siete prescripciones ficticias. Incluye los registros generados para las capturas. `cargar_demo.py` puede repetirse sin duplicar sus registros ni reemplazar fichas existentes. Sus códigos, fármacos, dosis y vías son ficticios. La HC es el identificador único del paciente en SQLite.

`datos.py`, `esquema.py`, `interfaz.py` y `ventanas_clinicas.py` son módulos auxiliares necesarios y deben incluirse en el paquete. La base se ubica respecto de los archivos del proyecto, independientemente de la carpeta desde la que se ejecute el programa. La GUI requiere Tkinter; para comprobar el entorno: `python -m tkinter`.

Los módulos nuevos también pueden abrirse por separado:

```powershell
python Tablas_maestras_app.pyw
python Profesionales_app.pyw
python Prescripcion_app.pyw
```

## Uso de la interfaz final

1. Registrar: completar los campos obligatorios y guardar. Se muestra la HC generada.
2. Buscar: ingresar DNI; el resultado queda seleccionado y su ficha aparece debajo del listado. Ver todos restaura el listado completo.
3. Modificar: seleccionar un paciente y editar teléfono, email, domicilio u obra social.
4. Signos: seleccionar un paciente y pulsar Signos, o hacer doble clic en su fila. Elegir profesional, ingresar mediciones y motivo, y guardar; el historial se actualiza.
5. Eliminar: seleccionar y confirmar la baja. Se eliminan físicamente el paciente y sus signos en una misma transacción, siempre que no tenga prescripciones, incluso anuladas.
6. Tablas maestras: crear especialidades, códigos SNOMED locales y fármacos. Las especialidades se pueden modificar o desactivar.
7. Profesionales: registrar con DNI, matrícula y especialidad activa; buscar por DNI, modificar contacto/especialidad o eliminar si no tiene signos ni prescripciones asociados.
8. Prescripciones: seleccionar paciente, profesional y fármaco; completar dosis, vía y frecuencia. Se pueden consultar por DNI del paciente, ver el detalle y anular conservando el registro.

## Pruebas sencillas

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Última ejecución: **48 pruebas aprobadas, ninguna omitida**. Usan bases temporales de pytest: pacientes, signos, catálogos, profesionales, prescripciones, validaciones, integridad referencial, migración y carga demo repetible. También se comprueba la apertura de las nuevas ventanas y el selector de profesional. No modifican `BD/Salud.db`. Los tests de GUI se omiten explícitamente si el entorno no dispone de Tk; los tests de datos siguen ejecutándose.

## Validaciones

DNI numérico sin separadores; nombre, apellido, fecha de nacimiento y sexo obligatorios. Fecha válida con formato AAAA-MM-DD, no futura; sexo M/F según la guía. Contacto, domicilio y obra social son opcionales conforme al esquema. La validación de formato de fecha y DNI es una decisión de implementación.

En signos vitales, el motivo es obligatorio; las mediciones pueden dejarse vacías y se guardan como NULL. Presiones, frecuencia y saturación admiten enteros; temperatura admite decimales con punto o coma y rechaza valores no finitos. No se agregan umbrales ni interpretaciones clínicas. El historial presenta los diez últimos registros; en igualdad de fecha/hora se ordena por ID descendente. Las fechas automáticas de SQLite se muestran identificadas como UTC.

Los nuevos signos requieren `medico_id` válido, relacionado con Profesionales. La migración conserva los signos históricos sin autor y permite asignarles su autor confirmado desde la ventana de signos. No inventa autores; la base demo entregada tiene todos sus signos asociados.

Las matrículas son obligatorias y únicas; su vigencia real no se consulta en un registro oficial. Las prescripciones requieren relaciones válidas, dosis, vía y frecuencia; las fechas opcionales deben ser válidas y la final no puede preceder a la inicial. No se implementan reportes/XML, FHIR, control de acceso, turnos ni SMS.

## Documentación y evidencias

Consultar `docs/entrega-4.md`, `docs/verificacion.md`, `PLAN_PROYECTO.md` y las reflexiones de cada sprint. Entrega 4 incluye cuatro capturas reales en `evidencias/sprint3/`, embebidas en `scrum/Planilla Scrum.xlsx` → Bitácora, y la reflexión de dos párrafos en `docs/reflexion-sprint-3.md`. La copia Scrum conserva fechas y estados heredados de la plantilla; estos no certifican avance. Las capturas de las entregas anteriores siguen pendientes y no se sustituyen por estas evidencias de Sprint 3.

Alejandro asume desarrollo, coordinación, documentación y pruebas; se conserva al profesor como Product Owner en la plantilla. Los PDFs originales, formato y fecha final de entrega no están confirmados. La guía ampliada de entregas 1–4 es la fuente del incremento actual.
