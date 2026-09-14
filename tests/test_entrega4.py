import sqlite3
import tkinter as tk

import pytest

from cargar_demo import cargar_demo
from datos import DNIDuplicado, ErrorValidacion, Repositorio
from ventanas_clinicas import TablasMaestrasApp, ProfesionalesApp, PrescripcionesApp
from interfaz import AplicacionPacientes


def test_especialidad_alta_modificacion_desactivacion(repositorio):
    especialidad = repositorio.guardar_catalogo("especialidades", {"codigo": "CLI", "nombre": "Clínica"})
    repositorio.guardar_catalogo("especialidades", {"codigo": "CLI", "nombre": "Clínica médica", "descripcion": "Nueva descripción"}, especialidad)
    assert repositorio.listar_catalogo("especialidades")[0]["nombre"] == "Clínica médica"
    repositorio.desactivar_especialidad(especialidad)
    assert repositorio.listar_catalogo("especialidades", solo_activos=True) == []
    assert repositorio.listar_catalogo("especialidades")[0]["activo"] == 0


@pytest.mark.parametrize("catalogo,datos", [
    ("especialidades", {"codigo": "TEST", "nombre": "Prueba"}),
    ("snomed", {"codigo": "TEST", "termino": "Concepto de prueba"}),
    ("farmacos", {"codigo": "TEST", "nombre": "Fármaco de prueba"}),
])
def test_catalogos_rechazan_codigo_duplicado(repositorio, catalogo, datos):
    repositorio.guardar_catalogo(catalogo, datos)
    with pytest.raises(ErrorValidacion, match="código"):
        repositorio.guardar_catalogo(catalogo, datos)


def test_busqueda_snomed_por_termino(repositorio):
    repositorio.guardar_catalogo("snomed", {"codigo": "LOCAL-1", "termino": "Concepto de prueba"})
    assert len(repositorio.listar_catalogo("snomed", "PRUEBA")) == 1
    assert repositorio.listar_catalogo("snomed", "inexistente") == []


def test_profesional_alta_busqueda_modificacion_y_baja(repositorio, profesional):
    ficha = repositorio.buscar_profesional("20111222")
    assert ficha["id"] == profesional
    assert ficha["especialidad"] == "Especialidad de prueba"
    otra = repositorio.guardar_catalogo("especialidades", {"codigo": "OTRA", "nombre": "Otra especialidad"})
    repositorio.modificar_profesional(profesional, {"telefono": "555-0101", "email": "nuevo@example.com", "especialidad_id": otra})
    ficha = Repositorio(repositorio.ruta).buscar_profesional("20111222")
    assert ficha["telefono"] == "555-0101" and ficha["especialidad_id"] == otra
    repositorio.eliminar_profesional(profesional)
    assert repositorio.buscar_profesional("20111222") is None


@pytest.mark.parametrize("cambio,mensaje", [({"matricula": "OTRA"}, "DNI"), ({"dni": "20111223"}, "matrícula")])
def test_profesional_identificadores_unicos(repositorio, profesional, cambio, mensaje):
    ficha = repositorio.buscar_profesional("20111222")
    with pytest.raises(ErrorValidacion, match=mensaje):
        repositorio.registrar_profesional({**ficha, **cambio})


def test_especialidad_inactiva_no_admite_nuevo_profesional(repositorio, profesional):
    ficha = repositorio.buscar_profesional("20111222")
    repositorio.desactivar_especialidad(ficha["especialidad_id"])
    with pytest.raises(ErrorValidacion, match="activa"):
        repositorio.registrar_profesional({**ficha, "dni": "20111223", "matricula": "OTRA"})
    repositorio.modificar_profesional(profesional, {**ficha, "telefono": "555-0100"})
    assert repositorio.buscar_profesional(ficha["dni"])["telefono"] == "555-0100"


@pytest.mark.parametrize("medico", [None, "", 9999])
def test_signos_requieren_profesional_existente(repositorio, datos_paciente, medico):
    paciente = repositorio.registrar_paciente(datos_paciente)
    with pytest.raises(ErrorValidacion, match="profesional"):
        repositorio.registrar_signos(paciente, {"motivo_consulta": "Prueba", "medico_id": medico})
    with repositorio.conectar() as conexion:
        with pytest.raises(sqlite3.IntegrityError):
            conexion.execute("INSERT INTO SignosVitales(paciente_id,medico_id) VALUES (?,?)", (paciente, medico or None))


def test_profesional_con_signos_no_se_elimina(repositorio, datos_paciente, profesional):
    paciente = repositorio.registrar_paciente(datos_paciente)
    repositorio.registrar_signos(paciente, {"medico_id": profesional, "motivo_consulta": "Prueba"})
    with pytest.raises(ErrorValidacion, match="no puede eliminarse"):
        repositorio.eliminar_profesional(profesional)
    assert repositorio.historial_signos(paciente)[0]["medico_id"] == profesional


@pytest.fixture
def prescripcion(repositorio, datos_paciente, profesional):
    paciente = repositorio.registrar_paciente(datos_paciente)
    farmaco = repositorio.guardar_catalogo("farmacos", {"codigo": "FIC-1", "nombre": "Fármaco ficticio"})
    return {"paciente_id": paciente, "profesional_id": profesional, "farmaco_id": farmaco,
            "dosis": "Prueba", "via_administracion": "Prueba", "frecuencia": "Prueba", "cantidad": "1"}


def test_prescripcion_alta_detalle_busqueda_anulacion(repositorio, prescripcion):
    registro_id = repositorio.registrar_prescripcion(prescripcion)
    detalle = repositorio.obtener_prescripcion(registro_id)
    assert detalle["paciente"] == "Ana Prueba" and detalle["farmaco"] == "Fármaco ficticio"
    assert detalle["snomed_id"] is None
    assert len(repositorio.listar_prescripciones(prescripcion["paciente_id"])) == 1
    assert repositorio.listar_prescripciones(9999) == []
    repositorio.anular_prescripcion(registro_id)
    assert repositorio.obtener_prescripcion(registro_id)["activo"] == 0
    assert len(repositorio.listar_prescripciones()) == 1


@pytest.mark.parametrize("campo,valor", [("paciente_id",999), ("profesional_id",999), ("farmaco_id",999), ("snomed_id",999), ("dosis"," "), ("cantidad","-1"), ("fecha_inicio","2026-02-30")])
def test_prescripcion_rechaza_datos_invalidos(repositorio, prescripcion, campo, valor):
    with pytest.raises(ErrorValidacion):
        repositorio.registrar_prescripcion({**prescripcion, campo: valor})
    assert repositorio.listar_prescripciones() == []


def test_prescripciones_conservan_paciente_y_profesional(repositorio, prescripcion):
    registro_id = repositorio.registrar_prescripcion(prescripcion)
    repositorio.anular_prescripcion(registro_id)
    with pytest.raises(ErrorValidacion):
        repositorio.eliminar_paciente(prescripcion["paciente_id"])
    with pytest.raises(ErrorValidacion):
        repositorio.eliminar_profesional(prescripcion["profesional_id"])
    assert repositorio.obtener_prescripcion(registro_id)["activo"] == 0


def test_demo_repetible_con_datos_minimos(repositorio):
    cargar_demo(repositorio)
    cargar_demo(repositorio)
    assert len(repositorio.listar_profesionales()) == 5
    assert len({p["especialidad_id"] for p in repositorio.listar_profesionales()}) == 5
    assert len(repositorio.listar_prescripciones()) == 5
    with repositorio.conectar() as conexion:
        assert conexion.execute("SELECT COUNT(*) FROM SignosVitales WHERE medico_id IS NULL").fetchone()[0] == 0
        assert conexion.execute("PRAGMA foreign_key_check").fetchall() == []


def test_migracion_conserva_signos_historicos(repositorio, datos_paciente, profesional):
    paciente = repositorio.registrar_paciente(datos_paciente)
    with repositorio.conectar() as conexion:
        conexion.execute("DROP TABLE SignosVitales")
        conexion.execute("""CREATE TABLE SignosVitales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER NOT NULL,
            fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP, presion_sistolica INTEGER,
            presion_diastolica INTEGER, frecuencia_cardiaca INTEGER, temperatura REAL,
            saturacion_oxigeno INTEGER, motivo_consulta TEXT, medico_id INTEGER,
            FOREIGN KEY(paciente_id) REFERENCES Pacientes(id))""")
        conexion.execute("INSERT INTO SignosVitales(id,paciente_id,motivo_consulta) VALUES (7,?,'Histórico sin autor')", (paciente,))
    migrado = Repositorio(repositorio.ruta)
    registro = migrado.historial_signos(paciente)[0]
    assert registro["id"] == 7 and registro["medico_id"] is None
    migrado.asignar_profesional_signos(7, profesional)
    assert migrado.historial_signos(paciente)[0]["medico_id"] == profesional
    assert migrado.registrar_signos(paciente, {"motivo_consulta": "Nuevo", "medico_id": profesional}) > 7
    with migrado.conectar() as conexion:
        assert conexion.execute("PRAGMA foreign_key_check").fetchall() == []


@pytest.mark.parametrize("clase", [TablasMaestrasApp, ProfesionalesApp, PrescripcionesApp])
def test_nuevas_ventanas_cargan(repositorio, clase):
    try:
        raiz = tk.Tk()
    except tk.TclError as error:
        pytest.skip(str(error))
    raiz.withdraw()
    try:
        cargar_demo(repositorio)
        app = clase(raiz, repositorio)
        raiz.update_idletasks()
        assert app.raiz.winfo_exists()
        assert "OpenHIS" in raiz.title()
    finally:
        raiz.destroy()


def test_formulario_signos_exige_y_guarda_profesional(repositorio, datos_paciente, profesional, monkeypatch):
    errores = []
    monkeypatch.setattr('interfaz.messagebox.showerror', lambda *args, **kwargs: errores.append(args))
    monkeypatch.setattr('interfaz.messagebox.showinfo', lambda *args, **kwargs: None)
    try:
        raiz = tk.Tk()
    except tk.TclError as error:
        pytest.skip(str(error))
    raiz.withdraw()
    try:
        paciente = repositorio.registrar_paciente(datos_paciente)
        app = AplicacionPacientes(raiz, repositorio)
        app.refrescar(paciente)
        ventana = app.signos()
        ventana.motivo.insert('1.0', 'Prueba GUI con profesional')
        ventana.guardar()
        assert len(errores) == 1
        assert repositorio.historial_signos(paciente) == []
        ventana.medico.set(ventana.profesionales[profesional])
        ventana.guardar()
        assert repositorio.historial_signos(paciente)[0]['medico_id'] == profesional
        assert len(ventana.historial.get_children()) == 1
    finally:
        raiz.destroy()
