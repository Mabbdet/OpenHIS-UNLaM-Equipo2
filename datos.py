"""Persistencia y validaciones compartidas por las cuatro aplicaciones."""

from contextlib import contextmanager
from datetime import date
import math
from pathlib import Path
import sqlite3


RUTA_BD = Path(__file__).resolve().parent / "BD" / "Salud.db"
CAMPOS_PACIENTE = (
    "dni", "nombre", "apellido", "fecha_nacimiento", "sexo", "telefono",
    "email", "domicilio", "obra_social",
)
CAMPOS_EDITABLES = ("telefono", "email", "domicilio", "obra_social")
CAMPOS_SIGNOS = (
    "presion_sistolica", "presion_diastolica", "frecuencia_cardiaca",
    "temperatura", "saturacion_oxigeno",
)
ETIQUETAS = {
    "dni": "DNI", "nombre": "Nombre", "apellido": "Apellido",
    "fecha_nacimiento": "Fecha de nacimiento (AAAA-MM-DD)", "sexo": "Sexo (M/F)",
    "telefono": "Teléfono", "email": "Email", "domicilio": "Domicilio",
    "obra_social": "Obra social", "presion_sistolica": "Presión sistólica (mmHg)",
    "presion_diastolica": "Presión diastólica (mmHg)",
    "frecuencia_cardiaca": "Frecuencia cardíaca (lpm)",
    "temperatura": "Temperatura (°C)", "saturacion_oxigeno": "Saturación O2 (%)",
    "motivo_consulta": "Motivo de consulta",
}


class ErrorValidacion(ValueError):
    """Entrada incompleta o inválida."""


class DNIDuplicado(ErrorValidacion):
    """El identificador ya está registrado."""


class PacienteNoEncontrado(ErrorValidacion):
    """La ficha ya no existe o el identificador no corresponde a un paciente."""


def validar_dni(valor):
    dni = str(valor or "").strip()
    if not dni or not dni.isascii() or not dni.isdigit():
        raise ErrorValidacion("El DNI debe contener solamente números, sin puntos ni espacios.")
    return dni


def validar_paciente(entrada):
    datos = {campo: str(entrada.get(campo) or "").strip() for campo in CAMPOS_PACIENTE}
    datos["dni"] = validar_dni(datos["dni"])
    for campo in ("nombre", "apellido", "fecha_nacimiento", "sexo"):
        if not datos[campo]:
            raise ErrorValidacion(f"El campo {ETIQUETAS[campo]} es obligatorio.")
    try:
        nacimiento = date.fromisoformat(datos["fecha_nacimiento"])
    except ValueError as error:
        raise ErrorValidacion("La fecha de nacimiento debe ser válida y tener formato AAAA-MM-DD.") from error
    if nacimiento.isoformat() != datos["fecha_nacimiento"] or nacimiento > date.today():
        raise ErrorValidacion("La fecha de nacimiento debe tener formato AAAA-MM-DD y no ser futura.")
    datos["sexo"] = datos["sexo"].upper()
    if datos["sexo"] not in ("M", "F"):
        raise ErrorValidacion("El sexo debe ser M o F, según la consigna.")
    return datos


def validar_signos(entrada):
    motivo = str(entrada.get("motivo_consulta") or "").strip()
    if not motivo:
        raise ErrorValidacion("El motivo de consulta es obligatorio.")
    datos = {"motivo_consulta": motivo}
    for campo in CAMPOS_SIGNOS:
        valor = entrada.get(campo)
        texto = "" if valor is None else str(valor).strip()
        if not texto:
            datos[campo] = None
            continue
        try:
            numero = float(texto.replace(",", ".")) if campo == "temperatura" else int(texto)
        except ValueError as error:
            tipo = "un número" if campo == "temperatura" else "un número entero"
            raise ErrorValidacion(f"{ETIQUETAS[campo]} debe ser {tipo}.") from error
        if (campo == "temperatura" and not math.isfinite(numero)) or (campo != "temperatura" and not -(2**63) <= numero < 2**63):
            raise ErrorValidacion(f"{ETIQUETAS[campo]} contiene un valor numérico no admitido.")
        datos[campo] = numero
    return datos


class Repositorio:
    def __init__(self, ruta=RUTA_BD):
        self.ruta = Path(ruta).resolve()
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.inicializar()

    @contextmanager
    def conectar(self):
        conexion = sqlite3.connect(self.ruta)
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON")
        try:
            with conexion:
                yield conexion
        finally:
            conexion.close()

    def inicializar(self):
        with self.conectar() as conexion:
            conexion.executescript("""
                CREATE TABLE IF NOT EXISTS Pacientes (
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
                CREATE TABLE IF NOT EXISTS SignosVitales (
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
                CREATE INDEX IF NOT EXISTS idx_signos_paciente_fecha
                ON SignosVitales(paciente_id, fecha_hora DESC, id DESC);
            """)

    def registrar_paciente(self, entrada):
        datos = validar_paciente(entrada)
        try:
            with self.conectar() as conexion:
                cursor = conexion.execute("""
                    INSERT INTO Pacientes
                    (dni, nombre, apellido, fecha_nacimiento, sexo, telefono, email, domicilio, obra_social)
                    VALUES (:dni, :nombre, :apellido, :fecha_nacimiento, :sexo, :telefono, :email, :domicilio, :obra_social)
                """, datos)
                return cursor.lastrowid
        except sqlite3.IntegrityError as error:
            if "Pacientes.dni" in str(error):
                raise DNIDuplicado("Ya existe un paciente con ese DNI.") from error
            raise

    def buscar_paciente(self, dni):
        dni = validar_dni(dni)
        with self.conectar() as conexion:
            fila = conexion.execute("SELECT * FROM Pacientes WHERE dni = ?", (dni,)).fetchone()
            return dict(fila) if fila else None

    def obtener_paciente(self, paciente_id):
        with self.conectar() as conexion:
            fila = conexion.execute("SELECT * FROM Pacientes WHERE id = ?", (paciente_id,)).fetchone()
            if fila is None:
                raise PacienteNoEncontrado("El paciente no existe. Actualice el listado.")
            return dict(fila)

    def listar_pacientes(self):
        with self.conectar() as conexion:
            return [dict(fila) for fila in conexion.execute("SELECT * FROM Pacientes ORDER BY apellido, nombre, id")]

    def modificar_paciente(self, paciente_id, entrada):
        datos = {campo: str(entrada.get(campo) or "").strip() for campo in CAMPOS_EDITABLES}
        datos["id"] = paciente_id
        with self.conectar() as conexion:
            cursor = conexion.execute("""
                UPDATE Pacientes SET telefono=:telefono, email=:email,
                    domicilio=:domicilio, obra_social=:obra_social WHERE id=:id
            """, datos)
            if cursor.rowcount != 1:
                raise PacienteNoEncontrado("El paciente no existe. Actualice el listado.")

    def eliminar_paciente(self, paciente_id):
        # Ambas operaciones se confirman juntas o se revierten juntas.
        with self.conectar() as conexion:
            cantidad = conexion.execute("DELETE FROM SignosVitales WHERE paciente_id = ?", (paciente_id,)).rowcount
            cursor = conexion.execute("DELETE FROM Pacientes WHERE id = ?", (paciente_id,))
            if cursor.rowcount != 1:
                raise PacienteNoEncontrado("El paciente no existe. Actualice el listado.")
            return cantidad

    def registrar_signos(self, paciente_id, entrada):
        datos = validar_signos(entrada)
        datos["paciente_id"] = paciente_id
        with self.conectar() as conexion:
            if conexion.execute("SELECT id FROM Pacientes WHERE id = ?", (paciente_id,)).fetchone() is None:
                raise PacienteNoEncontrado("El paciente no existe. Actualice el listado.")
            cursor = conexion.execute("""
                INSERT INTO SignosVitales
                (paciente_id, presion_sistolica, presion_diastolica, frecuencia_cardiaca,
                    temperatura, saturacion_oxigeno, motivo_consulta)
                VALUES (:paciente_id, :presion_sistolica, :presion_diastolica, :frecuencia_cardiaca,
                    :temperatura, :saturacion_oxigeno, :motivo_consulta)
            """, datos)
            return cursor.lastrowid

    def historial_signos(self, paciente_id):
        self.obtener_paciente(paciente_id)
        with self.conectar() as conexion:
            return [dict(fila) for fila in conexion.execute("""
                SELECT * FROM SignosVitales WHERE paciente_id = ?
                ORDER BY fecha_hora DESC, id DESC LIMIT 10
            """, (paciente_id,))]
