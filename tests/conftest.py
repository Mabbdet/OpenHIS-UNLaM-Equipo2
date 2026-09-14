import pytest

from datos import Repositorio


@pytest.fixture
def repositorio(tmp_path):
    return Repositorio(tmp_path / "Salud.db")


@pytest.fixture
def datos_paciente():
    return {
        "dni": "30111222", "nombre": "Ana", "apellido": "Prueba",
        "fecha_nacimiento": "1990-05-12", "sexo": "F",
        "telefono": "555-0100", "email": "ana@example.com",
        "domicilio": "Calle Ficticia 123", "obra_social": "Cobertura ficticia",
    }


@pytest.fixture
def profesional(repositorio):
    especialidad_id = repositorio.guardar_catalogo("especialidades", {"codigo": "ESP-TEST", "nombre": "Especialidad de prueba"})
    return repositorio.registrar_profesional({
        "dni": "20111222", "nombre": "Profesional", "apellido": "Prueba",
        "fecha_nacimiento": "1980-01-01", "sexo": "M", "matricula": "TEST-123",
        "especialidad_id": especialidad_id,
    })
