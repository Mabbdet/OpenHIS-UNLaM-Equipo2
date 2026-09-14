# Guía de trabajo — Entrega 1 y Entrega 2
## Informática Biomédica y Tecnologías de la Salud — OpenHIS-UNLaM

Este documento sirve como **guía de análisis y ejecución** para continuar el trabajo posteriormente en un chat de **ChatGPT Work**.

La base del trabajo son dos PDFs:

- **Entrega 1:** `Sist-Info-Salud-1_1.pdf`
- **Entrega 2:** `Sist-Info-Salud-2_3.pdf`

La prioridad es respetar lo que indican los documentos. Cuando un requisito no esté expresamente definido, debe marcarse como **no especificado** o **inferencia**, evitando inventar condiciones de entrega.

---

# 1. Objetivo general del proyecto

El proyecto de la materia es:

**OpenHIS-UNLaM — Sistema de Información Hospitalaria Educativo**

Se plantea como un desarrollo incremental de un HIS para el ficticio **Hospital Universitario San Justo**.

El objetivo no es desarrollar un HIS completo desde el comienzo, sino construir un MVP progresivamente mediante Sprints y aplicar conceptos de:

- Informática Biomédica.
- Ingeniería de Software.
- Bases de datos.
- SCRUM.
- Interoperabilidad.
- Historia Clínica Electrónica.
- SNOMED CT.
- HL7 FHIR.
- DICOM.
- Tecnologías específicas de salud.

---

# 2. Regla principal para trabajar las entregas

Antes de implementar cualquier cosa:

1. Leer completamente el PDF correspondiente.
2. Separar:
   - requisitos explícitos;
   - requisitos sugeridos;
   - ejemplos;
   - conceptos teóricos;
   - entregables;
   - evidencias;
   - requisitos no especificados.
3. No transformar ejemplos en requisitos obligatorios salvo que la consigna lo indique.
4. No agregar tecnologías o funcionalidades por cuenta propia sin marcarlas como opcionales.
5. Mantener trazabilidad entre:
   - Epic;
   - Historia de Usuario;
   - criterio de aceptación;
   - implementación;
   - prueba;
   - evidencia.
6. Cada funcionalidad debe poder probarse contra sus criterios de aceptación.

---

# 3. ENTREGA 1 — Primer PDF

## 3.1. Naturaleza de la Entrega 1

El primer PDF define principalmente:

- contexto institucional;
- problema del hospital;
- visión general del producto;
- flujo de información;
- arquitectura conceptual;
- capas de Informática Biomédica;
- Product Backlog preliminar;
- Epics;
- Historias de Usuario;
- organización por Sprints.

También incluye una sección explícita llamada:

**TRABAJO PRELIMINAR — Documento de Visión del Proyecto**

Por lo tanto, la Entrega 1 debe analizarse principalmente como una **entrega conceptual/documental previa al desarrollo**.

El PDF no indica con precisión:

- plataforma de entrega;
- formato final obligatorio;
- extensión máxima;
- plantilla;
- nombre obligatorio de archivo;
- fecha límite;
- si debe entregarse como PDF, Word, Excel o repositorio.

Estos puntos deben mantenerse como **no especificados** hasta tener una consigna externa.

---

# 4. Entrega 1 — Documento de Visión

## 4.1. Qué debe explicar

El Documento de Visión debería describir de manera ordenada el sistema que se pretende construir.

### 4.1.1. Nombre del proyecto

**OpenHIS-UNLaM**

Sistema de Información Hospitalaria Educativo.

---

## 4.2. Institución

**Hospital Universitario San Justo**

Institución ficticia utilizada como caso de estudio.

Debe describirse brevemente:

- hospital universitario;
- institución de mediana complejidad;
- atención a alumnos y familias;
- actividad asistencial;
- actividad docente;
- investigación.

Servicios mencionados en el PDF:

- Guardia Médica.
- Consultorios Externos.
- Diagnóstico por Imágenes.
- Laboratorio.
- Farmacia Hospitalaria.
- Quirófanos.
- Internación General.
- Unidad de Terapia Intensiva.
- Enfermería.

---

# 5. Problema a resolver

El hospital posee sistemas informáticos desarrollados por distintos proveedores y en distintos momentos.

Actualmente existen aplicaciones independientes para:

- admisión;
- laboratorio;
- imágenes;
- farmacia;
- facturación;
- turnos;
- internación.

La falta de interoperabilidad produce:

- pacientes duplicados;
- historias clínicas incompletas;
- errores de identificación;
- demoras para acceder a antecedentes;
- demoras para acceder a resultados;
- imposibilidad de explotar datos integrados;
- dificultades para análisis;
- limitaciones para futuras aplicaciones de IA.

---

# 6. Objetivo del producto

Construir progresivamente un Sistema de Información Hospitalaria integrado que permita centralizar procesos administrativos y clínicos.

El sistema debe evolucionar hacia un ecosistema capaz de incorporar estándares internacionales de interoperabilidad.

---

# 7. Flujo principal del sistema

El primer PDF propone como hilo conductor:

```text
PERSONA
   ↓
ADMISIÓN
   ↓
PACIENTE
   ↓
TURNO
   ↓
PROFESIONAL
   ↓
ATENCIÓN
   ↓
HISTORIA CLÍNICA
   ↓
DIAGNÓSTICO
   ↓
TRATAMIENTO
   ↓
ESTUDIOS
   ↓
RESULTADOS
   ↓
FACTURACIÓN
```

Este flujo debe utilizarse como referencia para comprender cómo se relacionan los módulos.

---

# 8. Capas de Informática Biomédica

## 8.1. Capa 1 — Gestión Administrativa

Incluye:

- pacientes;
- profesionales;
- especialidades;
- turnos;
- admisión;
- obras sociales/prepagas;
- prestaciones;
- facturación.

---

## 8.2. Capa 2 — Clínica Asistencial

Incluye:

- consulta;
- antecedentes;
- alergias;
- vacunas;
- problemas de salud;
- signos vitales;
- diagnóstico;
- procedimientos;
- indicaciones;
- medicamentos;
- evolución.

---

## 8.3. Capa 3 — Interoperabilidad

Incluye:

- SNOMED CT;
- HL7;
- FHIR;
- identificadores;
- terminologías;
- recursos clínicos;
- intercambio de información.

Idea principal:

**FHIR funciona como un lenguaje común para que diferentes sistemas de salud intercambien información estructurada.**

Ejemplos conceptuales planteados:

```text
Patient          → Paciente
Practitioner     → Profesional
Encounter        → Atención
Observation      → Mediciones
Condition        → Problemas de salud
DiagnosticReport → Informes diagnósticos
```

---

## 8.4. Capa 4 — Tecnologías específicas de salud

Incluye:

- diagnóstico por imágenes;
- DICOM;
- PACS;
- laboratorio;
- dispositivos biomédicos;
- IoT;
- Inteligencia Artificial.

---

# 9. Product Backlog preliminar

El PDF organiza el proyecto inicialmente en ocho Epics.

## Epic 1 — Gestión de Pacientes

Historias inicialmente definidas:

- HU-01 — Registro de paciente.
- HU-02 — Búsqueda de paciente.
- HU-03 — Registro de signos vitales.

---

## Epic 2 — Gestión de Profesionales

Historias inicialmente definidas:

- HU-04.
- HU-05.
- HU-06.

---

## Epic 3 — Gestión de Turnos

Historias inicialmente definidas:

- HU-07.
- HU-08.
- HU-09.

---

## Epic 4 — Seguridad y Autenticación

El documento indica:

**HACER HHUU**

Por lo tanto, las Historias de Usuario todavía deben definirse.

---

## Epic 5 — Historia Clínica Electrónica

El documento indica:

**HACER HHUU**

---

## Epic 6 — Gestión de Imágenes Médicas / DICOM

El documento indica:

**HACER HHUU**

---

## Epic 7 — Interoperabilidad / HL7 / SNOMED

El documento indica:

**HACER HHUU**

---

## Epic 8 — Inteligencia Artificial

El documento indica:

**HACER HHUU**

---

# 10. Entrega 1 — Propuesta de documento a construir

Salvo que exista otra consigna de la cátedra, estructurar el Documento de Visión de esta forma:

```text
1. Portada
2. Integrantes del grupo
3. Roles SCRUM iniciales
4. Nombre del producto
5. Descripción del Hospital Universitario San Justo
6. Situación actual
7. Problema a resolver
8. Objetivo general
9. Alcance
10. Actores
11. Flujo general del sistema
12. Capas de Informática Biomédica
13. Módulos previstos
14. Product Backlog
15. Epics
16. Historias de Usuario conocidas
17. Historias de Usuario pendientes
18. Organización preliminar en Sprints
19. Riesgos / supuestos
20. Conclusión
```

---

# 11. Entrega 1 — Alcance

## Incluir

- visión del producto;
- problema institucional;
- alcance conceptual;
- actores;
- módulos;
- flujo principal;
- Epics;
- Historias de Usuario;
- criterios de aceptación disponibles;
- Sprints iniciales;
- roles del equipo.

## No asumir como obligatorio

- frontend terminado;
- backend terminado;
- base de datos final;
- APIs;
- FHIR implementado;
- SNOMED completo;
- DICOM completo;
- IA;
- internación completa;
- facturación completa.

---

# 12. ENTREGA 2 — Segundo PDF

La Entrega 2 convierte el proyecto conceptual en una práctica concreta.

El PDF la presenta como:

**GUÍA DE CLASE SPRINT 1: MÓDULO DE PACIENTES**

Objetivos principales:

1. Comprender CRUD.
2. Configurar entorno de desarrollo.
3. Crear la tabla `Pacientes`.
4. Implementar CREATE.
5. Implementar READ.
6. Validar DNI duplicado.

---

# 13. Stack definido para Entrega 2

La Entrega 2 sí define concretamente las tecnologías:

- Python.
- SQLite.
- DB Browser for SQLite.
- Visual Studio Code.

También recomienda extensiones de VS Code, pero deben diferenciarse de los requisitos funcionales.

---

# 14. Estructura de proyecto esperada

```text
OpenHIS-UNLaM/
│
├── Pacientes.py
│
└── BD/
    └── Salud.db
```

---

# 15. Base de datos

Crear:

```text
OpenHIS-UNLaM/BD/Salud.db
```

Tabla requerida:

```sql
CREATE TABLE Pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dni TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    fecha_nacimiento TEXT NOT NULL,
    sexo TEXT NOT NULL,
    telefono TEXT,
    email TEXT,
    domicilio TEXT,
    obra_social TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

# 16. HU-01 — Registrar paciente

Historia de Usuario:

**Como administrativo, quiero registrar un nuevo paciente con sus datos personales para crear su ficha en el sistema.**

Criterios de aceptación:

- ingresar DNI;
- ingresar nombre;
- ingresar fecha de nacimiento;
- ingresar obra social;
- ingresar contacto;
- DNI no duplicado;
- generar número de Historia Clínica único.

La guía práctica amplía los datos utilizados:

- DNI;
- nombre;
- apellido;
- fecha de nacimiento;
- sexo;
- teléfono;
- email;
- domicilio;
- obra social.

---

# 17. HU-02 — Buscar paciente

Historia de Usuario:

**Como administrativo, quiero buscar un paciente por DNI para acceder rápidamente a su ficha.**

Criterios de aceptación:

- búsqueda por DNI;
- resultados en menos de 2 segundos;
- mostrar nombre completo;
- mostrar número de Historia Clínica;
- permitir acceder al detalle.

En la implementación de consola de la guía, el detalle se muestra directamente luego de encontrar al paciente.

---

# 18. Funcionalidades requeridas en `Pacientes.py`

El programa debe tener al menos:

```text
1. Registrar nuevo paciente
2. Buscar paciente por DNI
3. Salir
```

Funciones esperadas conceptualmente:

```python
conectar_bd()
registrar_paciente()
buscar_paciente()
menu()
```

No es necesario copiar literalmente el código de la guía si se mantiene el mismo comportamiento y los criterios de aceptación, salvo que el docente exija transcripción exacta.

---

# 19. Validación de DNI duplicado

Debe existir una protección a nivel de base de datos:

```sql
dni TEXT UNIQUE NOT NULL
```

Python debe manejar:

```python
sqlite3.IntegrityError
```

Resultado esperado:

```text
ERROR: Ya existe un paciente con ese DNI.
```

---

# 20. Historia Clínica

En esta primera versión:

```text
id
```

se utiliza como identificador / número de Historia Clínica.

Debe ser único y autoincremental.

---

# 21. Datos mínimos a cargar

`Salud.db` debe contener **al menos 5 pacientes registrados**.

Conviene usar datos ficticios para evitar exposición innecesaria de datos personales.

Ejemplo:

```text
Paciente 1
DNI: 40123456
Nombre: María
Apellido: González

Paciente 2
DNI: 41123456
Nombre: Juan
Apellido: Pérez

Paciente 3
DNI: 42123456
Nombre: Ana
Apellido: López

Paciente 4
DNI: 43123456
Nombre: Pedro
Apellido: Martínez

Paciente 5
DNI: 44123456
Nombre: Laura
Apellido: Fernández
```

Completar todos los campos necesarios.

---

# 22. Pruebas obligatorias

## Prueba 1 — Alta correcta

Registrar un paciente nuevo.

Resultado esperado:

```text
PACIENTE REGISTRADO CON ÉXITO
Número de Historia Clínica: X
```

Guardar captura.

---

## Prueba 2 — Búsqueda correcta

Buscar el paciente anterior por DNI.

Resultado esperado:

```text
PACIENTE ENCONTRADO
```

Mostrar los datos.

Guardar captura.

---

## Prueba 3 — DNI duplicado

Intentar registrar nuevamente el mismo DNI.

Resultado esperado:

```text
ERROR: Ya existe un paciente con ese DNI.
```

Guardar captura.

---

# 23. Evidencias de Entrega 2

La guía especifica explícitamente cuatro elementos.

## 23.1. Base de datos

```text
Salud.db
```

Debe contener al menos 5 pacientes.

---

## 23.2. Código

```text
Pacientes.py
```

Debe funcionar correctamente.

---

## 23.3. Planilla Scrum

Archivo:

```text
Planilla Scrum.xlsx
```

Pestaña:

```text
Bitácora
```

Debe contener capturas de:

1. registro exitoso;
2. búsqueda exitosa;
3. intento de registro duplicado.

---

## 23.4. Reflexión del equipo

Dos párrafos.

Responder:

1. ¿Qué problema del hospital resuelve este módulo?
2. ¿Cómo se relaciona con la interoperabilidad HL7 FHIR?

---

# 24. Reflexión — enfoque recomendado

## Párrafo 1 — Problema del hospital

Explicar que el módulo centraliza la identificación de pacientes y reduce:

- duplicación;
- fragmentación;
- errores de identidad;
- dificultad para localizar información.

Concepto central:

**un paciente debe poseer una identidad única dentro del sistema.**

---

## Párrafo 2 — Relación con interoperabilidad

Explicar que una identificación consistente del paciente es fundamental para intercambiar información clínica con otros sistemas.

FHIR representa al paciente mediante recursos estructurados, por ejemplo:

```text
Patient
```

Si la identidad está duplicada o inconsistente, los sistemas podrían interpretar que se trata de pacientes distintos y fragmentar la información clínica.

No afirmar que el Sprint 1 ya implementa FHIR: solamente prepara una base conceptual y de datos para una futura interoperabilidad.

---

# 25. Qué NO corresponde a Entrega 2

No implementar todavía como requisito del Sprint 1:

- HU-03;
- signos vitales;
- motivo de consulta;
- UPDATE;
- DELETE;
- profesionales;
- turnos;
- frontend web;
- SMS;
- FHIR real;
- SNOMED real;
- DICOM;
- PACS;
- IA;
- internación;
- facturación.

El segundo PDF anticipa que HU-03 llegará posteriormente.

---

# 26. Relación entre Entrega 1 y Entrega 2

La secuencia conceptual es:

```text
ENTREGA 1
Visión del sistema
        ↓
Problema institucional
        ↓
Product Backlog
        ↓
Epic 1
        ↓
HU-01 / HU-02
        ↓
ENTREGA 2
Sprint 1
        ↓
SQLite
        ↓
Pacientes
        ↓
CREATE + READ
        ↓
Pruebas
        ↓
Evidencias en Scrum
```

La Entrega 1 explica **qué sistema se quiere construir y por qué**.

La Entrega 2 comienza a construirlo.

---

# 27. Plan de trabajo recomendado

## Fase A — Analizar Entrega 1

1. Extraer requisitos del PDF.
2. Identificar contexto institucional.
3. Identificar problema.
4. Identificar actores.
5. Identificar módulos.
6. Identificar Epics.
7. Identificar Historias de Usuario.
8. Identificar criterios de aceptación.
9. Identificar Sprints.
10. Marcar puntos no especificados.

Resultado:

```text
Documento de Visión
+
Backlog preliminar
```

---

## Fase B — Preparar Entrega 2

1. Crear `OpenHIS-UNLaM`.
2. Crear `BD`.
3. Crear `Salud.db`.
4. Crear tabla `Pacientes`.
5. Verificar restricciones.
6. Crear `Pacientes.py`.
7. Implementar conexión.
8. Implementar HU-01.
9. Implementar HU-02.
10. Implementar menú.
11. Ejecutar pruebas.

---

## Fase C — Testing

Preparar una matriz:

| ID | Caso | Entrada | Resultado esperado | Resultado real | Estado |
|---|---|---|---|---|---|
| T01 | Alta válida | DNI nuevo | Registro exitoso | | |
| T02 | Búsqueda válida | DNI existente | Paciente encontrado | | |
| T03 | DNI duplicado | DNI existente | Error duplicado | | |
| T04 | Búsqueda inexistente | DNI inexistente | Paciente no encontrado | | |
| T05 | Persistencia | Reiniciar programa | Datos continúan | | |

Los tres primeros son los principales requeridos por la consigna.

---

# 28. Evidencias

Crear una carpeta auxiliar:

```text
evidencias/
│
├── 01_alta_exitosa.png
├── 02_busqueda_exitosa.png
└── 03_dni_duplicado.png
```

Después insertar esas imágenes en:

```text
Planilla Scrum.xlsx
→ Bitácora
```

---

# 29. Checklist — Entrega 1

```text
[ ] Leer completamente Sist-Info-Salud-1_1.pdf

[ ] Definir:
    [ ] Hospital
    [ ] problema actual
    [ ] objetivo
    [ ] actores
    [ ] flujo de información

[ ] Documentar las 4 capas

[ ] Documentar Product Backlog

[ ] Registrar:
    [ ] Epic 1
    [ ] Epic 2
    [ ] Epic 3
    [ ] Epic 4
    [ ] Epic 5
    [ ] Epic 6
    [ ] Epic 7
    [ ] Epic 8

[ ] Registrar HHUU existentes

[ ] Marcar HHUU todavía pendientes

[ ] Documentar organización inicial de Sprints

[ ] Documentar integrantes y roles SCRUM

[ ] No asumir formato/plataforma de entrega si no existe otra consigna
```

---

# 30. Checklist — Entrega 2

```text
[ ] Crear OpenHIS-UNLaM/

[ ] Crear OpenHIS-UNLaM/BD/

[ ] Crear BD/Salud.db

[ ] Crear tabla Pacientes

[ ] Verificar:
    [ ] id AUTOINCREMENT
    [ ] dni UNIQUE
    [ ] dni NOT NULL
    [ ] fecha_registro automática

[ ] Crear Pacientes.py

[ ] Implementar conexión SQLite

[ ] Implementar HU-01

[ ] Implementar HU-02

[ ] Implementar menú

[ ] Registrar mínimo 5 pacientes

[ ] Probar alta exitosa

[ ] Probar búsqueda exitosa

[ ] Probar DNI duplicado

[ ] Capturar las 3 evidencias

[ ] Colocar capturas en:
    Planilla Scrum.xlsx → Bitácora

[ ] Escribir reflexión de 2 párrafos

[ ] Verificar que Salud.db persista correctamente

[ ] Verificar que Pacientes.py funcione desde la carpeta raíz
```

---

# 31. Estructura recomendada del repositorio de trabajo

Aunque el PDF no exige explícitamente un repositorio Git remoto, esta estructura ayuda a mantener el proyecto organizado:

```text
OpenHIS-UNLaM/
│
├── README.md
│
├── Pacientes.py
│
├── BD/
│   └── Salud.db
│
├── docs/
│   ├── entrega-1-vision.md
│   └── reflexion-sprint-1.md
│
├── evidencias/
│   ├── 01_alta_exitosa.png
│   ├── 02_busqueda_exitosa.png
│   └── 03_dni_duplicado.png
│
└── scrum/
    └── Planilla Scrum.xlsx
```

Esta estructura es organizativa, no un requisito textual de los PDFs.

---

# 32. Prompt para continuar posteriormente en ChatGPT Work

Copiar este bloque en un nuevo chat de Work junto con los dos PDFs y, si existen, `Planilla Scrum.xlsx`, el código y la base de datos:

---

## PROMPT

Estoy trabajando en el proyecto **OpenHIS-UNLaM** de la materia Informática Biomédica y Tecnologías de la Salud.

Tengo dos consignas:

- `Sist-Info-Salud-1_1.pdf` = **Entrega 1**
- `Sist-Info-Salud-2_3.pdf` = **Entrega 2**

Quiero que trabajes tomando los PDFs como fuente principal y sin inventar requisitos que no estén presentes.

### Objetivo

Ayudarme a completar ambas entregas y verificar que todo cumpla con las consignas.

### Método de trabajo obligatorio

Primero:

1. Lee completamente ambos PDFs.
2. Extrae todos los requisitos.
3. Clasifícalos en:
   - obligatorio;
   - sugerido;
   - ejemplo;
   - opcional;
   - no especificado.
4. Compara Entrega 1 y Entrega 2.
5. Detecta si la Entrega 2 aclara o modifica algo de la Entrega 1.
6. Señala contradicciones o ambigüedades sin resolverlas arbitrariamente.

### Entrega 1

Analiza específicamente el **Trabajo Preliminar / Documento de Visión**.

Quiero construir un documento que incluya, cuando corresponda según la fuente:

- contexto del Hospital Universitario San Justo;
- problema actual;
- objetivo del producto;
- alcance;
- actores;
- flujo principal;
- cuatro capas de Informática Biomédica;
- módulos;
- Product Backlog;
- Epics;
- Historias de Usuario;
- criterios de aceptación;
- Sprints;
- roles SCRUM.

No agregues requisitos no presentes en la consigna.

Si consideras conveniente agregar una sección no obligatoria, márcala claramente como:

**Propuesta adicional — no exigida explícitamente por la consigna.**

### Entrega 2

Debemos resolver el **Sprint 1 — Módulo de Pacientes**.

Revisar y completar:

```text
OpenHIS-UNLaM/
├── Pacientes.py
└── BD/
    └── Salud.db
```

Debe verificarse:

#### HU-01

- alta de paciente;
- DNI;
- nombre;
- apellido;
- fecha de nacimiento;
- sexo;
- teléfono;
- email;
- domicilio;
- obra social;
- DNI UNIQUE;
- número de Historia Clínica único.

#### HU-02

- buscar por DNI;
- encontrar paciente;
- mostrar sus datos;
- manejar paciente inexistente.

#### Base de datos

Tabla `Pacientes` según la definición del PDF.

#### Datos

`Salud.db` debe contener al menos 5 pacientes.

#### Evidencias

En `Planilla Scrum.xlsx`, pestaña `Bitácora`:

1. captura de alta exitosa;
2. captura de búsqueda exitosa;
3. captura de intento de DNI duplicado.

#### Reflexión

Dos párrafos:

1. problema del hospital que resuelve el módulo;
2. relación con interoperabilidad / HL7 FHIR.

No afirmar que el Sprint 1 implementa FHIR. Solamente explicar su relación conceptual con una identificación consistente del paciente.

### Control de calidad

Antes de considerar terminada la entrega:

1. Ejecuta el programa.
2. Verifica la conexión con SQLite.
3. Verifica que la base esté en `BD/Salud.db`.
4. Verifica que existan mínimo 5 pacientes.
5. Prueba un alta correcta.
6. Prueba una búsqueda correcta.
7. Prueba un DNI duplicado.
8. Prueba un DNI inexistente.
9. Comprueba que los datos persisten.
10. Revisa que las evidencias coincidan con los criterios de aceptación.
11. Revisa que la documentación no diga que se implementaron funcionalidades todavía no realizadas.

### Forma de trabajar conmigo

Avanza en este orden:

```text
1. Auditoría de requisitos
2. Entrega 1
3. Revisión de Planilla Scrum
4. Base de datos
5. Código Python
6. Pruebas
7. Evidencias
8. Reflexión
9. Auditoría final de ambas entregas
```

Para cada etapa:

- indica qué exige la consigna;
- indica qué ya está realizado;
- indica qué falta;
- realiza los cambios necesarios;
- verifica el resultado antes de avanzar.

Mantén trazabilidad con las Historias de Usuario y sus criterios de aceptación.

---

# 33. Resultado final esperado

Al terminar el trabajo deberían existir, como mínimo:

```text
ENTREGA 1
└── Documento de Visión / documentación equivalente

ENTREGA 2
├── Pacientes.py
├── BD/
│   └── Salud.db
├── Planilla Scrum.xlsx
│   └── Bitácora con evidencias
└── Reflexión del equipo
```

Además, debe poder demostrarse que:

```text
HU-01 → cumple
HU-02 → cumple
DNI duplicado → bloqueado
5 pacientes → cargados
evidencias → registradas
```

---

# 34. Punto pendiente

Los PDFs analizados no especifican claramente dónde debe subirse físicamente la entrega.

Hasta contar con una consigna adicional, mantener como:

```text
Plataforma de entrega: NO ESPECIFICADA
Formato final de Entrega 1: NO ESPECIFICADO
Repositorio remoto obligatorio: NO ESPECIFICADO
```

---

# 35. ENTREGA 3 — Tercer PDF

Archivo base:

```text
Sist-Info-Salud-3.pdf
```

Esta entrega corresponde al **Sprint 2 del Epic 1 — Módulo de Gestión de Pacientes**.

El tercer PDF aclara que:

- los avances finalizados aparecen resaltados en verde;
- las evidencias que deben registrarse en `Planilla Scrum.xlsx` aparecen resaltadas en amarillo;
- el objetivo del Sprint 2 fue ampliado y debe actualizarse en la Planilla Scrum.

## 36. Cambio importante respecto de Entrega 2

El Sprint 2 ya no consiste solamente en agregar signos vitales. El objetivo actualizado es:

```text
Evolucionar el sistema a Interfaz Gráfica.
Implementar el registro de signos vitales y motivo
 de consulta durante la admisión médica.
Permitir modificaciones y bajas.
```

Por lo tanto, Entrega 3 amplía el alcance del Epic 1 en tres direcciones:

1. Migrar la aplicación de consola a una GUI con Tkinter.
2. Completar CRUD de pacientes: CREATE, READ, UPDATE y DELETE.
3. Implementar HU-03: signos vitales, motivo de consulta e historial de signos vitales.

También debe actualizarse la definición del Sprint 2 dentro de `Planilla Scrum.xlsx`.

## 37. Objetivos de Entrega 3

Al finalizar el Sprint 2, el equipo debe:

1. Comprender el concepto de GUI.
2. Verificar el entorno gráfico.
3. Migrar el CRUD de consola a interfaz gráfica.
4. Agregar modificación de pacientes.
5. Agregar baja de pacientes.
6. Crear la tabla `SignosVitales`.
7. Implementar el registro de signos vitales.
8. Implementar motivo de consulta.
9. Mostrar historial de signos vitales.
10. Verificar los criterios de aceptación de HU-03.
11. Documentar las evidencias en la Planilla Scrum.

## 38. Tecnología agregada

La aplicación pasa a utilizar:

```text
Python
SQLite
Tkinter
DB Browser for SQLite
```

Tkinter se usa para transformar la aplicación de consola en una interfaz gráfica orientada a eventos.

Conceptos básicos utilizados:

- `Tk()`
- `Frame`
- `Label`
- `Entry`
- `Button`
- `pack()`
- `grid()`
- `messagebox`
- `ttk.Treeview`

## 39. Archivos nuevos de Entrega 3

La guía construye tres versiones progresivas.

### 39.1. Primera evolución gráfica

```text
Pacientes_app.py
```

Funcionalidades:

- registrar paciente;
- buscar paciente;
- ver todos;
- interfaz Tkinter.

### 39.2. CRUD completo

```text
Pacientes2_app.pyw
```

El `.pyw` permite ejecutar la aplicación gráfica sin mostrar la consola.

Funcionalidades:

- CREATE;
- READ;
- UPDATE;
- DELETE;
- listado completo;
- interfaz gráfica.

### 39.3. Versión final del Sprint 2

```text
Pacientes2b_app.pyw
```

Funcionalidades:

- registrar paciente;
- buscar paciente;
- modificar paciente;
- eliminar paciente;
- listar pacientes;
- registrar signos vitales;
- registrar motivo de consulta;
- ver historial de signos vitales;
- acceso a signos vitales con doble clic;
- interfaz gráfica completa.

## 40. Estructura esperada luego de Entrega 3

```text
OpenHIS-UNLaM/
│
├── Pacientes.py
├── Pacientes_app.py
├── Pacientes2_app.pyw
├── Pacientes2b_app.pyw
│
└── BD/
    └── Salud.db
```

Además, `Planilla Scrum.xlsx` debe quedar con la Bitácora actualizada.

## 41. CRUD completo de pacientes

### CREATE

Registrar nuevo paciente. Se conservan DNI, nombre, apellido, fecha de nacimiento, sexo, teléfono, email, domicilio y obra social.

Validaciones principales:

- campos obligatorios;
- DNI único;
- sexo `M` o `F`.

### READ

Buscar paciente por DNI y mostrar Historia Clínica, DNI, nombre, apellido, fecha de nacimiento, sexo, teléfono, email, domicilio, obra social y fecha de registro.

También se incorpora `Ver Todos` para listar pacientes en un `Treeview`.

### UPDATE

Se incorpora modificación de:

```text
telefono
email
domicilio
obra_social
```

Flujo:

```text
Buscar por DNI
    ↓
Encontrar paciente
    ↓
Cargar valores actuales
    ↓
Editar
    ↓
Guardar cambios
```

### DELETE

Se incorpora baja de pacientes. La guía implementa inicialmente una eliminación física:

```sql
DELETE FROM Pacientes
WHERE id = ?
```

El propio PDF aclara que para una baja lógica podría agregarse un campo `activo`.

En la versión final, antes de eliminar el paciente también se eliminan sus signos vitales asociados.

## 42. HU-03 — Signos Vitales

Historia de Usuario:

```text
Como médico, quiero registrar el motivo de consulta
y los signos vitales del paciente en la admisión.
```

Criterios de aceptación originales:

- presión arterial;
- frecuencia cardíaca;
- temperatura;
- motivo;
- fecha y hora automáticas;
- asociación con el médico.

La versión final además incorpora presión sistólica, presión diastólica, saturación de oxígeno e historial de signos vitales.

## 43. Nueva tabla `SignosVitales`

Crear en `Salud.db`:

```sql
CREATE TABLE SignosVitales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    presion_sistolica INTEGER,
    presion_diastolica INTEGER,
    frecuencia_cardiaca INTEGER,
    temperatura REAL,
    saturacion_oxigeno INTEGER,
    motivo_consulta TEXT,
    medico_id INTEGER,
    FOREIGN KEY (paciente_id) REFERENCES Pacientes(id)
);
```

Interpretación:

```text
paciente_id
    ↓
Pacientes.id
```

`medico_id` queda preparado para una futura integración con el módulo de profesionales.

## 44. Funcionalidad de signos vitales

La aplicación debe permitir seleccionar un paciente y registrar:

```text
Presión sistólica
Presión diastólica
Frecuencia cardíaca
Temperatura
Saturación O2
Motivo de consulta
```

El motivo de consulta es obligatorio. Los campos numéricos deben validarse.

## 45. Historial de signos vitales

La aplicación muestra los últimos 10 registros del paciente, ordenados por:

```sql
ORDER BY fecha_hora DESC
```

Columnas:

```text
Fecha/Hora
Presión
FC
Temperatura
SatO2
Motivo
```

## 46. Acceso mediante doble clic

La versión final agrega:

```text
Doble clic sobre paciente
        ↓
Abrir ventana de signos vitales
```

## 47. Eliminación conjunta

La versión final elimina primero los signos vitales:

```sql
DELETE FROM SignosVitales
WHERE paciente_id = ?
```

Y después al paciente:

```sql
DELETE FROM Pacientes
WHERE id = ?
```

Objetivo: evitar registros huérfanos y mantener integridad referencial.

Aunque el documento lo denomina “eliminación en cascada”, en el código mostrado la eliminación se realiza explícitamente desde Python y no mediante `ON DELETE CASCADE` en la definición de la clave foránea.

## 48. Interfaz final esperada

```text
HOSPITAL UNIVERSITARIO SAN JUSTO
Sistema de Gestión de Pacientes - Sprint 2

[Registrar] [Buscar] [Modificar] [Eliminar]
          [Signos] [Ver Todos]

-------------------------------------------------

HC | DNI | Nombre | Apellido | Teléfono

-------------------------------------------------
```

| Botón | Función |
|---|---|
| Registrar | Alta de paciente |
| Buscar | Buscar por DNI |
| Modificar | Editar datos |
| Eliminar | Baja |
| Signos | Gestionar signos vitales |
| Ver Todos | Refrescar listado |

## 49. Pruebas requeridas

### GUI inicial

```text
[ ] Registrar paciente
[ ] Buscar paciente
[ ] DNI duplicado
[ ] Ver todos
```

### CRUD completo

```text
[ ] Modificar un paciente
[ ] Buscarlo nuevamente y verificar el cambio
[ ] Eliminar un paciente
[ ] Verificar que desaparece del listado
```

### Signos vitales

```text
[ ] Registrar signos vitales
[ ] Verificar el botón Signos Vitales
[ ] Doble clic sobre paciente
[ ] Verificar acceso a historial
[ ] Eliminar paciente con signos vitales
[ ] Verificar eliminación de los signos asociados
```

## 50. Entregables exactos de Entrega 3

### Base de datos

`Salud.db` debe contener:

- al menos 5 pacientes;
- signos vitales cargados en al menos 3 pacientes.

### Código

Entregar funcionando:

```text
Pacientes_app.py
Pacientes2_app.pyw
Pacientes2b_app.pyw
```

### Evidencias en Planilla Scrum

En `Planilla Scrum.xlsx` → pestaña `Bitácora`:

1. registro exitoso de alta de signos vitales;
2. modificación exitosa;
3. eliminación exitosa de paciente y sus signos vitales.

### Reflexión

Dos párrafos:

1. ¿Qué problema del hospital resuelve este módulo?
2. ¿Cómo se relaciona con la experiencia del usuario?

## 51. Actualización obligatoria de Planilla Scrum

El tercer PDF indica explícitamente que el Sprint 2 fue modificado. La planilla debe reflejar:

```text
Sprint 2
HU-03

Objetivo:
- evolucionar el sistema a interfaz gráfica;
- implementar signos vitales;
- implementar motivo de consulta;
- permitir modificaciones;
- permitir bajas.
```

## 52. Reflexión de Entrega 3 — enfoque recomendado

### Párrafo 1 — Problema hospitalario

Explicar que el módulo mejora la gestión integral del paciente porque centraliza sus datos, permite actualizarlos, registra datos clínicos objetivos, incorpora un historial asociado al mismo paciente y evita información clínica desconectada.

### Párrafo 2 — Experiencia del usuario

Explicar el salto de consola a interfaz gráfica. La GUI reduce dependencia de comandos, mejora accesibilidad y facilita la operación por administrativos y profesionales. No limitar la reflexión a estética: experiencia de usuario, eficacia y eficiencia deben considerarse de forma conjunta.

## 53. Relación con FHIR

El PDF vincula conceptualmente:

```text
Paciente       → FHIR Patient
Signos vitales → FHIR Observation
```

No debe afirmarse que la aplicación ya implementa FHIR.

## 54. Qué NO corresponde todavía

No corresponde todavía como requisito de Entrega 3:

- módulo completo de profesionales;
- turnos;
- agenda;
- SMS;
- SNOMED real;
- servidor FHIR;
- PACS;
- DICOM real;
- IA;
- internación;
- facturación.

El próximo avance anunciado es:

```text
Epic 2 — Gestión de Profesionales
Sprint 3
HU-04
HU-05
```

## 55. Relación entre las tres entregas

```text
ENTREGA 1
Visión del producto
        ↓
Problema hospitalario
        ↓
Backlog
        ↓
Epic 1
        ↓

ENTREGA 2
Sprint 1
HU-01 + HU-02
        ↓
Consola
        ↓
Pacientes
        ↓
CREATE + READ
        ↓

ENTREGA 3
Sprint 2
        ↓
Interfaz gráfica
        ↓
CRUD completo
        ↓
HU-03
        ↓
Signos Vitales
        ↓
Historial
```

## 56. Matriz acumulada de funcionalidades

| Funcionalidad | Entrega 1 | Entrega 2 | Entrega 3 |
|---|---:|---:|---:|
| Visión del producto | Sí | Referencia | Referencia |
| Backlog | Sí | Referencia | Actualización |
| Pacientes | Diseño | Implementación | Evolución |
| CREATE | Conceptual | Sí | Sí |
| READ | Conceptual | Sí | Sí |
| UPDATE | Conceptual | No | Sí |
| DELETE | Conceptual | No | Sí |
| GUI | No | No | Sí |
| Signos vitales | Planeado | Próximo | Sí |
| Historial de signos | No | No | Sí |
| Clave foránea | Conceptual | No | Sí |
| Planilla Scrum | Preparación | Evidencias Sprint 1 | Evidencias Sprint 2 |

## 57. Checklist — Entrega 3

```text
[ ] Actualizar Sprint 2 en Planilla Scrum.xlsx

[ ] Crear Pacientes_app.py
    [ ] GUI Tkinter
    [ ] Registrar
    [ ] Buscar
    [ ] Ver Todos

[ ] Crear Pacientes2_app.pyw
    [ ] CREATE
    [ ] READ
    [ ] UPDATE
    [ ] DELETE
    [ ] Ver Todos

[ ] Crear tabla SignosVitales

[ ] Crear Pacientes2b_app.pyw
    [ ] CRUD completo
    [ ] Registrar signos vitales
    [ ] Motivo de consulta
    [ ] Historial
    [ ] Doble clic
    [ ] Eliminación conjunta

[ ] Salud.db
    [ ] mínimo 5 pacientes
    [ ] signos vitales en mínimo 3 pacientes

[ ] Probar modificación
[ ] Probar eliminación
[ ] Probar alta de signos vitales
[ ] Probar historial
[ ] Probar eliminación de paciente con signos

[ ] Planilla Scrum.xlsx → Bitácora
    [ ] captura alta signos vitales
    [ ] captura modificación
    [ ] captura eliminación paciente + signos

[ ] Reflexión de 2 párrafos
    [ ] problema hospitalario
    [ ] experiencia del usuario
```

## 58. Extensión del prompt para ChatGPT Work

Agregar al prompt existente:

```text
También existe:

- Sist-Info-Salud-3.pdf = Entrega 3 / Sprint 2

Para Entrega 3 debes:

1. Detectar y aplicar la modificación del objetivo del Sprint 2.
2. Revisar que Planilla Scrum.xlsx refleje esa actualización.
3. Verificar Pacientes_app.py.
4. Verificar Pacientes2_app.pyw.
5. Verificar Pacientes2b_app.pyw.
6. Verificar que Salud.db tenga la tabla SignosVitales.
7. Verificar mínimo 5 pacientes.
8. Verificar signos vitales en mínimo 3 pacientes.
9. Probar CREATE, READ, UPDATE y DELETE.
10. Probar alta e historial de signos vitales.
11. Probar eliminación conjunta de paciente y signos.
12. Verificar las tres capturas requeridas en la Bitácora.
13. Preparar la reflexión de dos párrafos.
14. No afirmar que existe implementación FHIR real.
15. Distinguir entre eliminación manual desde Python y ON DELETE CASCADE.
```

## 59. Estado acumulado esperado después de Entrega 3

```text
Epic 1 — Gestión de Pacientes

HU-01
[OK] Registro de pacientes

HU-02
[OK] Búsqueda de pacientes

HU-03
[OK] Signos vitales
[OK] Motivo de consulta

Sprint 1
[OK] Consola
[OK] CREATE
[OK] READ

Sprint 2
[OK] GUI
[OK] UPDATE
[OK] DELETE
[OK] Signos vitales
[OK] Historial
```

La siguiente entrega debería iniciar el **Epic 2 — Gestión de Profesionales**, según el cierre del tercer PDF.
