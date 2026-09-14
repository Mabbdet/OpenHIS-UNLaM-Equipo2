import pytest

from datos import DNIDuplicado, ErrorValidacion, Repositorio


def test_registrar_y_buscar_paciente(repositorio, datos_paciente):
    historia_clinica = repositorio.registrar_paciente(datos_paciente)
    paciente = repositorio.buscar_paciente(datos_paciente["dni"])
    assert paciente["id"] == historia_clinica
    assert paciente["fecha_registro"]
    for campo, valor in datos_paciente.items():
        assert paciente[campo] == valor


def test_rechaza_dni_duplicado(repositorio, datos_paciente):
    repositorio.registrar_paciente(datos_paciente)
    with pytest.raises(DNIDuplicado, match="Ya existe un paciente"):
        repositorio.registrar_paciente(datos_paciente)
    with repositorio.conectar() as conexion:
        assert conexion.execute("SELECT COUNT(*) FROM Pacientes").fetchone()[0] == 1


def test_busqueda_inexistente(repositorio):
    assert repositorio.buscar_paciente("99999999") is None


@pytest.mark.parametrize("campo", ["dni", "nombre", "apellido", "fecha_nacimiento", "sexo"])
def test_rechaza_campo_obligatorio_vacio(repositorio, datos_paciente, campo):
    datos_paciente[campo] = " "
    with pytest.raises(ErrorValidacion):
        repositorio.registrar_paciente(datos_paciente)
    with repositorio.conectar() as conexion:
        assert conexion.execute("SELECT COUNT(*) FROM Pacientes").fetchone()[0] == 0


def test_persistencia_e_identificadores_unicos(repositorio, datos_paciente):
    primer_id = repositorio.registrar_paciente(datos_paciente)
    otra_conexion = Repositorio(repositorio.ruta)
    assert otra_conexion.buscar_paciente(datos_paciente["dni"])["id"] == primer_id
    datos_paciente["dni"] = "30111223"
    assert otra_conexion.registrar_paciente(datos_paciente) > primer_id
