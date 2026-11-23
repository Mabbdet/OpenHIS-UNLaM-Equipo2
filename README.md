# OpenHIS-UNLaM — Equipo 2

## Estado al cierre de la entrega final

Implementadas las entregas 1, 2, 3, 4, 5, 7, 9 y 10 y la entrega final. El escritorio integra pacientes, profesionales, signos, prescripciones, catálogos, usuarios, auditoría, intervenciones, FHIR, DICOM, agenda profesional, turnero telefónico, recordatorios locales e historia clínica. La HCE reúne consultas, evolución, antecedentes, cronología de intervenciones y trazabilidad de accesos y cambios.

La regresión completa del 22/11/2026 aprobó 204 pruebas. Scrum reúne las 23 historias y los 10 sprints, con responsables y evidencias por tarea. Alejandro coordina como Scrum Master.

El integrador FHIR cuenta con importación de los archivos de Lautaro, reimportación sin duplicados y comprobante del correo enviado. El [ejemplo híbrido](intercambio/hibrido/FHIR_44895843_hibrido_Equipo2.json) conserva los recursos recibidos de Bart Simpson y agrega una solicitud de práctica sintética del Equipo 2. Su procedencia y los dos escenarios de importación están documentados en [intercambio/hibrido/README.txt](intercambio/hibrido/README.txt) y [la verificación](evidencias/integrador-fhir/verificacion_hibrido.json). La impresión del reporte HTML de la entrega 5 está acreditada con PDF y captura del diálogo de impresión.

El detalle de las comprobaciones está en [docs/verificacion.md](docs/verificacion.md). Los apartados de incrementos anteriores describen su evolución. Turnos, HCE, seguridad e interoperabilidad forman parte de la versión actual.

## Turnero web — Ampliación opcional de la entrega final

Portal de pacientes con clave individual: disponibilidad por especialidad/profesional/fecha, reserva, confirmación, reprogramación y cancelación. Comparte horarios y auditoría con el turnero telefónico; cada paciente accede únicamente a sus propios turnos. El personal habilita o revoca las claves desde **Turnos → Habilitar / renovar acceso web**. **204 pruebas aprobadas, ninguna omitida** (202 de regresión completa y dos adicionales del escritorio).

```powershell
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe turnero_web.py
```

Abrir [http://127.0.0.1:5000](http://127.0.0.1:5000). Funciona localmente en esta computadora. Instrucciones, permisos, migración y alcance en [docs/turnero-web.txt](docs/turnero-web.txt). Capturas y prueba real del navegador en `evidencias/turnero-web/`, realizadas sobre una copia ficticia de la base. La [planilla Scrum revisada](scrum/Planilla%20Scrum.xlsx) reúne la revisión por entrega y las evidencias de turnero y HCE.

## Referencia histórica — Entrega 10 / Cierre técnico del Epic 2

Visor DICOM con metadatos completos y vista previa de imágenes sin comprimir; conversión con datos de pacientes/profesionales. FHIR incorpora análisis sin escritura, revisión de acciones y confirmación explícita antes de importar, con agrupación de mediciones. **142 pruebas aprobadas, ninguna omitida.**

```powershell
python -m pip install -r requirements.txt
python OpenHIS_app.pyw
```

Se conservan las cuentas de demostración y los permisos descritos abajo. El menú integra las versiones actuales; `_Herramientas_DICOM_Visor.pyw` abre las tres pestañas DICOM con login. En FHIR: analizar archivo, revisar JSON y acciones, confirmar e importar. Cancelar no modifica la base; los cambios del archivo o de los datos relevantes exigen repetir el análisis.

Imagen sintética y DICOM en `IMAGENES/RX/`; entrada FHIR en `intercambio/e10_recibido_sintetico.json`. Cuatro capturas y verificaciones de archivos intactos en `evidencias/entrega10/`, también embebidas en Scrum. El visor es básico y la anonimización requiere revisar identificadores en los píxeles.

Alcance y verificación del incremento en [Entrega 10](docs/entrega-10.md), con [su reflexión](docs/reflexion-entrega-10.md). Turnos e HCE se implementaron en la entrega final. La revisión documental, los comprobantes y el ejemplo híbrido se encuentran en la rama de trabajo `develop-revisionFinal`.

## Referencia histórica — Entrega 9 / Sprint 5

Consulta consolidada y auditada de intervenciones, intercambio FHIR R4 JSON/XML con importación efectiva y herramientas DICOM de conversión/anonimización básica. **121 pruebas aprobadas, ninguna omitida.**

```powershell
python -m pip install -r requirements.txt
python OpenHIS_app.pyw
```

Cuentas ficticias de demostración: `admin / admin123`, `medico_equipo2 / medico123`, `enfermero_equipo2 / enfermero123`, `administrativo_equipo2 / administrativo123`. Intervenciones y DICOM admiten admin/médico/enfermero; FHIR es de administrador. Todos los accesos independientes piden login.

Entradas: `_Consulta_intervenciones.pyw`, `_Interoperabilidad_FHIR.pyw`, `_Herramientas_Dicom.pyw`. El menú principal también las integra. La importación reutiliza DNI activos/inactivos y conserva registros locales; el mismo recurso externo no se duplica al repetir el archivo. Auditoría Q/E/I/C y autor de los registros recibidos.

Archivos de intercambio en `intercambio/`. Capturas, imagen sintética, DICOM y verificación de metadatos en `evidencias/entrega9/`; las cuatro capturas están embebidas en Scrum. La anonimización conserva solo años/sexo y atributos técnicos; requiere revisar datos incrustados en los píxeles. El perfil FHIR soportado y las limitaciones están en [docs/entrega-9.md](docs/entrega-9.md).

## Referencia histórica — Entrega 7 / Sprint 4

El sistema ahora exige login, limita los módulos por rol y registra autoría y auditoría. Ejecutar `python OpenHIS_app.pyw` o `python Menu_principal_app.pyw`.

La base incluida tiene cuentas ficticias de demostración: `admin / admin123`, `medico_equipo2 / medico123`, `enfermero_equipo2 / enfermero123` y `administrativo_equipo2 / administrativo123`. En una base nueva se crea el administrador desde la pantalla inicial. Las entradas independientes y la consola también piden credenciales.

El administrador gestiona usuarios, contraseñas, roles y estados. Las tres tablas maestras admiten alta, modificación y baja lógica con auditoría. No puede desactivarse ni degradarse al último administrador activo. Cada alta identifica a su autor; el log conserva cambios y accesos. Los registros históricos mantienen autor desconocido. Contraseñas con PBKDF2-HMAC-SHA256 y sal, sin texto legible ni hashes en auditoría.

Entrega 7 verificada con **96 pruebas aprobadas, ninguna omitida**. Tres usuarios nuevos de distintos roles, dos capturas reales embebidas en Scrum y reflexión completada. La consigna renumera seguridad como HU-07 y FHIR como HU-09. FHIR se incorporó en las entregas 9 y 10.

Matriz de requisitos, permisos, cuentas y límites en [docs/entrega-7.md](docs/entrega-7.md). Reflexión en [docs/reflexion-entrega-7.md](docs/reflexion-entrega-7.md).

## Referencia del incremento anterior — Entrega 5

Sistema hospitalario educativo desarrollado por Alejandro y Leonel con Python, Tkinter y SQLite. Entrega 5 amplía el Sprint 3: pacientes, profesionales, signos vitales independientes y prescripciones con bajas reversibles, XML académico y HTML imprimible.

## Ejecución

Requiere Python 3.10 o posterior con Tkinter y las dependencias de `requirements.txt`.

```powershell
python -m pip install -r requirements.txt
python OpenHIS_app.pyw
```

El menú muestra los módulos habilitados para el rol autenticado, incluidos Agenda profesional, Turnos, Agenda y recordatorios e Historia clínica. Todos comparten `BD/Salud.db`, ubicada respecto de la raíz del proyecto. En Windows se puede abrir un `.pyw` con doble clic si Python tiene esa extensión asociada.

Los cuatro módulos también funcionan como ejecutables independientes:

```powershell
python Pacientes_def_app.pyw
python Profesionales_def_app.pyw
python Signos_vitales_def_app.pyw
python Prescripciones_def_app.pyw
```

Se conservan `Pacientes.py` (consola), `Pacientes_app.py`, `Pacientes2_app.pyw`, `Pacientes2b_app.pyw`, `Tablas_maestras_app.pyw`, `Profesionales_app.pyw` y `Prescripcion_app.pyw`. Las versiones anteriores usan las mismas reglas de datos; sus bajas ya son lógicas. `Pacientes2b_app.pyw` conserva su acceso integrado a signos.

## Uso

1. **Pacientes:** registrar datos personales; el sistema genera la HC. Buscar por DNI, seleccionar la ficha y modificar contacto. Dar de baja conserva el registro y sus intervenciones; Reactivar recupera la misma HC.
2. **Profesionales:** registrar DNI, matrícula y especialidad activa. Modificar contacto o especialidad. La baja informa cuántas intervenciones conservará. La matrícula debe ser única; no se comprueba su vigencia en un registro oficial.
3. **Signos vitales:** seleccionar paciente y profesional activos, completar motivo y mediciones, y guardar. Buscar historial por DNI incluye todos sus registros, activos y anulados. Ver detalle muestra los estados de las fichas relacionadas. Anular y Reactivar cambian solamente el signo seleccionado.
4. **Prescripciones:** seleccionar paciente, profesional y fármaco activos; diagnóstico opcional. Completar dosis, vía y frecuencia. Buscar por DNI, ver detalle, anular o reactivar. No se editan mediciones ni prescripciones ya guardadas.
5. **Exportar:** desde el detalle de una prescripción, generar XML o HTML. El XML se muestra en una vista previa; el HTML puede abrirse en el navegador e imprimirse con Ctrl+P. Si Windows pregunta con qué aplicación abrirlo, elegir un navegador. Los archivos se guardan en `recetas/` y `reportes/` con nombres únicos; los errores de escritura no eliminan la prescripción.
6. **Filtros:** Ver activos, Ver inactivos/anulados y Ver todos cambian los listados. Buscar por DNI encuentra fichas de ambos estados. Los documentos históricos pueden exportarse y muestran el estado que tenían al generarse.

Las bajas y reactivaciones son manuales, **sin cascada**. Reactivar una intervención histórica no reactiva sus fichas relacionadas. Registrar intervenciones nuevas exige que ambas fichas estén activas, incluso si su estado cambia mientras el formulario está abierto. DNI y matrícula siguen siendo únicos entre activos e inactivos.

## Datos y arquitectura

Al cierre de la entrega 5, la base contenía seis pacientes, siete profesionales, cuatro signos y ocho prescripciones. Los incrementos posteriores incorporaron los recursos FHIR, turnos y registros de HCE de las demostraciones. Los registros de Entrega 5 —paciente 6, profesional 7, signo 4 y prescripción 8— quedaron inactivos; mantienen sus relaciones. Los datos y tratamientos son ficticios. `python cargar_demo.py` conserva los registros existentes, incluidos los anulados, sin duplicar su conjunto inicial.

`datos.py` concentra validaciones y consultas; `esquema.py` migra la base y crea índices. `interfaz.py`, `ventanas_clinicas.py`, `signos_app.py` y `menu_app.py` construyen las ventanas. `exportaciones.py` genera los documentos. Todos estos archivos son necesarios al copiar el proyecto.

La migración agrega `activo` donde falte y no reactiva registros anulados. Antes de actualizar una instalación, cerrar la aplicación y respaldar `BD/Salud.db`. Para esta entrega se respaldaron la base y la planilla originales en `.trabajo-local/entrega5/`, fuera de Git.

El DNI admite números sin separadores. Nombre, apellido, nacimiento y sexo son obligatorios. Las fechas deben ser válidas; el nacimiento no puede ser futuro. El motivo de consulta es obligatorio; las mediciones vacías se guardan como NULL. No se aplican interpretaciones clínicas. El historial es completo y se ordena por fecha e ID descendentes; las fechas automáticas se identifican como UTC. Los signos históricos sin autor se conservan y pueden recibir su autor confirmado desde el acceso anterior.

La exportación XML de recetas usa `Prescription` y el espacio de nombres del ejemplo docente. El intercambio FHIR R4 JSON/XML se realiza desde el módulo FHIR de las entregas 9 y 10. Seguridad y auditoría se incorporaron en la entrega 7. Los documentos y datos son demostraciones académicas. La matrícula se valida como obligatoria y única; la verificación de su vigencia requiere un registro institucional.

## Pruebas sencillas

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q -rs
```

Resultado de Entrega 5: **66 pruebas aprobadas, ninguna omitida**. Usan bases y carpetas temporales. Cubren migración repetida, conservación, ciclos de estado, filtros, unicidad, validaciones, XML/HTML y formularios reales. Los tests de GUI requieren Tkinter (`python -m tkinter`); una omisión por falta de Tk no cuenta como aprobación. Se comparte una raíz Tk durante la sesión de pruebas para evitar la carga repetida que provocaba intermitencias.

## Ramas y documentación

Las ramas `develop-Entrega1` a `develop-Entrega5` son acumulativas. Cada entrega se verifica y se integra localmente a `develop` antes de iniciar la siguiente. No se realiza push automático.

Consultar `docs/entrega-5.md`, `docs/verificacion.md`, `docs/reflexion-entrega-5.md` y `PLAN_PROYECTO.md`. Scrum conserva las cuatro capturas de Entrega 4 y agrega ocho capturas de altas/bajas, la vista previa XML y una revisión estática del HTML. El 22/11/2026 se acreditó la impresión desde navegador con un PDF de dos páginas A4 y la captura del diálogo de impresión en `evidencias/entrega5/`, incorporada a la Bitácora desde la fila 1480.

El equipo está integrado por Alejandro, Scrum Master y desarrollador, y Leonel, desarrollador. Ambos comparten implementación, documentación y pruebas. María Susana Burioni figura como Product Owner. Las fechas y estados heredados de Scrum se conservaron; no acreditan avance por sí solos. Los documentos de entregas anteriores describen su estado histórico.
