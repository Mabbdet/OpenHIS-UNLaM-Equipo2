import pytest

from datos import ErrorValidacion, PacienteNoEncontrado, Repositorio


def test_modificacion_persiste(repositorio, datos_paciente):
    paciente_id = repositorio.registrar_paciente(datos_paciente)
    contacto = {"telefono": "555-0199", "email": "nuevo@example.com", "domicilio": "Otro domicilio", "obra_social": "Otra cobertura"}
    repositorio.modificar_paciente(paciente_id, contacto)
    paciente = Repositorio(repositorio.ruta).buscar_paciente(datos_paciente["dni"])
    assert all(paciente[campo] == valor for campo, valor in contacto.items())
    assert paciente["nombre"] == datos_paciente["nombre"]
    assert paciente["id"] == paciente_id


def test_registra_signos_con_fecha_y_paciente(repositorio, datos_paciente):
    paciente_id = repositorio.registrar_paciente(datos_paciente)
    registro_id = repositorio.registrar_signos(paciente_id, {
        "presion_sistolica": "120", "presion_diastolica": "80", "frecuencia_cardiaca": "72",
        "temperatura": "36,5", "saturacion_oxigeno": "98", "motivo_consulta": "Consulta de prueba",
    })
    registro = repositorio.historial_signos(paciente_id)[0]
    assert registro["id"] == registro_id
    assert registro["paciente_id"] == paciente_id
    assert registro["fecha_hora"]
    assert registro["temperatura"] == 36.5
    assert registro["presion_sistolica"] == 120
    assert registro["motivo_consulta"] == "Consulta de prueba"


@pytest.mark.parametrize("entrada", [
    {"motivo_consulta": " "},
    {"motivo_consulta": "Prueba", "frecuencia_cardiaca": "texto"},
    {"motivo_consulta": "Prueba", "temperatura": "nan"},
])
def test_rechaza_signos_invalidos(repositorio, datos_paciente, entrada):
    paciente_id = repositorio.registrar_paciente(datos_paciente)
    with pytest.raises(ErrorValidacion):
        repositorio.registrar_signos(paciente_id, entrada)
    assert repositorio.historial_signos(paciente_id) == []


def test_historial_muestra_ultimos_diez(repositorio, datos_paciente):
    paciente_id = repositorio.registrar_paciente(datos_paciente)
    registros = [repositorio.registrar_signos(paciente_id, {"motivo_consulta": f"Registro {i}"}) for i in range(12)]
    historial = repositorio.historial_signos(paciente_id)
    assert [registro["id"] for registro in historial] == list(reversed(registros[-10:]))


def test_eliminar_paciente_elimina_solo_sus_signos(repositorio, datos_paciente):
    paciente_id = repositorio.registrar_paciente(datos_paciente)
    otro_id = repositorio.registrar_paciente({**datos_paciente, "dni": "30111223"})
    repositorio.registrar_signos(paciente_id, {"motivo_consulta": "Consulta A"})
    repositorio.registrar_signos(otro_id, {"motivo_consulta": "Consulta B"})
    assert repositorio.eliminar_paciente(paciente_id) == 1
    assert repositorio.buscar_paciente(datos_paciente["dni"]) is None
    assert len(repositorio.historial_signos(otro_id)) == 1
    with repositorio.conectar() as conexion:
        assert conexion.execute("SELECT COUNT(*) FROM SignosVitales WHERE paciente_id=?", (paciente_id,)).fetchone()[0] == 0


def test_no_registra_signos_sin_paciente(repositorio):
    with pytest.raises(PacienteNoEncontrado):
        repositorio.registrar_signos(999, {"motivo_consulta": "Consulta"})
