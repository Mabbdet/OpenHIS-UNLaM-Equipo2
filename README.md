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

## Entrega 2 — ejecución

Requiere Python 3.10 o posterior. La aplicación usa solamente la biblioteca estándar.

```powershell
python cargar_demo.py
python Pacientes.py
```

`BD/Salud.db` incluye cinco pacientes ficticios. `cargar_demo.py` omite los DNI existentes y no reemplaza datos. El menú permite registrar, buscar por DNI y salir. La HC es el identificador único de SQLite.

`datos.py` es un módulo auxiliar necesario: debe entregarse junto con `Pacientes.py`. La base se ubica respecto de los archivos del proyecto, independientemente de la carpeta desde la que se ejecute el programa.

## Pruebas sencillas

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Las pruebas usan bases temporales de pytest: alta/búsqueda, DNI duplicado, búsqueda inexistente, campos obligatorios, persistencia e identificadores únicos. No modifican `BD/Salud.db`.

## Validaciones

DNI numérico sin separadores; nombre, apellido, fecha de nacimiento y sexo obligatorios. Fecha válida con formato AAAA-MM-DD, no futura; sexo M/F según la guía. Contacto, domicilio y obra social son opcionales conforme al esquema. La validación de formato de fecha y DNI es una decisión de implementación.

## Documentación y evidencias

Consultar `docs/entrega-1-vision.md`, `PLAN_PROYECTO.md` y `docs/reflexion-sprint-1.md`. Las capturas académicas de alta, búsqueda y duplicado y su incorporación a la Bitácora siguen pendientes; las pruebas automatizadas no las sustituyen.

Los PDFs originales, integrantes/roles propios, formato y fecha final de entrega no están confirmados. La visión es un borrador basado en la guía y en la planilla aportada; los estados de la plantilla no se usan como prueba de avance.
