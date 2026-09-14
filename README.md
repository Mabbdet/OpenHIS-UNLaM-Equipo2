# OpenHIS-UNLaM — Equipo 2

Sistema de información hospitalaria educativo. Alcance actual: Epic 1, HU-01, HU-02 y HU-03.

## Ramas por entrega

Las ramas son acumulativas y locales. Cada incremento se verifica, se integra a `develop` y recién entonces se crea la siguiente rama desde `develop`. No se publica automáticamente en el remoto.

| Rama | Incremento |
|---|---|
| `develop` | Integra las entregas verificadas. |
| `develop-Entrega1` | Documento de Visión y plan de proyecto. |
| `develop-Entrega2` | Consola para HU-01/HU-02, SQLite y pruebas simples con pytest. |
| `develop-Entrega3` | Versiones gráficas, CRUD completo, HU-03 e historial. |

## Ejecución

Requiere Python 3.10 o posterior. La aplicación usa solamente la biblioteca estándar.

```powershell
python cargar_demo.py
python Pacientes.py
python Pacientes_app.py
python Pacientes2_app.pyw
python Pacientes2b_app.pyw
```

Ejecutar una aplicación por vez. `Pacientes.py` conserva la consola; `Pacientes_app.py` permite alta, búsqueda y listado; `Pacientes2_app.pyw` agrega modificación y baja; `Pacientes2b_app.pyw` agrega signos vitales e historial. Esta última es la aplicación final del Sprint 2. Con Python configurado en Windows, la extensión `.pyw` permite abrirla sin consola.

`BD/Salud.db` incluye cinco pacientes ficticios y signos en tres de ellos. `cargar_demo.py` no reemplaza fichas existentes; completa signos únicamente para fichas que coinciden con sus datos de demostración y no tienen historial. Puede repetirse sin duplicar registros. La HC es el identificador único de SQLite.

`datos.py` e `interfaz.py` son módulos auxiliares necesarios y deben incluirse en el paquete. La base se ubica respecto de los archivos del proyecto, independientemente de la carpeta desde la que se ejecute el programa. La GUI requiere Tkinter; para comprobar el entorno: `python -m tkinter`.

## Uso de la interfaz final

1. Registrar: completar los campos obligatorios y guardar. Se muestra la HC generada.
2. Buscar: ingresar DNI; el resultado queda seleccionado y su ficha aparece debajo del listado. Ver todos restaura el listado completo.
3. Modificar: seleccionar un paciente y editar teléfono, email, domicilio u obra social.
4. Signos: seleccionar un paciente y pulsar Signos, o hacer doble clic en su fila. Ingresar mediciones y motivo, y guardar; el historial se actualiza.
5. Eliminar: seleccionar y confirmar la baja. Se eliminan físicamente el paciente y sus signos en una misma transacción.

## Pruebas sencillas

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Las pruebas usan bases temporales de pytest: alta/búsqueda, DNI duplicado, búsqueda inexistente, campos obligatorios, persistencia, modificación, signos, historial y eliminación conjunta. También se comprueba carga y búsqueda en las tres variantes de la GUI. No modifican `BD/Salud.db`. Los tests de GUI se omiten explícitamente si el entorno no dispone de Tk; los tests de datos siguen ejecutándose.

## Validaciones

DNI numérico sin separadores; nombre, apellido, fecha de nacimiento y sexo obligatorios. Fecha válida con formato AAAA-MM-DD, no futura; sexo M/F según la guía. Contacto, domicilio y obra social son opcionales conforme al esquema. La validación de formato de fecha y DNI es una decisión de implementación.

En signos vitales, el motivo es obligatorio; las mediciones pueden dejarse vacías y se guardan como NULL. Presiones, frecuencia y saturación admiten enteros; temperatura admite decimales con punto o coma y rechaza valores no finitos. No se agregan umbrales ni interpretaciones clínicas. El historial presenta los diez últimos registros; en igualdad de fecha/hora se ordena por ID descendente. Las fechas automáticas de SQLite se muestran identificadas como UTC.

`medico_id` queda preparado y sin asignar: la planilla ubica la integración con profesionales en Sprint 3. No se presenta como cumplido ese criterio original de HU-03 en esta versión. Tampoco se implementan profesionales, prescripción, FHIR, turnos ni SMS.

## Documentación y evidencias

Consultar `docs/entrega-1-vision.md`, `PLAN_PROYECTO.md`, `docs/reflexion-sprint-1.md` y `docs/reflexion-sprint-2.md`. Las capturas académicas de alta, búsqueda, duplicado, signos, modificación y eliminación, y su incorporación a la Bitácora siguen pendientes; las pruebas automatizadas no las sustituyen. La integración en `develop` representa el incremento de código verificado y no certifica que la presentación académica esté completa.

Los PDFs originales, integrantes/roles propios, formato y fecha final de entrega no están confirmados. La visión es un borrador basado en la guía y en la planilla aportada; los estados de la plantilla no se usan como prueba de avance.
