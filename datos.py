"""Persistencia y validaciones compartidas por la aplicación de consola."""

from contextlib import contextmanager
from datetime import date
from pathlib import Path
import sqlite3


RUTA_BD = Path(__file__).resolve().parent / "BD" / "Salud.db"
CAMPOS_PACIENTE = (
    "dni", "nombre", "apellido", "fecha_nacimiento", "sexo", "telefono",
    "email", "domicilio", "obra_social",
)
ETIQUETAS = {
    "dni": "DNI", "nombre": "Nombre", "apellido": "Apellido",
    "fecha_nacimiento": "Fecha de nacimiento (AAAA-MM-DD)", "sexo": "Sexo (M/F)",
    "telefono": "Teléfono", "email": "Email", "domicilio": "Domicilio",
    "obra_social": "Obra social",
}


class ErrorValidacion(ValueError):
    """Entrada incompleta o inválida."""


class DNIDuplicado(ErrorValidacion):
    """El identificador ya está registrado."""



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
