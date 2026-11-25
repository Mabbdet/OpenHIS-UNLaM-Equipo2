# OpenHIS-UNLaM · Equipo 2

Sistema académico con aplicación de escritorio y turnero web para pacientes. Ambos usan la base SQLite de demostración `BD/Salud.db`.

## Instalación y ejecución en Windows

Desde la raíz del repositorio, con Python 3.10 o posterior y Tkinter:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

En una terminal, iniciar el escritorio:

```powershell
.\.venv\Scripts\python.exe OpenHIS_app.pyw
```

La cuenta administradora de demostración es `admin` con contraseña `admin123`. Desde el menú se accede a los módulos clínicos, la agenda, los turnos y la interoperabilidad FHIR y DICOM.

En otra terminal, iniciar el turnero:

```powershell
.\.venv\Scripts\python.exe turnero_web.py
```

Abrir [http://127.0.0.1:5000](http://127.0.0.1:5000). El personal habilita la clave individual desde **Turnos → Habilitar / renovar acceso web**. El paciente inicia sesión con su DNI y esa clave. El servidor escucha solo en esta computadora.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q -rs
```

La [planilla Scrum](scrum/Planilla%20Scrum.xlsx) conserva su Bitácora y evidencias incorporadas. Las guías, archivos de intercambio y demás evidencias citadas en la planilla están en la [revisión anterior del repositorio](https://github.com/Mabbdet/OpenHIS-UNLaM-Equipo2/tree/2d94dada2def394f3737b88fdeae162091c1f348).
