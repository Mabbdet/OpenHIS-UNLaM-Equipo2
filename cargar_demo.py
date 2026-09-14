"""Carga inicial reproducible de datos ficticios; no reemplaza pacientes existentes."""

from datos import Repositorio


PACIENTES_DEMO = (
    ("40123456", "María", "González", "1997-04-12", "F"),
    ("41123456", "Juan", "Pérez", "1998-06-23", "M"),
    ("42123456", "Ana", "López", "1999-02-18", "F"),
    ("43123456", "Pedro", "Martínez", "2000-10-09", "M"),
    ("44123456", "Laura", "Fernández", "2001-08-15", "F"),
)


def cargar_demo(repositorio):
    creados = 0
    for indice, (dni, nombre, apellido, nacimiento, sexo) in enumerate(PACIENTES_DEMO):
        datos = {
            "dni": dni, "nombre": nombre, "apellido": apellido,
            "fecha_nacimiento": nacimiento, "sexo": sexo,
            "telefono": f"555-010{indice}", "email": f"paciente{indice + 1}@example.com",
            "domicilio": f"Calle Ficticia {100 + indice}", "obra_social": "Cobertura de demostración",
        }
        existente = repositorio.buscar_paciente(dni)
        if existente:
            # Completar signos solo para una ficha que coincide con la demo propia.
            if any(existente[campo] != valor for campo, valor in datos.items()):
                continue
            paciente_id = existente["id"]
        else:
            paciente_id = repositorio.registrar_paciente(datos)
            creados += 1
        if indice < 3 and not repositorio.historial_signos(paciente_id):
            repositorio.registrar_signos(paciente_id, {
                "presion_sistolica": 120, "presion_diastolica": 80,
                "frecuencia_cardiaca": 72 + indice, "temperatura": "36,5",
                "saturacion_oxigeno": 98, "motivo_consulta": "Consulta ficticia para demostración académica",
            })
    return creados


if __name__ == "__main__":
    repositorio = Repositorio()
    cantidad = cargar_demo(repositorio)
    print(f"Pacientes ficticios creados: {cantidad}\nBase de datos: {repositorio.ruta}")
