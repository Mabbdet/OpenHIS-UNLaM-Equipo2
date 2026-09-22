from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from cargar_demo import cargar_demo
from datos import ErrorValidacion, Repositorio
from exportaciones import ESPACIO_XML, exportar_prescripcion
from interfaz import AplicacionPacientes
from menu_app import MenuApp
from signos_app import SignosApp
from ventanas_clinicas import ProfesionalesApp, PrescripcionesApp


@pytest.fixture
def caso(repositorio, datos_paciente, profesional):
    paciente = repositorio.registrar_paciente(datos_paciente)
    farmaco = repositorio.guardar_catalogo("farmacos", {"codigo": "E5", "nombre": "Fármaco <ficticio> & prueba"})
    datos = {"paciente_id": paciente, "profesional_id": profesional, "farmaco_id": farmaco,
             "dosis": "Prueba", "via_administracion": "Prueba", "frecuencia": "Prueba",
             "indicaciones": '<script>alert("prueba")</script> & áéíóú'}
    receta = repositorio.registrar_prescripcion(datos)
    signo = repositorio.registrar_signos(paciente, {"medico_id": profesional, "motivo_consulta": "Prueba"})
    return {"paciente": paciente, "profesional": profesional, "signo": signo, "prescripcion": receta, "datos": datos}


@pytest.mark.parametrize("tipo,baja,alta,consulta", [
    ("paciente", "dar_baja_paciente", "reactivar_paciente", "obtener_paciente"),
    ("profesional", "dar_baja_profesional", "reactivar_profesional", None),
    ("signo", "anular_signo", "reactivar_signo", "obtener_signo"),
    ("prescripcion", "anular_prescripcion", "reactivar_prescripcion", "obtener_prescripcion"),
])
def test_ciclo_reversible_sin_perder_datos(repositorio, caso, tipo, baja, alta, consulta):
    def ficha():
        return getattr(repositorio, consulta)(caso[tipo]) if consulta else repositorio.buscar_profesional("20111222")
    inicial = ficha()
    getattr(repositorio, baja)(caso[tipo])
    assert ficha() == {**inicial, "activo": 0}
    with pytest.raises(ErrorValidacion, match="ya estaba"):
        getattr(repositorio, baja)(caso[tipo])
    getattr(repositorio, alta)(caso[tipo])
    assert ficha() == inicial
    with pytest.raises(ErrorValidacion, match="ya estaba"):
        getattr(repositorio, alta)(caso[tipo])
    with pytest.raises(ErrorValidacion, match="no existe"):
        getattr(repositorio, alta)(99999)


def test_bajas_sin_cascada_y_reactivacion_historica(repositorio, caso):
    repositorio.dar_baja_paciente(caso["paciente"])
    repositorio.dar_baja_profesional(caso["profesional"])
    assert repositorio.obtener_signo(caso["signo"])["activo"] == 1
    assert repositorio.obtener_prescripcion(caso["prescripcion"])["activo"] == 1
    repositorio.anular_signo(caso["signo"])
    repositorio.anular_prescripcion(caso["prescripcion"])
    repositorio.reactivar_signo(caso["signo"])
    repositorio.reactivar_prescripcion(caso["prescripcion"])
    assert repositorio.obtener_signo(caso["signo"])["paciente_activo"] == 0
    assert repositorio.obtener_prescripcion(caso["prescripcion"])["profesional_activo"] == 0
    repositorio.anular_signo(caso["signo"])
    repositorio.anular_prescripcion(caso["prescripcion"])
    repositorio.reactivar_paciente(caso["paciente"])
    repositorio.reactivar_profesional(caso["profesional"])
    assert repositorio.obtener_signo(caso["signo"])["activo"] == 0
    assert repositorio.obtener_prescripcion(caso["prescripcion"])["activo"] == 0


@pytest.mark.parametrize("tipo", ["paciente", "profesional"])
def test_rechaza_intervenciones_nuevas_de_inactivos(repositorio, caso, tipo):
    getattr(repositorio, f"dar_baja_{tipo}")(caso[tipo])
    with pytest.raises(ErrorValidacion, match="inactivo"):
        repositorio.registrar_prescripcion(caso["datos"])
    with pytest.raises(ErrorValidacion, match="inactivo"):
        repositorio.registrar_signos(caso["paciente"], {"medico_id": caso["profesional"], "motivo_consulta": "Prueba"})
    assert len(repositorio.listar_signos(activos=None)) == 1
    assert len(repositorio.listar_prescripciones(activos=None)) == 1


def test_consultas_inactivos_y_unicidad(repositorio, caso, datos_paciente):
    repositorio.dar_baja_paciente(caso["paciente"])
    repositorio.dar_baja_profesional(caso["profesional"])
    repositorio.anular_signo(caso["signo"])
    repositorio.anular_prescripcion(caso["prescripcion"])
    for metodo in (repositorio.listar_pacientes, repositorio.listar_profesionales, repositorio.listar_signos, repositorio.listar_prescripciones):
        assert metodo(activos=True) == []
        assert len(metodo(activos=False)) == len(metodo(activos=None)) == 1
    assert repositorio.buscar_paciente(datos_paciente["dni"])["id"] == caso["paciente"]
    with pytest.raises(ErrorValidacion, match="DNI"):
        repositorio.registrar_paciente(datos_paciente)
    profesional = repositorio.buscar_profesional("20111222")
    with pytest.raises(ErrorValidacion, match="DNI"):
        repositorio.registrar_profesional({**profesional, "matricula": "OTRA"})
    with pytest.raises(ErrorValidacion, match="matrícula"):
        repositorio.registrar_profesional({**profesional, "dni": "20111223"})


def test_migracion_e4_y_repeticion_preservan_estados(repositorio, caso):
    repositorio.anular_prescripcion(caso["prescripcion"])
    with repositorio.conectar() as c:
        for tabla in ("Pacientes", "Profesionales", "SignosVitales"):
            for fila in c.execute("SELECT name,sql FROM sqlite_master WHERE type='index' AND tbl_name=?", (tabla,)).fetchall():
                if fila["sql"] and "activo" in fila["sql"]:
                    c.execute(f'DROP INDEX "{fila["name"]}"')
            c.execute(f"ALTER TABLE {tabla} DROP COLUMN activo")
    migrado = Repositorio(repositorio.ruta)
    assert migrado.obtener_paciente(caso["paciente"])["activo"] == 1
    migrado.dar_baja_paciente(caso["paciente"])
    migrado.dar_baja_profesional(caso["profesional"])
    migrado.anular_signo(caso["signo"])
    esperado = migrado.obtener_prescripcion(caso["prescripcion"])
    otra = Repositorio(repositorio.ruta)
    assert otra.obtener_prescripcion(caso["prescripcion"]) == esperado
    assert otra.obtener_signo(caso["signo"])["activo"] == 0
    with otra.conectar() as c:
        assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert c.execute("PRAGMA foreign_key_check").fetchall() == []


@pytest.mark.parametrize("diagnostico", [False, True])
def test_exportacion_xml_html_y_estados(repositorio, caso, tmp_path, diagnostico):
    datos = caso["datos"]
    if diagnostico:
        datos = {**datos, "snomed_id": repositorio.guardar_catalogo("snomed", {"codigo": "LOCAL", "termino": "Concepto & prueba"})}
    receta = repositorio.registrar_prescripcion(datos)
    for estado in (1, 0):
        if not estado:
            repositorio.anular_prescripcion(receta)
        ruta, xml = exportar_prescripcion(repositorio, receta, "xml", tmp_path)
        raiz = ET.fromstring(ruta.read_text(encoding="utf-8"))
        assert raiz.tag == f"{{{ESPACIO_XML}}}Prescription"
        ns = {"r": ESPACIO_XML}
        assert raiz.findtext("r:Metadata/r:Estado", namespaces=ns) == ("Activa" if estado else "Anulada")
        assert raiz.findtext("r:Dosage/r:Indicaciones", namespaces=ns) == datos["indicaciones"]
        assert (raiz.find("r:Condition", ns) is not None) == diagnostico
        ruta_html, html = exportar_prescripcion(repositorio, receta, "html", tmp_path)
        assert ruta_html.read_text(encoding="utf-8") == html
        assert "<script>" not in html and "&lt;script&gt;" in html
        assert ("ACTIVA" if estado else "ANULADA") in html
        otra, _ = exportar_prescripcion(repositorio, receta, "xml", tmp_path)
        assert otra != ruta and ruta.read_text(encoding="utf-8") == xml


def test_error_de_escritura_conserva_prescripcion(repositorio, caso, tmp_path):
    (tmp_path / "recetas").write_text("No es un directorio", encoding="utf-8")
    with pytest.raises(OSError):
        exportar_prescripcion(repositorio, caso["prescripcion"], "xml", tmp_path)
    assert repositorio.obtener_prescripcion(caso["prescripcion"])["activo"] == 1


def test_demo_no_recrea_registros_anulados(repositorio):
    cargar_demo(repositorio)
    receta = repositorio.listar_prescripciones()[0]
    repositorio.anular_prescripcion(receta["id"])
    repositorio.dar_baja_paciente(receta["paciente_id"])
    cargar_demo(repositorio)
    assert len(repositorio.listar_prescripciones(activos=None)) == 5
    assert repositorio.obtener_prescripcion(receta["id"])["activo"] == 0
    assert repositorio.obtener_paciente(receta["paciente_id"])["activo"] == 0


@pytest.mark.parametrize("tipo", ["paciente", "profesional", "signo", "prescripcion"])
def test_flujo_gui_alta_baja_reactivacion(repositorio, caso, datos_paciente, raiz_tk, monkeypatch, tipo):
    errores = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *a, **k: errores.append(a))
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *a, **k: None)
    monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *a, **k: True)
    clases = {"paciente": lambda r, repo: AplicacionPacientes(r, repo, modo="crud"),
              "profesional": ProfesionalesApp, "signo": SignosApp, "prescripcion": PrescripcionesApp}
    app = clases[tipo](raiz_tk, repositorio)
    formulario = app.registrar()
    valores = {**datos_paciente, "dni": "30111999", "matricula": "GUI-999", "motivo_consulta": "Prueba GUI", **caso["datos"]}
    valores["especialidad_id"] = repositorio.buscar_profesional("20111222")["especialidad_id"]
    for campo, variable in formulario.campos.items():
        opciones = getattr(formulario, "opciones", {}).get(campo)
        variable.set(opciones.get(valores.get(campo), next(iter(opciones.values()), "")) if opciones else valores.get(campo, ""))
    formulario.guardar()
    assert errores == []
    registro_id = int(app.tabla.selection()[0])
    (app.eliminar if tipo in ("paciente", "profesional") else app.anular)()
    app.reactivar()
    assert errores == []
    if tipo == "paciente":
        assert repositorio.obtener_paciente(registro_id)["activo"] == 1
    elif tipo == "profesional":
        assert repositorio.buscar_profesional("30111999")["activo"] == 1
    else:
        consulta = repositorio.obtener_signo if tipo == "signo" else repositorio.obtener_prescripcion
        assert consulta(registro_id)["activo"] == 1


def test_menu_abre_modulos_independientes(repositorio, raiz_tk):
    menu = MenuApp(raiz_tk, repositorio)
    for nombre in ("Pacientes", "Profesionales", "Signos vitales", "Prescripciones", "Tablas maestras"):
        app = menu.abrir(nombre)
        assert app.repositorio is repositorio
        assert app.raiz.winfo_exists()
        assert menu.abrir(nombre) is app
        app.raiz.destroy()
