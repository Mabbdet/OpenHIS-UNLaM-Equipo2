import hashlib
import json
import sqlite3
import tkinter as tk

import pytest

from datos import ErrorValidacion, Repositorio
from exportaciones import exportar_prescripcion
from seguridad import AccesoDenegado, Seguridad, Sesion, hashear_password, verificar_password
from seguridad_app import LoginApp, UsuariosApp, AuditoriaApp
from menu_app import MenuApp, MODULOS
from cargar_demo import cargar_demo
from interfaz import AplicacionPacientes
from ventanas_clinicas import TablasMaestrasApp


@pytest.fixture
def seguridad(repositorio):
    servicio = Seguridad(repositorio.ruta)
    servicio.crear_admin_inicial("admin", "AdminTest123", "Administrador prueba")
    sesion = servicio.autenticar("admin", "AdminTest123")
    return servicio, sesion


def alta(servicio, sesion, usuario, rol):
    return servicio.guardar_usuario(sesion, dict(usuario=usuario, password="ClaveTest123", nombre_completo=f"Usuario {usuario}", rol=rol))


def test_hash_con_sal_y_compatibilidad():
    a, b = hashear_password("ClaveTest123"), hashear_password("ClaveTest123")
    assert a != b and verificar_password("ClaveTest123", a)
    assert not verificar_password("incorrecta", a)
    assert not verificar_password("ClaveTest123", "hash-roto")
    assert verificar_password("admin123", hashlib.sha256(b"admin123").hexdigest())
    with pytest.raises(ErrorValidacion):
        hashear_password("corta")


def test_bootstrap_unico_login_logout_y_sesion_falsa(seguridad, repositorio):
    s, sesion = seguridad
    with pytest.raises(AccesoDenegado):
        s.crear_admin_inicial("otro", "ClaveTest123", "Otro admin")
    for usuario, clave in [("admin", "incorrecta"), ("nadie", "AdminTest123"), ("' OR 1=1 --", "AdminTest123")]:
        with pytest.raises(AccesoDenegado):
            s.autenticar(usuario, clave)
    with pytest.raises(AccesoDenegado):
        s.repositorio(Sesion("falsa"))
    repo = s.repositorio(sesion)
    with pytest.raises(AttributeError):
        repo.conectar()
    s.cerrar_sesion(sesion)
    with pytest.raises(AccesoDenegado):
        repo.listar_pacientes()
    otra = s.autenticar("admin", "AdminTest123")
    assert {f["tipo_accion"] for f in s.listar_auditoria(otra)} >= {"A", "L", "X"}
    assert s.listar_usuarios(otra)[0]["ultimo_acceso"]


@pytest.mark.parametrize("rol,permitidos", [
    ("admin", set(MODULOS)), ("medico", {"Pacientes", "Signos vitales", "Prescripciones", "Intervenciones", "DICOM", "Historia clínica"}),
    ("enfermero", {"Pacientes", "Signos vitales", "Intervenciones", "DICOM", "Historia clínica"}), ("administrativo", {"Pacientes", "Profesionales", "Agenda profesional", "Turnos", "Agenda y recordatorios"})])
def test_menu_y_acceso_directo_por_rol(seguridad, raiz_tk, rol, permitidos):
    s, admin = seguridad
    alta(s, admin, "prueba", rol)
    sesion = s.autenticar("prueba", "ClaveTest123")
    repo = s.repositorio(sesion)
    menu = MenuApp(raiz_tk, repo)
    assert set(menu.botones) == permitidos
    for nombre in MODULOS:
        if nombre in permitidos:
            app = menu.abrir(nombre)
            assert app.raiz.winfo_exists()
            app.raiz.destroy()
        else:
            with pytest.raises(AccesoDenegado):
                menu.abrir(nombre)


@pytest.mark.parametrize("rol", ["medico", "enfermero", "administrativo"])
def test_permisos_backend_sin_menu(seguridad, datos_paciente, rol):
    s, admin = seguridad
    alta(s, admin, "prueba", rol)
    sesion = s.autenticar("prueba", "ClaveTest123")
    repo = s.repositorio(sesion)
    with pytest.raises(AccesoDenegado):
        repo.guardar_catalogo("farmacos", {"codigo": "X", "nombre": "Prueba"})
    with pytest.raises(AccesoDenegado):
        s.listar_usuarios(sesion)
    with pytest.raises(AccesoDenegado):
        s.listar_auditoria(sesion)
    if rol != "administrativo":
        with pytest.raises(AccesoDenegado):
            repo.registrar_profesional(datos_paciente)
    if rol != "medico":
        with pytest.raises(AccesoDenegado):
            repo.registrar_prescripcion({})
    if rol == "administrativo":
        with pytest.raises(AccesoDenegado):
            repo.listar_signos()


def test_usuario_validaciones_ultimo_admin_y_revocacion(seguridad):
    s, sesion = seguridad
    admin = s.listar_usuarios(sesion)[0]
    with pytest.raises(ErrorValidacion):
        s.cambiar_estado_usuario(sesion, admin["id"], 0)
    with pytest.raises(ErrorValidacion):
        s.guardar_usuario(sesion, {**admin, "rol": "medico"}, admin["id"])
    usuario = alta(s, sesion, "medico", "medico")
    medico = s.autenticar("medico", "ClaveTest123")
    s.cambiar_estado_usuario(sesion, usuario, 0)
    with pytest.raises(AccesoDenegado):
        s.autorizar(medico)
    with pytest.raises(AccesoDenegado):
        s.autenticar("medico", "ClaveTest123")
    s.cambiar_estado_usuario(sesion, usuario, 1)
    with pytest.raises(AccesoDenegado):
        s.autorizar(medico)
    medico = s.autenticar("medico", "ClaveTest123")
    s.cambiar_password(sesion, usuario, "ClaveNueva123")
    with pytest.raises(AccesoDenegado):
        s.autorizar(medico)
    with pytest.raises(AccesoDenegado):
        s.autenticar("medico", "ClaveTest123")
    assert s.autenticar("medico", "ClaveNueva123")
    with pytest.raises(ErrorValidacion):
        alta(s, sesion, "medico", "medico")
    with pytest.raises(ErrorValidacion):
        alta(s, sesion, "invalido", "superadmin")
    logs = json.dumps(s.listar_auditoria(sesion), ensure_ascii=False)
    for secreto in ["password_hash", "ClaveTest123", "ClaveNueva123", "pbkdf2_sha256"]:
        assert secreto not in logs


def test_rol_actualizado_se_aplica_a_sesiones_abiertas(seguridad):
    s, sesion = seguridad
    i = alta(s, sesion, "doctor", "medico")
    doctor = s.autenticar("doctor", "ClaveTest123")
    repo = s.repositorio(doctor)
    assert repo.listar_prescripciones() == []
    s.guardar_usuario(sesion, dict(usuario="doctor", nombre_completo="Doctor", rol="administrativo"), i)
    with pytest.raises(AccesoDenegado):
        repo.listar_prescripciones()


def test_auditoria_completa_y_autor_transaccional(seguridad, datos_paciente, tmp_path):
    s, sesion = seguridad
    r = s.repositorio(sesion)
    paciente = r.registrar_paciente(datos_paciente)
    r.modificar_paciente(paciente, {**datos_paciente, "telefono": "555-9999"})
    esp = r.guardar_catalogo("especialidades", {"codigo": "E7", "nombre": "Especialidad"})
    r.guardar_catalogo("especialidades", {"codigo": "E7", "nombre": "Nueva especialidad"}, esp)
    farmaco = r.guardar_catalogo("farmacos", {"codigo": "F7", "nombre": "Fármaco"})
    snomed = r.guardar_catalogo("snomed", {"codigo": "S7", "termino": "Prueba"})
    profesional = r.registrar_profesional({**datos_paciente, "dni": "40111222", "matricula": "MAT-7", "especialidad_id": esp})
    r.modificar_profesional(profesional, {"especialidad_id": esp, "telefono": "123"})
    signo = r.registrar_signos(paciente, {"medico_id": profesional, "motivo_consulta": "Prueba"})
    receta = r.registrar_prescripcion(dict(paciente_id=paciente, profesional_id=profesional, farmaco_id=farmaco, snomed_id=snomed, dosis="Prueba", frecuencia="Prueba", via_administracion="Prueba"))
    for baja, reactivar, i in [(r.dar_baja_paciente, r.reactivar_paciente, paciente), (r.dar_baja_profesional, r.reactivar_profesional, profesional),
                               (r.anular_signo, r.reactivar_signo, signo), (r.anular_prescripcion, r.reactivar_prescripcion, receta)]:
        baja(i)
        reactivar(i)
    r.desactivar_especialidad(esp)
    ruta, _ = exportar_prescripcion(r, receta, "xml", tmp_path)
    logs = s.listar_auditoria(sesion)
    for tabla, i in [("Pacientes", paciente), ("Profesionales", profesional), ("SignosVitales", signo), ("Prescripciones", receta)]:
        eventos = {f["tipo_accion"] for f in logs if f["tabla_afectada"] == tabla and f["registro_id"] == i}
        assert eventos >= {"A", "B", "R"}
    cambios = s.listar_auditoria(sesion, tabla="Pacientes", accion="M")
    assert json.loads(cambios[0]["datos_anteriores"])["telefono"] == datos_paciente["telefono"]
    assert json.loads(cambios[0]["datos_nuevos"])["telefono"] == "555-9999"
    assert r.obtener_paciente(paciente)["usuario_alta_id"] == s.autorizar(sesion)["id"]
    assert str(ruta) in [f["payload_referencia"] for f in logs]


def test_fallo_auditoria_revierte_alta(seguridad, datos_paciente, repositorio):
    s, sesion = seguridad
    with repositorio.conectar() as c:
        c.execute("CREATE TRIGGER rechazar_log BEFORE INSERT ON Auditoria BEGIN SELECT RAISE(ABORT,'fallo simulado'); END")
    with pytest.raises(sqlite3.IntegrityError):
        s.repositorio(sesion).registrar_paciente(datos_paciente)
    assert repositorio.listar_pacientes() == []


def test_exportacion_fallida_y_denegada_no_deja_archivos(seguridad, repositorio, tmp_path):
    s, sesion = seguridad
    cargar_demo(repositorio)
    receta = repositorio.listar_prescripciones()[0]["id"]
    r = s.repositorio(sesion)
    with repositorio.conectar() as c:
        c.execute("CREATE TRIGGER rechazar_exportacion BEFORE INSERT ON Auditoria WHEN NEW.tipo_accion='E' BEGIN SELECT RAISE(ABORT,'fallo simulado'); END")
    with pytest.raises(sqlite3.IntegrityError):
        exportar_prescripcion(r, receta, "xml", tmp_path)
    assert list((tmp_path / "recetas").glob("*.xml")) == []
    alta(s, sesion, "enfermero", "enfermero")
    enfermero = s.repositorio(s.autenticar("enfermero", "ClaveTest123"))
    with pytest.raises(AccesoDenegado):
        exportar_prescripcion(enfermero, receta, "xml", tmp_path)
    assert list((tmp_path / "recetas").glob("*.xml")) == []


def test_revocacion_entre_instancias_y_parametros_por_nombre(seguridad, repositorio, datos_paciente):
    s, sesion = seguridad
    i = alta(s, sesion, "medico", "medico")
    otra = Seguridad(repositorio.ruta)
    medico = otra.autenticar("medico", "ClaveTest123")
    repo = otra.repositorio(medico)
    paciente = repo.registrar_paciente(entrada=datos_paciente)
    repo.modificar_paciente(paciente_id=paciente, entrada={**datos_paciente, "telefono": "999"})
    s.cambiar_password(sesion, i, "ClaveNueva123")
    with pytest.raises(AccesoDenegado):
        repo.listar_pacientes()


def test_login_sha256_heredado_se_actualiza(seguridad, repositorio):
    s, sesion = seguridad
    i = alta(s, sesion, "legado", "medico")
    with repositorio.conectar() as c:
        c.execute("UPDATE Usuarios SET password_hash=? WHERE id=?", (hashlib.sha256(b"ClaveTest123").hexdigest(), i))
    s.autenticar("legado", "ClaveTest123")
    with repositorio.conectar() as c:
        assert c.execute("SELECT password_hash FROM Usuarios WHERE id=?", (i,)).fetchone()[0].startswith("pbkdf2_sha256$")


def test_migracion_repetible_conserva_historicos(repositorio, datos_paciente):
    i = repositorio.registrar_paciente(datos_paciente)
    repositorio.dar_baja_paciente(i)
    for _ in range(2):
        Seguridad(repositorio.ruta)
    ficha = repositorio.obtener_paciente(i)
    assert ficha["activo"] == 0 and ficha["usuario_alta_id"] is None
    with repositorio.conectar() as c:
        assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert c.execute("PRAGMA foreign_key_check").fetchall() == []


def test_gui_login_usuario_y_auditoria(seguridad, raiz_tk, monkeypatch):
    s, sesion = seguridad
    recibidas = []
    login = LoginApp(raiz_tk, s, recibidas.append)
    login.usuario.set("admin")
    login.password.set("incorrecta")
    login.ingresar()
    assert not recibidas and login.estado.get()
    login.password.set("AdminTest123")
    login.ingresar()
    assert len(recibidas) == 1 and login.password.get() == ""
    errores = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *a, **k: errores.append(a))
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *a, **k: None)
    app = UsuariosApp(raiz_tk, s.repositorio(recibidas[0]))
    f = app.registrar()
    for campo, valor in dict(usuario="nuevo", nombre_completo="Nuevo usuario", password="ClaveTest123", rol="enfermero").items():
        f.campos[campo].set(valor)
    controles = f.winfo_children()[0].winfo_children()
    assert any(isinstance(w, tk.ttk.Entry) and w.cget("show") == "*" for w in controles)
    f.guardar()
    assert not errores and len(app.filas) == 2
    app.cuerpo.destroy()
    auditoria = AuditoriaApp(raiz_tk, s.repositorio(sesion))
    assert len(auditoria.filas) >= 4
    auditoria.accion.set("A")
    auditoria.refrescar()
    assert all(f["tipo_accion"] == "A" for f in auditoria.filas.values())


@pytest.mark.parametrize("nombre", [None, "Pacientes", "Profesionales", "Signos vitales", "Prescripciones", "Tablas maestras", "Usuarios", "Auditoría"])
def test_arranque_y_logout_real_de_cada_acceso(seguridad, raiz_tk, monkeypatch, nombre):
    import menu_app
    s, _ = seguridad
    logins = []
    menus = []
    class LoginRegistrado(LoginApp):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            logins.append(self)
    class MenuRegistrado(MenuApp):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            menus.append(self)
    monkeypatch.setattr(menu_app.tk, "Tk", lambda: raiz_tk)
    monkeypatch.setattr(raiz_tk, "mainloop", lambda: None)
    monkeypatch.setattr(menu_app, "Seguridad", lambda: s)
    monkeypatch.setattr(menu_app, "LoginApp", LoginRegistrado)
    monkeypatch.setattr(menu_app, "MenuApp", MenuRegistrado)
    errores = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *a, **k: errores.append(a))
    menu_app.ejecutar_modulo(nombre)
    logins[0].usuario.set("admin")
    logins[0].password.set("AdminTest123")
    logins[0].ingresar()
    raiz_tk.update_idletasks()
    assert not errores
    hijo = menus[0].abrir("Usuarios").raiz if menus else None
    def botones(widget):
        for w in widget.winfo_children():
            if isinstance(w, tk.ttk.Button):
                yield w
            yield from botones(w)
    cerrar = next(w for w in botones(raiz_tk) if w.cget("text") == "Cerrar sesión")
    cerrar.invoke()
    assert len(logins) == 2
    if hijo:
        assert not hijo.winfo_exists()
    assert s.listar_auditoria(s.autenticar("admin", "AdminTest123"))[1]["tipo_accion"] == "X"


@pytest.mark.parametrize("catalogo,campo", [("especialidades", "nombre"), ("snomed", "termino"), ("farmacos", "nombre")])
def test_tres_catalogos_modificacion_baja_y_auditoria(seguridad, raiz_tk, monkeypatch, catalogo, campo):
    s, sesion = seguridad
    r = s.repositorio(sesion)
    i = r.guardar_catalogo(catalogo, {"codigo": "E7-CAT", campo: "Original"})
    app = TablasMaestrasApp(raiz_tk, r)
    app.tablas[catalogo].selection_set(str(i))
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *a, **k: None)
    monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *a, **k: True)
    f = app.modificar(catalogo)
    f.campos[campo].set("Modificado")
    f.guardar()
    app.desactivar(catalogo)
    fila = r.listar_catalogo(catalogo)[0]
    assert fila[campo] == "Modificado" and fila["activo"] == 0
    tabla = {"especialidades": "Especialidades", "snomed": "SnomedCT", "farmacos": "Farmacos"}[catalogo]
    assert {f["tipo_accion"] for f in s.listar_auditoria(sesion, tabla=tabla)} == {"A", "M", "B"}


def test_historial_y_navegacion_heredada_con_sesion(seguridad, repositorio, raiz_tk, monkeypatch):
    s, sesion = seguridad
    cargar_demo(repositorio)
    r = s.repositorio(sesion)
    app = AplicacionPacientes(raiz_tk, r, modo="signos")
    app.refrescar(r.listar_pacientes()[0]["id"])
    ventana = app.signos()
    assert ventana is not None
    ventana.destroy()
    alta(s, sesion, "administrativo", "administrativo")
    app.repositorio = s.repositorio(s.autenticar("administrativo", "ClaveTest123"))
    errores = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *a, **k: errores.append(a))
    assert app.signos() is None
    assert app.abrir_modulo("maestras") is None
    assert len(errores) == 2
