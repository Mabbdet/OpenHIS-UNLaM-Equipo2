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
