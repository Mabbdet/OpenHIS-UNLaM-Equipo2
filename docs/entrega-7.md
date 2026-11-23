# Entrega 7 — Sprint 4 / HU-07

Fuente: `Sist-Info-Salud-7.pdf`, proporcionado por el usuario. Requisitos y permisos en páginas 4–10, esquema de auditoría en páginas 37–44 y evidencias en páginas 175–176. Desarrollo en `develop-Entrega7`, desde `develop` en `5bea6ef`. Equipo: Alejandro y Leonel. Scrum Master: Alejandro.

## Alcance

Esta entrega incorpora seguridad a los módulos existentes. La consigna cambia la numeración: HU-07 corresponde a identificación, roles y autoría; FHIR pasa a HU-09. Sprint 4 implementa HU-07. Sprint 5 reúne HU-08 y HU-09.

Los PDFs de semanas 9, 10 y 13, la práctica FHIR y el ZIP de Semana 13 se revisaron para separar las etapas posteriores. Consulta consolidada de intervenciones, intercambio FHIR, DICOM, agenda, turnos y HCE no se incorporan a esta entrega. Arduino e IA en imágenes son trabajos ya realizados por el equipo. La rúbrica corresponde a la presentación oral.

## Matriz de cumplimiento

| Requisito | Implementación | Verificación |
|---|---|---|
| Login obligatorio | `LoginApp`, `Seguridad.autenticar`; entradas antiguas y consola también piden credenciales | Login válido, incorrecto, cuenta inactiva y sesión falsa |
| Contraseñas con hash SHA-256 | PBKDF2-HMAC-SHA256, sal aleatoria de 16 bytes, 600.000 iteraciones, comparación constante | Igual contraseña produce hashes distintos; la contraseña incorrecta falla |
| Compatibilidad con ejemplos docentes | Acepta SHA-256 simple existente y lo convierte al iniciar sesión correctamente | Prueba de migración de hash heredado |
| Roles y menú limitado | Admin, médico, enfermero y administrativo; autorización en menú y operaciones | Los cuatro roles y sus accesos directos |
| Gestión de usuarios | Alta, listado, modificación de nombre/contacto/rol, cambio de contraseña, baja y reactivación | Formulario real y pruebas de validación, duplicados y estados |
| Protección del último admin | No permite desactivarlo ni quitarle el rol de admin activo | Comprobación dentro de una transacción de escritura |
| Último acceso | `Usuarios.ultimo_acceso` en UTC | Se actualiza al autenticar |
| Sesiones y logout | Tokens aleatorios en memoria; logout invalida el token y cierra las ventanas dependientes | Rechazo de operaciones después del cierre; auditoría L/X |
| Revocación | Cambio de contraseña y estado invalidan sesiones, también entre instancias | Versión de sesión persistida; rol consultado en cada operación |
| Autor de altas | `usuario_alta_id` en las tablas de datos y usuarios | El ID corresponde al usuario autenticado; históricos quedan NULL |
| Auditoría | A/M/B/R en datos y usuarios; L/X en sesiones; E en XML/HTML | Autor, tabla, ID, fecha, valores anteriores/nuevos y referencia al archivo |
| Tres tablas maestras | Alta, modificación y baja lógica de especialidades, SNOMED CT local y fármacos, según la ampliación de Semana 7 | Formularios y log A/M/B para las tres tablas; relaciones existentes conservadas |
| Atomicidad | Cambio de datos y auditoría en la misma transacción SQLite | Un fallo simulado del log revierte el alta; una exportación sin log se retira |
| Tres usuarios nuevos de distintos roles | Médico, enfermero y administrativo en la base entregada | Captura `evidencias/entrega7/01_usuarios.jpg` |
| Captura del log tras interacciones | Visor de auditoría con filtros y detalle | Captura `evidencias/entrega7/02_auditoria.jpg` |
| Scrum y reflexión | Sprint 4/HU-07 actualizados, evidencias embebidas y reflexión de dos párrafos | `scrum/Planilla Scrum.xlsx` y `docs/reflexion-entrega-7.md` |

Los tipos I/C se admiten en el esquema docente para futuras importaciones y conflictos; no se generan importaciones simuladas para dar por realizada HU-09.

## Permisos de los módulos disponibles

| Módulo | admin | medico | enfermero | administrativo |
|---|---|---|---|---|
| Pacientes | Sí | Sí | Sí | Sí |
| Profesionales | Sí | No | No | Sí |
| Signos vitales | Sí | Sí | Sí | No |
| Prescripciones y sus exportaciones | Sí | Sí | No | No |
| Tablas maestras | Sí | No | No | No |
| Usuarios y auditoría | Sí | No | No | No |

Los listados de profesionales y catálogos también sirven como datos de referencia de los formularios clínicos. Ese acceso no autoriza modificar esas tablas. Las entregas 9 y 10 incorporaron el módulo FHIR, con acceso de administrador. La exportación de recetas académicas XML/HTML mantiene los permisos de Prescripciones.

## Uso y cuentas de demostración

```powershell
python OpenHIS_app.pyw
```

`Menu_principal_app.pyw` es una entrada equivalente. `Usuarios_app.pyw` inicia la gestión de usuarios y solicita login de administrador. Los accesos independientes existentes mantienen su módulo y requieren login. `Pacientes.py` solicita credenciales por consola y oculta la contraseña con `getpass`.

| Usuario | Contraseña de demostración | Rol |
|---|---|---|
| admin | admin123 | admin |
| medico_equipo2 | medico123 | medico |
| enfermero_equipo2 | enfermero123 | enfermero |
| administrativo_equipo2 | administrativo123 | administrativo |

Son cuentas ficticias para reproducir el práctico. En una base nueva no se instalan contraseñas predeterminadas: la pantalla inicial permite crear un único administrador. Luego ese administrador crea las otras cuentas. Las contraseñas nunca se muestran en listados ni se incluyen en auditoría.

## Base entregada y evidencias

La migración conserva los 6 pacientes, 7 profesionales, 4 signos y 8 prescripciones de Entrega 5, incluidos sus estados. No se atribuyen autores históricos desconocidos. Se agregaron las tablas Usuarios y Auditoria y los campos de autoría. La especialidad ficticia `E7-SEG` permite demostrar A/M/B; su estado final es inactivo y no tiene relaciones clínicas.

Las capturas provienen de las pantallas reales de Usuarios y Auditoría, conectadas a `BD/Salud.db`. Registran tres altas de usuarios, cambios en el catálogo ficticio y accesos de los distintos roles. Las marcas de tiempo de la base son UTC; el trabajo y la documentación se fechan el 20/11/2026 en Argentina.

En el cierre de la entrega 7, Scrum conservó las 14 imágenes anteriores y agregó dos capturas desde la fila 480 de Bitácora. HU-07 y Sprint 4 documentan seguridad. HU-09/FHIR se implementó después, en Sprint 5. La revisión final concilió las fórmulas y la numeración de las 23 historias y los 10 sprints.

## Verificación y límites

Resultado: **96 pruebas aprobadas, ninguna omitida**, incluidas las 66 pruebas anteriores adaptadas al ingreso autenticado del menú. Comando:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -rs -p no:cacheprovider
```

Se inspeccionaron visualmente las pantallas de Usuarios y Auditoría y las evidencias de Scrum. La base pasa `PRAGMA integrity_check` y `PRAGMA foreign_key_check`. Los respaldos anteriores a la migración y de Scrum se conservan en `.trabajo-local/entrega7/`, fuera de Git.

La autorización protege las entradas de la aplicación y el servicio que usan las ventanas. `Repositorio` sigue siendo una API interna para migraciones, pruebas y mantenimiento; quien tenga acceso directo de escritura al archivo SQLite puede modificarlo fuera de esos controles. El log no es inmutable ni constituye una auditoría certificada. No se agregan autenticación de red, cifrado del archivo, bloqueo por intentos, perfiles clínicos vinculados a matrículas ni interoperabilidad FHIR real en esta etapa.

El hash iterado con sal reemplaza el SHA-256 simple del ejemplo para evitar guardar hashes idénticos para contraseñas iguales. El contrato de login y los roles docentes se conservan. Las sesiones se comparten en memoria entre ventanas del mismo proceso; no se guardan credenciales ni un archivo editable de sesión.
