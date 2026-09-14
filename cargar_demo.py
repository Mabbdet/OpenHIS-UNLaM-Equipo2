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
    profesionales = cargar_catalogos_profesionales(repositorio)
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
                "medico_id": profesionales[indice],
            })
        elif indice < 3:
            for registro in repositorio.historial_signos(paciente_id):
                # Solo se completa la autoría de la medición sintética creada por esta demo.
                if registro["medico_id"] is None and registro["motivo_consulta"] == "Consulta ficticia para demostración académica":
                    repositorio.asignar_profesional_signos(registro["id"], profesionales[indice])
    cargar_prescripciones_demo(repositorio, profesionales)
    return creados


def cargar_catalogos_profesionales(repositorio):
    especialidades = ("Clínica médica", "Cardiología", "Pediatría", "Dermatología", "Neurología")
    profesionales = []
    for indice, especialidad in enumerate(especialidades, start=1):
        codigo = f"DEMO-ESP-{indice}"
        existentes = {fila["codigo"]: fila for fila in repositorio.listar_catalogo("especialidades")}
        especialidad_id = existentes[codigo]["id"] if codigo in existentes else repositorio.guardar_catalogo("especialidades", {
            "codigo": codigo, "nombre": especialidad, "descripcion": "Especialidad de demostración académica",
        })
        dni = f"2900000{indice}"
        profesional = repositorio.buscar_profesional(dni)
        if profesional and profesional["matricula"] != f"DEMO-MAT-{indice}":
            raise ValueError(f"El DNI demo {dni} está ocupado por otra ficha; no se modificaron sus datos.")
        if profesional is None:
            profesional_id = repositorio.registrar_profesional({
                "dni": dni, "nombre": ("Lucía", "Martín", "Sofía", "Diego", "Elena")[indice-1],
                "apellido": "Demo", "fecha_nacimiento": "1985-01-15", "sexo": "M" if indice in (2, 4) else "F",
                "matricula": f"DEMO-MAT-{indice}", "especialidad_id": especialidad_id,
                "telefono": f"555-020{indice}", "email": f"profesional{indice}@example.com",
            })
        else:
            profesional_id = profesional["id"]
        profesionales.append(profesional_id)
    # Los identificadores DEMO son locales y explícitamente ficticios, no códigos SNOMED oficiales.
    snomed = {fila["codigo"] for fila in repositorio.listar_catalogo("snomed")}
    if "DEMO-SN-1" not in snomed:
        repositorio.guardar_catalogo("snomed", {"codigo": "DEMO-SN-1", "termino": "Concepto ficticio de prueba", "categoria": "Demostración", "descripcion": "No representa un código SNOMED CT oficial"})
    farmacos = {fila["codigo"] for fila in repositorio.listar_catalogo("farmacos")}
    for indice in range(1, 6):
        codigo = f"DEMO-FAR-{indice}"
        if codigo not in farmacos:
            repositorio.guardar_catalogo("farmacos", {"codigo": codigo, "nombre": f"Fármaco ficticio {indice}",
                "principio_activo": "Sustancia de demostración", "presentacion": "Presentación ficticia",
                "concentracion": "Dato de prueba", "via_administracion": "Vía de prueba"})
    return profesionales


def cargar_prescripciones_demo(repositorio, profesionales):
    existentes = {fila["indicaciones"] for fila in repositorio.listar_prescripciones()}
    farmacos = {fila["codigo"]: fila["id"] for fila in repositorio.listar_catalogo("farmacos", solo_activos=True)}
    snomed = next(fila["id"] for fila in repositorio.listar_catalogo("snomed") if fila["codigo"] == "DEMO-SN-1")
    for indice, paciente in enumerate(PACIENTES_DEMO, start=1):
        ficha = repositorio.buscar_paciente(paciente[0])
        marca = f"DEMO-PRES-{indice}: registro ficticio sin uso clínico"
        if marca not in existentes and ficha and ficha["nombre"] == paciente[1] and ficha["apellido"] == paciente[2]:
            repositorio.registrar_prescripcion({"paciente_id": ficha["id"], "profesional_id": profesionales[indice-1],
                "farmaco_id": farmacos[f"DEMO-FAR-{indice}"], "snomed_id": snomed,
                "dosis": "Dosis de prueba", "via_administracion": "Vía de prueba", "frecuencia": "Frecuencia de prueba",
                "duracion": "Duración de prueba", "cantidad": 1, "indicaciones": marca})


if __name__ == "__main__":
    repositorio = Repositorio()
    cantidad = cargar_demo(repositorio)
    print(f"Pacientes ficticios creados: {cantidad}\nBase de datos: {repositorio.ruta}")
