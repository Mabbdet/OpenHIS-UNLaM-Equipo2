"""Autenticación, permisos y operaciones con auditoría atómica para HU-07.

Repositorio es la capa interna de migración y pruebas. Las aplicaciones reciben
RepositorioSeguro: no expone conexiones SQL ni operaciones sin permiso.
"""

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import hmac
import inspect
import json
import secrets
import sqlite3

from datos import CATALOGOS, ErrorValidacion, Repositorio, RUTA_BD
from esquema_seguridad import TABLAS_AUDITADAS

ROLES = ("admin", "medico", "enfermero", "administrativo")
PERMISOS = {
    'Agenda profesional': ('admin', 'administrativo'),
    'Configurar agenda': ('admin',),
    'Turnos': ('admin', 'administrativo'),
    'Agenda y recordatorios': ('admin', 'administrativo'),
    'Historia clínica': ('admin', 'medico', 'enfermero'),
    'Registrar HCE': ('admin', 'medico'),
    'Intervenciones': ('admin','medico','enfermero'),
    'FHIR': ('admin',),
    'DICOM': ('admin','medico','enfermero'),
    "Pacientes": ROLES,
    "Profesionales": ("admin", "administrativo"),
    "Signos vitales": ("admin", "medico", "enfermero"),
    "Prescripciones": ("admin", "medico"),
    "Tablas maestras": ("admin",), "Usuarios": ("admin",), "Auditoría": ("admin",),
}
ITERACIONES = 600_000


class AccesoDenegado(ErrorValidacion):
    """Sesión inexistente, revocada o sin permiso."""


def hashear_password(password):
    if not isinstance(password, str) or not 8 <= len(password) <= 256:
        raise ErrorValidacion("La contraseña debe tener entre 8 y 256 caracteres.")
    sal = secrets.token_hex(16)
    valor = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(sal), ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${sal}${valor.hex()}"


def verificar_password(password, almacenado):
    if not isinstance(password, str) or len(password) > 256:
        return False
    try:
        if len(almacenado) == 64:  # Compatibilidad con los hashes SHA-256 del material.
            return hmac.compare_digest(hashlib.sha256(password.encode("utf-8")).hexdigest(), almacenado)
        algoritmo, vueltas, sal, esperado = almacenado.split("$")
        if algoritmo != "pbkdf2_sha256" or not 1 <= int(vueltas) <= 2_000_000:
            return False
        valor = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(sal), int(vueltas))
        return hmac.compare_digest(valor.hex(), esperado)
    except (ValueError, TypeError, AttributeError):
        return False


@dataclass(frozen=True)
class Sesion:
    token: str


def _publico(fila):
    if fila is None:
        return None
    return {k: fila[k] for k in fila.keys() if k != "password_hash"}


def _auditar(c, actor, tabla, registro_id, accion, anterior=None, nuevo=None, referencia=None):
    c.execute("""INSERT INTO Auditoria
        (usuario_id,usuario_nombre,tabla_afectada,registro_id,tipo_accion,descripcion,
         datos_anteriores,datos_nuevos,origen_sistema,payload_referencia)
        VALUES (?,?,?,?,?,?,?,?,?,?)""", (
        actor["id"], actor["usuario"], tabla, registro_id, accion,
        f"{accion}: {tabla} #{registro_id}",
        json.dumps(anterior, ensure_ascii=False) if anterior is not None else None,
        json.dumps(nuevo, ensure_ascii=False) if nuevo is not None else None,
        "OpenHIS-UNLaM", str(referencia) if referencia is not None else None))


class _RepositorioTransaccional(Repositorio):
    """Reutiliza la transacción del servicio para el cambio y su auditoría."""
    transaccion = None

    @contextmanager
    def conectar(self):
        if self.transaccion is not None:
            yield self.transaccion
        else:
            with super().conectar() as conexion:
                yield conexion


class Seguridad:
    def __init__(self, ruta=RUTA_BD):
        self._repo = _RepositorioTransaccional(ruta)
        self._sesiones = {}

    def requiere_admin_inicial(self):
        with self._repo.conectar() as c:
            return c.execute("SELECT COUNT(*) FROM Usuarios").fetchone()[0] == 0

    def crear_admin_inicial(self, usuario, password, nombre):
        datos = self._validar_usuario(dict(usuario=usuario, password=password, nombre_completo=nombre, rol="admin"))
        with self._repo.conectar() as c:
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT COUNT(*) FROM Usuarios").fetchone()[0]:
                raise AccesoDenegado("El administrador inicial ya está creado. Ingrese al sistema.")
            nuevo = self._insertar_usuario(c, datos)
            c.execute("UPDATE Usuarios SET usuario_alta_id=? WHERE id=?", (nuevo, nuevo))
            actor = _publico(c.execute("SELECT * FROM Usuarios WHERE id=?", (nuevo,)).fetchone())
            _auditar(c, actor, "Usuarios", nuevo, "A", nuevo=actor)
            return nuevo

    def autenticar(self, usuario, password):
        with self._repo.conectar() as c:
            c.execute("BEGIN IMMEDIATE")
            fila = c.execute("SELECT * FROM Usuarios WHERE usuario=?", (str(usuario).strip(),)).fetchone()
            if not fila or not verificar_password(password, fila["password_hash"]) or not fila["activo"]:
                raise AccesoDenegado("Usuario o contraseña incorrectos, o cuenta inactiva.")
            if len(fila["password_hash"]) == 64:
                c.execute("UPDATE Usuarios SET password_hash=? WHERE id=?", (hashear_password(password), fila["id"]))
            c.execute("UPDATE Usuarios SET ultimo_acceso=CURRENT_TIMESTAMP WHERE id=?", (fila["id"],))
            _auditar(c, _publico(fila), "Usuarios", fila["id"], "L")
        sesion = Sesion(secrets.token_urlsafe(32))
        self._sesiones[sesion.token] = (fila["id"], fila["version_sesion"])
        return sesion

    def _actor(self, c, sesion, modulo=None):
        usuario_id, version = self._sesiones.get(getattr(sesion, "token", None), (None, None))
        fila = c.execute("SELECT * FROM Usuarios WHERE id=? AND activo=1", (usuario_id,)).fetchone()
        if fila is None or fila["version_sesion"] != version:
            raise AccesoDenegado("La sesión no está activa. Ingrese nuevamente.")
        actor = _publico(fila)
        if modulo is not None and actor["rol"] not in PERMISOS.get(modulo, ()):
            raise AccesoDenegado(f"Su rol no permite acceder a {modulo}.")
        return actor

    def autorizar(self, sesion, modulo=None):
        with self._repo.conectar() as c:
            return self._actor(c, sesion, modulo)

    def cerrar_sesion(self, sesion):
        datos = self._sesiones.get(getattr(sesion, "token", None))
        if datos is None:
            return
        usuario_id = datos[0]
        with self._repo.conectar() as c:
            actor = _publico(c.execute("SELECT * FROM Usuarios WHERE id=?", (usuario_id,)).fetchone())
            _auditar(c, actor, "Usuarios", usuario_id, "X")
        self._sesiones.pop(sesion.token, None)

    def repositorio(self, sesion):
        self.autorizar(sesion)
        return RepositorioSeguro(self, sesion)

    @staticmethod
    def _validar_usuario(entrada, nuevo=True):
        d = {k: str(entrada.get(k) or "").strip() for k in ("usuario", "nombre_completo", "email", "rol")}
        if not d["usuario"] or not d["nombre_completo"] or d["rol"] not in ROLES:
            raise ErrorValidacion("Complete usuario, nombre y un rol válido.")
        if len(d["usuario"]) > 60 or any(ch.isspace() for ch in d["usuario"]):
            raise ErrorValidacion("El usuario debe tener hasta 60 caracteres y no contener espacios.")
        if nuevo:
            d["password_hash"] = hashear_password(entrada.get("password"))
        return d

    @staticmethod
    def _insertar_usuario(c, d):
        try:
            return c.execute("""INSERT INTO Usuarios (usuario,password_hash,nombre_completo,email,rol)
                VALUES (:usuario,:password_hash,:nombre_completo,:email,:rol)""", d).lastrowid
        except sqlite3.IntegrityError as error:
            raise ErrorValidacion("Ya existe ese nombre de usuario.") from error

    def listar_usuarios(self, sesion, activos=None):
        with self._repo.conectar() as c:
            self._actor(c, sesion, "Usuarios")
            filtro, args = Repositorio._filtro_estado(activos)
            return [_publico(f) for f in c.execute("SELECT * FROM Usuarios WHERE 1=1" + filtro + " ORDER BY id", args)]

    def guardar_usuario(self, sesion, entrada, usuario_id=None):
        datos = self._validar_usuario(entrada, nuevo=usuario_id is None)
        with self._repo.conectar() as c:
            c.execute("BEGIN IMMEDIATE")
            actor = self._actor(c, sesion, "Usuarios")
            anterior = None
            if usuario_id is None:
                usuario_id = self._insertar_usuario(c, datos)
                c.execute("UPDATE Usuarios SET usuario_alta_id=? WHERE id=?", (actor["id"], usuario_id))
            else:
                anterior = self._usuario(c, usuario_id)
                self._proteger_admin(c, anterior, datos["rol"], anterior["activo"])
                c.execute("UPDATE Usuarios SET nombre_completo=:nombre_completo,email=:email,rol=:rol WHERE id=:id", {**datos, "id": usuario_id})
            nuevo = self._usuario(c, usuario_id)
            _auditar(c, actor, "Usuarios", usuario_id, "M" if anterior else "A", anterior, nuevo)
            return usuario_id

    @staticmethod
    def _usuario(c, usuario_id):
        fila = c.execute("SELECT * FROM Usuarios WHERE id=?", (usuario_id,)).fetchone()
        if fila is None:
            raise ErrorValidacion("El usuario no existe.")
        return _publico(fila)

    @staticmethod
    def _proteger_admin(c, anterior, rol, activo):
        if anterior["rol"] == "admin" and anterior["activo"] and (rol != "admin" or not activo):
            if not c.execute("SELECT 1 FROM Usuarios WHERE rol='admin' AND activo=1 AND id!=?", (anterior["id"],)).fetchone():
                raise ErrorValidacion("No se puede desactivar ni cambiar el rol del último administrador activo.")

    def cambiar_estado_usuario(self, sesion, usuario_id, activo):
        if activo not in (0, 1):
            raise ErrorValidacion("Estado de usuario no válido.")
        with self._repo.conectar() as c:
            c.execute("BEGIN IMMEDIATE")
            actor = self._actor(c, sesion, "Usuarios")
            anterior = self._usuario(c, usuario_id)
            if anterior["activo"] == activo:
                raise ErrorValidacion("El usuario ya tiene ese estado.")
            self._proteger_admin(c, anterior, anterior["rol"], activo)
            c.execute("UPDATE Usuarios SET activo=?,version_sesion=version_sesion+1 WHERE id=?", (activo, usuario_id))
            _auditar(c, actor, "Usuarios", usuario_id, "R" if activo else "B", anterior, self._usuario(c, usuario_id))
        if not activo:
            self._revocar_usuario(usuario_id)

    def _revocar_usuario(self, usuario_id):
        for token, datos in list(self._sesiones.items()):
            if datos[0] == usuario_id:
                del self._sesiones[token]

    def cambiar_password(self, sesion, usuario_id, password):
        valor = hashear_password(password)
        with self._repo.conectar() as c:
            c.execute("BEGIN IMMEDIATE")
            actor = self._actor(c, sesion, "Usuarios")
            self._usuario(c, usuario_id)
            c.execute("UPDATE Usuarios SET password_hash=?,version_sesion=version_sesion+1 WHERE id=?", (valor, usuario_id))
            _auditar(c, actor, "Usuarios", usuario_id, "M", nuevo={"contraseña_actualizada": True})
        self._revocar_usuario(usuario_id)

    def listar_auditoria(self, sesion, usuario_id=None, tabla="", accion="", limite=500):
        if not isinstance(limite, int) or not 1 <= limite <= 5000:
            raise ErrorValidacion("El límite debe estar entre 1 y 5000.")
        with self._repo.conectar() as c:
            self._actor(c, sesion, "Auditoría")
            condiciones, args = [], []
            for campo, valor in (("usuario_id", usuario_id), ("tabla_afectada", tabla), ("tipo_accion", accion)):
                if valor is not None and valor != "":
                    condiciones.append(campo + "=?")
                    args.append(valor)
            filtro = " WHERE " + " AND ".join(condiciones) if condiciones else ""
            return [dict(f) for f in c.execute("SELECT * FROM Auditoria" + filtro + " ORDER BY id DESC LIMIT ?", (*args, limite))]


# Operaciones de escritura: tabla y posición del ID, o None para un alta.
ESCRITURAS = {
    "registrar_paciente": ("Pacientes", None), "modificar_paciente": ("Pacientes", 0),
    "eliminar_paciente": ("Pacientes", 0), "dar_baja_paciente": ("Pacientes", 0), "reactivar_paciente": ("Pacientes", 0),
    "registrar_profesional": ("Profesionales", None), "modificar_profesional": ("Profesionales", 0),
    "eliminar_profesional": ("Profesionales", 0), "dar_baja_profesional": ("Profesionales", 0), "reactivar_profesional": ("Profesionales", 0),
    "registrar_signos": ("SignosVitales", None), "asignar_profesional_signos": ("SignosVitales", 0),
    "anular_signo": ("SignosVitales", 0), "reactivar_signo": ("SignosVitales", 0),
    "registrar_prescripcion": ("Prescripciones", None), "anular_prescripcion": ("Prescripciones", 0), "reactivar_prescripcion": ("Prescripciones", 0),
    "desactivar_especialidad": ("Especialidades", 0),
}
LECTURAS = {
    "buscar_paciente": "Pacientes", "obtener_paciente": "Pacientes", "listar_pacientes": "Pacientes",
    "contar_intervenciones": "Pacientes", "listar_signos": "Signos vitales", "obtener_signo": "Signos vitales",
    "historial_signos": "Signos vitales",
    "listar_prescripciones": "Prescripciones", "obtener_prescripcion": "Prescripciones",
    "buscar_profesional": "Profesionales",
    # Datos de referencia requeridos por los formularios clínicos, sin habilitar su gestión.
    "listar_profesionales": None, "listar_catalogo": None,
}
MODULO_TABLA = {"Pacientes": "Pacientes", "Profesionales": "Profesionales", "SignosVitales": "Signos vitales",
                "Prescripciones": "Prescripciones", "Especialidades": "Tablas maestras", "SnomedCT": "Tablas maestras", "Farmacos": "Tablas maestras"}


class RepositorioSeguro:
    def __init__(self, servicio, sesion):
        self._servicio = servicio
        self._sesion = sesion

    def autorizar(self, modulo=None):
        return self._servicio.autorizar(self._sesion, modulo)

    def __getattr__(self, nombre):
        catalogo_escritura = nombre in ("guardar_catalogo", "desactivar_catalogo")
        if nombre not in ESCRITURAS and nombre not in LECTURAS and not catalogo_escritura:
            raise AttributeError(nombre)

        def ejecutar(*args, **kwargs):
            repo = self._servicio._repo
            metodo = getattr(repo, nombre)
            argumentos = inspect.signature(metodo).bind(*args, **kwargs)
            argumentos.apply_defaults()
            escritura = nombre in ESCRITURAS or catalogo_escritura
            if catalogo_escritura:
                tabla = CATALOGOS[argumentos.arguments["catalogo"]][0]
                registro_id = argumentos.arguments["registro_id"]
            elif escritura:
                tabla, posicion = ESCRITURAS[nombre]
                registro_id = list(argumentos.arguments.values())[posicion] if posicion is not None else None
            else:
                tabla, registro_id = None, None
            modulo = MODULO_TABLA[tabla] if escritura else LECTURAS[nombre]
            with repo.conectar() as c:
                if escritura:
                    c.execute("BEGIN IMMEDIATE")
                actor = self._servicio._actor(c, self._sesion, modulo)
                anterior = self._fila(c, tabla, registro_id) if escritura and registro_id is not None else None
                repo.transaccion = c
                try:
                    resultado = metodo(*args, **kwargs)
                    if escritura:
                        if anterior is None:
                            registro_id = resultado
                            c.execute(f"UPDATE {tabla} SET usuario_alta_id=? WHERE id=?", (actor["id"], registro_id))
                        nuevo = self._fila(c, tabla, registro_id)
                        accion = "A" if anterior is None else "M"
                        if anterior and anterior.get("activo") != nuevo.get("activo"):
                            accion = "R" if nuevo["activo"] else "B"
                        _auditar(c, actor, tabla, registro_id, accion, anterior, nuevo)
                finally:
                    repo.transaccion = None
                return resultado
        return ejecutar

    @staticmethod
    def _fila(c, tabla, registro_id):
        if tabla not in TABLAS_AUDITADAS:
            raise ValueError("Tabla no admitida")
        return _publico(c.execute(f"SELECT * FROM {tabla} WHERE id=?", (registro_id,)).fetchone())

    def registrar_exportacion(self, registro_id, ruta, formato):
        with self._servicio._repo.conectar() as c:
            actor = self._servicio._actor(c, self._sesion, "Prescripciones")
            _auditar(c, actor, "Prescripciones", registro_id, "E", nuevo={"formato": formato}, referencia=ruta)
