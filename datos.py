"""Persistencia y validaciones compartidas por las cuatro aplicaciones."""

from contextlib import contextmanager
from datetime import date
import math
from pathlib import Path
import sqlite3

from esquema import ampliar_esquema


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


CATALOGOS = {
    "especialidades": ("Especialidades", ("codigo", "nombre", "descripcion"), "nombre"),
    "snomed": ("SnomedCT", ("codigo", "termino", "descripcion", "categoria"), "termino"),
    "farmacos": ("Farmacos", ("codigo", "nombre", "principio_activo", "presentacion", "concentracion", "via_administracion"), "nombre"),
}


def identificador(valor, etiqueta):
    try:
        texto = str(valor).strip()
        if not texto.isascii() or not texto.isdigit() or not 0 < int(texto) < 2**63:
            raise ValueError
        return int(texto)
    except (TypeError, ValueError):
        raise ErrorValidacion(f"Seleccione {etiqueta} válido.") from None


def textos(entrada, campos, obligatorios=()):
    salida = {campo: str(entrada.get(campo) or "").strip() for campo in campos}
    for campo in obligatorios:
        if not salida[campo]:
            raise ErrorValidacion(f"El campo {ETIQUETAS.get(campo, campo.replace('_', ' '))} es obligatorio.")
    return salida


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
            ampliar_esquema(conexion)

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

    def listar_pacientes(self, activos=True):
        filtro, parametros = self._filtro_estado(activos)
        with self.conectar() as conexion:
            return [dict(fila) for fila in conexion.execute("SELECT * FROM Pacientes WHERE 1=1" + filtro + " ORDER BY apellido, nombre, id", parametros)]

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
        """Compatibilidad con entradas anteriores: desde E5 la baja siempre es lógica."""
        return self.dar_baja_paciente(paciente_id)

    @staticmethod
    def _filtro_estado(activos, alias=""):
        if activos is None:
            return "", ()
        if activos is not True and activos is not False:
            raise ErrorValidacion("El filtro debe ser activos, inactivos o todos.")
        return f" AND {alias}activo=?", (int(activos),)

    def _cambiar_estado(self, tabla, registro_id, activo):
        if tabla not in ("Pacientes", "Profesionales", "SignosVitales", "Prescripciones"):
            raise ValueError("Tabla no admitida")
        with self.conectar() as conexion:
            fila = conexion.execute(f"SELECT activo FROM {tabla} WHERE id=?", (registro_id,)).fetchone()
            if fila is None:
                raise ErrorValidacion("El registro no existe.")
            if fila["activo"] == activo:
                raise ErrorValidacion("El registro ya estaba activo." if activo else "El registro ya estaba inactivo o anulado.")
            conexion.execute(f"UPDATE {tabla} SET activo=? WHERE id=?", (activo, registro_id))
        return registro_id

    def dar_baja_paciente(self, paciente_id):
        return self._cambiar_estado("Pacientes", paciente_id, 0)

    def reactivar_paciente(self, paciente_id):
        return self._cambiar_estado("Pacientes", paciente_id, 1)

    def contar_intervenciones(self, registro_id, tipo="paciente"):
        columnas = {"paciente": ("paciente_id", "paciente_id"), "profesional": ("medico_id", "profesional_id")}
        signo, receta = columnas[tipo]
        with self.conectar() as conexion:
            return {
                "signos": conexion.execute(f"SELECT COUNT(*) FROM SignosVitales WHERE {signo}=?", (registro_id,)).fetchone()[0],
                "prescripciones": conexion.execute(f"SELECT COUNT(*) FROM Prescripciones WHERE {receta}=?", (registro_id,)).fetchone()[0],
            }

    @staticmethod
    def _paciente_activo(conexion, paciente_id):
        fila = conexion.execute("SELECT activo FROM Pacientes WHERE id=?", (paciente_id,)).fetchone()
        if fila is None:
            raise PacienteNoEncontrado("El paciente no existe. Actualice el listado.")
        if not fila["activo"]:
            raise ErrorValidacion("El paciente está inactivo. Reactívelo antes de registrar una nueva intervención.")

    def registrar_signos(self, paciente_id, entrada):
        datos = validar_signos(entrada)
        datos["paciente_id"] = paciente_id
        with self.conectar() as conexion:
            self._paciente_activo(conexion, paciente_id)
            datos["medico_id"] = identificador(entrada.get("medico_id"), "un profesional")
            self._profesional_existente(conexion, datos["medico_id"], activo=True)
            cursor = conexion.execute("""
                INSERT INTO SignosVitales
                (paciente_id, presion_sistolica, presion_diastolica, frecuencia_cardiaca,
                    temperatura, saturacion_oxigeno, motivo_consulta, medico_id)
                VALUES (:paciente_id, :presion_sistolica, :presion_diastolica, :frecuencia_cardiaca,
                    :temperatura, :saturacion_oxigeno, :motivo_consulta, :medico_id)
            """, datos)
            return cursor.lastrowid

    def historial_signos(self, paciente_id, activos=None, limite=None):
        self.obtener_paciente(paciente_id)
        return self.listar_signos(paciente_id, activos=activos, limite=limite)

    def listar_signos(self, paciente_id=None, activos=True, limite=None):
        filtro, parametros = self._filtro_estado(activos, "s.")
        if paciente_id is not None:
            filtro += " AND s.paciente_id=?"
            parametros += (paciente_id,)
        if limite is not None:
            limite = identificador(limite, "un límite")
        with self.conectar() as conexion:
            return [dict(fila) for fila in conexion.execute("""
                SELECT s.*, p.nombre || ' ' || p.apellido AS profesional,
                    p.matricula, p.activo AS profesional_activo,
                    a.nombre || ' ' || a.apellido AS paciente, a.dni AS paciente_dni,
                    a.activo AS paciente_activo
                FROM SignosVitales s LEFT JOIN Profesionales p ON p.id=s.medico_id
                JOIN Pacientes a ON a.id=s.paciente_id WHERE 1=1
            """ + filtro + " ORDER BY s.fecha_hora DESC, s.id DESC" + (" LIMIT ?" if limite else ""), parametros + ((limite,) if limite else ()))]

    def obtener_signo(self, registro_id):
        for fila in self.listar_signos(activos=None):
            if fila["id"] == registro_id:
                return fila
        raise ErrorValidacion("El registro de signos no existe.")

    def anular_signo(self, registro_id):
        return self._cambiar_estado("SignosVitales", registro_id, 0)

    def reactivar_signo(self, registro_id):
        return self._cambiar_estado("SignosVitales", registro_id, 1)

    def asignar_profesional_signos(self, registro_id, profesional_id):
        profesional_id = identificador(profesional_id, "un profesional")
        with self.conectar() as conexion:
            self._profesional_existente(conexion, profesional_id)
            cursor = conexion.execute("UPDATE SignosVitales SET medico_id=? WHERE id=? AND medico_id IS NULL", (profesional_id, registro_id))
            if cursor.rowcount != 1:
                raise ErrorValidacion("El registro no existe o ya tiene un profesional asociado.")

    def listar_catalogo(self, catalogo, termino="", solo_activos=False):
        tabla, _, etiqueta = CATALOGOS[catalogo]
        condiciones, parametros = [], []
        if solo_activos:
            condiciones.append("activo=1")
        if termino.strip():
            condiciones.append(f"instr(lower({etiqueta}), lower(?)) > 0")
            parametros.append(termino.strip())
        filtro = " WHERE " + " AND ".join(condiciones) if condiciones else ""
        with self.conectar() as conexion:
            return [dict(fila) for fila in conexion.execute(f"SELECT * FROM {tabla}{filtro} ORDER BY {etiqueta}, id", parametros)]

    def guardar_catalogo(self, catalogo, entrada, registro_id=None):
        tabla, campos, etiqueta = CATALOGOS[catalogo]
        datos = textos(entrada, campos, ("codigo", etiqueta))
        if registro_id is not None and catalogo != "especialidades":
            raise ErrorValidacion("Esta tabla admite alta y listado en la entrega actual.")
        try:
            with self.conectar() as conexion:
                if registro_id is None:
                    columnas = ", ".join(campos)
                    parametros = ", ".join(f":{campo}" for campo in campos)
                    return conexion.execute(f"INSERT INTO {tabla} ({columnas}) VALUES ({parametros})", datos).lastrowid
                datos["id"] = registro_id
                asignaciones = ", ".join(f"{campo}=:{campo}" for campo in campos)
                cursor = conexion.execute(f"UPDATE {tabla} SET {asignaciones} WHERE id=:id", datos)
                if cursor.rowcount != 1:
                    raise ErrorValidacion("La especialidad no existe.")
                return registro_id
        except sqlite3.IntegrityError as error:
            if "UNIQUE" in str(error):
                raise ErrorValidacion("Ya existe un registro con ese código en esta tabla.") from error
            raise

    def desactivar_especialidad(self, especialidad_id):
        with self.conectar() as conexion:
            cursor = conexion.execute("UPDATE Especialidades SET activo=0 WHERE id=? AND activo=1", (especialidad_id,))
            if cursor.rowcount != 1:
                raise ErrorValidacion("La especialidad no existe o ya está inactiva.")

    @staticmethod
    def _especialidad_activa(conexion, especialidad_id):
        if not conexion.execute("SELECT 1 FROM Especialidades WHERE id=? AND activo=1", (especialidad_id,)).fetchone():
            raise ErrorValidacion("Seleccione una especialidad activa.")

    @staticmethod
    def _profesional_existente(conexion, profesional_id, activo=False):
        fila = conexion.execute("SELECT activo FROM Profesionales WHERE id=?", (profesional_id,)).fetchone()
        if fila is None:
            raise ErrorValidacion("El profesional seleccionado no existe.")
        if activo and not fila["activo"]:
            raise ErrorValidacion("El profesional está inactivo. Reactívelo antes de registrar una nueva intervención.")

    def registrar_profesional(self, entrada):
        datos = validar_paciente(entrada)
        datos.update(textos(entrada, ("matricula",), ("matricula",)))
        datos["especialidad_id"] = identificador(entrada.get("especialidad_id"), "una especialidad")
        try:
            with self.conectar() as conexion:
                self._especialidad_activa(conexion, datos["especialidad_id"])
                return conexion.execute("""
                    INSERT INTO Profesionales (dni,nombre,apellido,fecha_nacimiento,sexo,matricula,especialidad_id,telefono,email)
                    VALUES (:dni,:nombre,:apellido,:fecha_nacimiento,:sexo,:matricula,:especialidad_id,:telefono,:email)
                """, datos).lastrowid
        except sqlite3.IntegrityError as error:
            if "Profesionales.dni" in str(error):
                raise DNIDuplicado("Ya existe un profesional con ese DNI.") from error
            if "Profesionales.matricula" in str(error):
                raise ErrorValidacion("Ya existe un profesional con esa matrícula.") from error
            raise

    def listar_profesionales(self, activos=True):
        filtro, parametros = self._filtro_estado(activos, "p.")
        with self.conectar() as conexion:
            return [dict(fila) for fila in conexion.execute("""
                SELECT p.*, e.nombre AS especialidad, e.activo AS especialidad_activa
                FROM Profesionales p JOIN Especialidades e ON e.id=p.especialidad_id WHERE 1=1
            """ + filtro + " ORDER BY p.apellido, p.nombre, p.id", parametros)]

    def buscar_profesional(self, dni):
        dni = validar_dni(dni)
        with self.conectar() as conexion:
            fila = conexion.execute("""
                SELECT p.*, e.nombre AS especialidad, e.activo AS especialidad_activa
                FROM Profesionales p JOIN Especialidades e ON e.id=p.especialidad_id WHERE p.dni=?
            """, (dni,)).fetchone()
            return dict(fila) if fila else None

    def modificar_profesional(self, profesional_id, entrada):
        datos = textos(entrada, ("telefono", "email"))
        datos["id"] = profesional_id
        datos["especialidad_id"] = identificador(entrada.get("especialidad_id"), "una especialidad")
        with self.conectar() as conexion:
            existente = conexion.execute("SELECT * FROM Profesionales WHERE id=?", (profesional_id,)).fetchone()
            if existente is None:
                raise ErrorValidacion("El profesional no existe.")
            # Una especialidad desactivada conserva relaciones históricas. Se permite
            # editar contacto sin cambiarla; las nuevas asignaciones requieren una activa.
            if existente["especialidad_id"] != datos["especialidad_id"]:
                self._especialidad_activa(conexion, datos["especialidad_id"])
            conexion.execute("UPDATE Profesionales SET telefono=:telefono,email=:email,especialidad_id=:especialidad_id WHERE id=:id", datos)

    def eliminar_profesional(self, profesional_id):
        return self.dar_baja_profesional(profesional_id)

    def dar_baja_profesional(self, profesional_id):
        return self._cambiar_estado("Profesionales", profesional_id, 0)

    def reactivar_profesional(self, profesional_id):
        return self._cambiar_estado("Profesionales", profesional_id, 1)

    def registrar_prescripcion(self, entrada):
        campos = ("dosis", "via_administracion", "frecuencia", "duracion", "indicaciones", "fecha_inicio", "fecha_fin")
        datos = textos(entrada, campos, ("dosis", "via_administracion", "frecuencia"))
        for campo, etiqueta in (("paciente_id", "un paciente"), ("profesional_id", "un profesional"), ("farmaco_id", "un fármaco")):
            datos[campo] = identificador(entrada.get(campo), etiqueta)
        datos["snomed_id"] = identificador(entrada["snomed_id"], "un término SNOMED") if str(entrada.get("snomed_id") or "").strip() else None
        cantidad = entrada.get("cantidad")
        datos["cantidad"] = identificador(cantidad, "una cantidad entera positiva") if cantidad is not None and str(cantidad).strip() else None
        for campo in ("fecha_inicio", "fecha_fin"):
            if datos[campo]:
                try:
                    if date.fromisoformat(datos[campo]).isoformat() != datos[campo]:
                        raise ValueError
                except ValueError:
                    raise ErrorValidacion("Las fechas de la prescripción deben tener formato AAAA-MM-DD y ser válidas.") from None
        if datos["fecha_inicio"] and datos["fecha_fin"] and datos["fecha_fin"] < datos["fecha_inicio"]:
            raise ErrorValidacion("La fecha de fin no puede ser anterior a la de inicio.")
        with self.conectar() as conexion:
            self._paciente_activo(conexion, datos["paciente_id"])
            self._profesional_existente(conexion, datos["profesional_id"], activo=True)
            for tabla, campo, etiqueta in (("Farmacos", "farmaco_id", "fármaco"), ("SnomedCT", "snomed_id", "término SNOMED")):
                if datos[campo] is not None and not conexion.execute(f"SELECT 1 FROM {tabla} WHERE id=? AND activo=1", (datos[campo],)).fetchone():
                    raise ErrorValidacion(f"Seleccione un {etiqueta} activo y existente.")
            return conexion.execute("""
                INSERT INTO Prescripciones (paciente_id,profesional_id,farmaco_id,snomed_id,dosis,via_administracion,
                    frecuencia,duracion,cantidad,indicaciones,fecha_inicio,fecha_fin)
                VALUES (:paciente_id,:profesional_id,:farmaco_id,:snomed_id,:dosis,:via_administracion,
                    :frecuencia,:duracion,:cantidad,:indicaciones,:fecha_inicio,:fecha_fin)
            """, datos).lastrowid

    def listar_prescripciones(self, paciente_id=None, activos=True):
        filtro, parametros = self._filtro_estado(activos, "r.")
        if paciente_id is not None:
            filtro += " AND r.paciente_id=?"
            parametros += (paciente_id,)
        with self.conectar() as conexion:
            return [dict(fila) for fila in conexion.execute("""
                SELECT r.*, p.nombre || ' ' || p.apellido AS paciente, p.dni AS paciente_dni,
                    p.nombre AS paciente_nombre, p.apellido AS paciente_apellido,
                    p.fecha_nacimiento AS paciente_fecha_nac, p.sexo AS paciente_sexo,
                    p.telefono AS paciente_telefono, p.email AS paciente_email,
                    p.domicilio AS paciente_domicilio, p.obra_social AS paciente_obra_social,
                    p.activo AS paciente_activo,
                    m.nombre || ' ' || m.apellido AS profesional, m.matricula,
                    m.nombre AS profesional_nombre, m.apellido AS profesional_apellido,
                    m.dni AS profesional_dni, m.email AS profesional_email,
                    m.activo AS profesional_activo, e.nombre AS especialidad,
                    f.nombre AS farmaco, f.codigo AS farmaco_codigo,
                    f.principio_activo AS farmaco_principio, f.presentacion AS farmaco_presentacion,
                    f.concentracion AS farmaco_concentracion,
                    s.termino AS snomed, s.codigo AS snomed_codigo
                FROM Prescripciones r JOIN Pacientes p ON p.id=r.paciente_id
                JOIN Profesionales m ON m.id=r.profesional_id
                JOIN Farmacos f ON f.id=r.farmaco_id
                JOIN Especialidades e ON e.id=m.especialidad_id
                LEFT JOIN SnomedCT s ON s.id=r.snomed_id
                WHERE 1=1
            """ + filtro + " ORDER BY r.fecha_prescripcion DESC, r.id DESC", parametros)]

    def obtener_prescripcion(self, prescripcion_id):
        # Volumen educativo: reutilizar la consulta con joins mantiene un único detalle.
        for fila in self.listar_prescripciones(activos=None):
            if fila["id"] == prescripcion_id:
                return fila
        raise ErrorValidacion("La prescripción no existe.")

    def anular_prescripcion(self, prescripcion_id):
        return self._cambiar_estado("Prescripciones", prescripcion_id, 0)

    def reactivar_prescripcion(self, prescripcion_id):
        return self._cambiar_estado("Prescripciones", prescripcion_id, 1)
