"""Receta XML académica y reporte HTML local. No implementa FHIR ni firma digital."""

from datetime import datetime
from html import escape
from pathlib import Path
from uuid import uuid4
import xml.etree.ElementTree as ET


RAIZ = Path(__file__).resolve().parent
ESPACIO_XML = "http://openhis.unlam.edu.ar/fhir"
AVISO = "Demostración académica. Documento sin validación para uso clínico."


def texto(valor):
    return "" if valor is None else str(valor)


def crear_xml(ficha):
    raiz = ET.Element("Prescription", xmlns=ESPACIO_XML, version="1.0")
    secciones = {
        "Metadata": {"PrescriptionID": ficha["id"], "FechaGeneracion": datetime.now().astimezone().isoformat(),
                     "SistemaEmisor": "OpenHIS-UNLaM", "Hospital": "Hospital Universitario San Justo",
                     "Estado": "Activa" if ficha["activo"] else "Anulada"},
        "Patient": {"ID": ficha["paciente_id"], "DNI": ficha["paciente_dni"], "Nombre": ficha["paciente_nombre"],
                    "Apellido": ficha["paciente_apellido"], "FechaNacimiento": ficha["paciente_fecha_nac"],
                    "Sexo": ficha["paciente_sexo"], "Telefono": ficha["paciente_telefono"], "Email": ficha["paciente_email"],
                    "Domicilio": ficha["paciente_domicilio"], "ObraSocial": ficha["paciente_obra_social"]},
        "Practitioner": {"ID": ficha["profesional_id"], "DNI": ficha["profesional_dni"], "Nombre": ficha["profesional_nombre"],
                         "Apellido": ficha["profesional_apellido"], "Matricula": ficha["matricula"],
                         "Especialidad": ficha["especialidad"], "Email": ficha["profesional_email"]},
        "Medication": {"ID": ficha["farmaco_id"], "Codigo": ficha["farmaco_codigo"], "Nombre": ficha["farmaco"],
                       "PrincipioActivo": ficha["farmaco_principio"], "Presentacion": ficha["farmaco_presentacion"],
                       "Concentracion": ficha["farmaco_concentracion"]},
    }
    if ficha["snomed_id"] is not None:
        secciones["Condition"] = {"CodigoSNOMED": ficha["snomed_codigo"], "Termino": ficha["snomed"]}
    secciones["Dosage"] = {"Dosis": ficha["dosis"], "ViaAdministracion": ficha["via_administracion"],
                           "Frecuencia": ficha["frecuencia"], "Duracion": ficha["duracion"], "Cantidad": ficha["cantidad"],
                           "FechaInicio": ficha["fecha_inicio"], "FechaFin": ficha["fecha_fin"], "Indicaciones": ficha["indicaciones"]}
    secciones["AdministrativeData"] = {"FechaPrescripcion": ficha["fecha_prescripcion"] + "Z",
                                       "Estado": "Activa" if ficha["activo"] else "Anulada"}
    for nombre, valores in secciones.items():
        nodo = ET.SubElement(raiz, nombre)
        for etiqueta, valor in valores.items():
            ET.SubElement(nodo, etiqueta).text = texto(valor)
    raiz.insert(0, ET.Comment(AVISO + " Formato propio de la cátedra; no es HL7 FHIR."))
    ET.indent(raiz, space="  ")
    return ET.tostring(raiz, encoding="utf-8", xml_declaration=True).decode("utf-8")


def crear_html(ficha):
    def seccion(titulo, campos):
        filas = "".join(f"<dt>{escape(etiqueta)}</dt><dd>{escape(texto(valor)) if valor is not None and valor != '' else 'Sin informar'}</dd>" for etiqueta, valor in campos)
        return f"<section><h2>{escape(titulo)}</h2><dl>{filas}</dl></section>"

    cuerpo = seccion("Paciente", [("HC / DNI", f"{ficha['paciente_id']} / {ficha['paciente_dni']}"),
        ("Nombre", ficha["paciente"]), ("Nacimiento", ficha["paciente_fecha_nac"]), ("Sexo", ficha["paciente_sexo"]),
        ("Domicilio", ficha["paciente_domicilio"]), ("Obra social", ficha["paciente_obra_social"]),
        ("Teléfono", ficha["paciente_telefono"]), ("Email", ficha["paciente_email"]),
        ("Estado de la ficha", "Activo" if ficha["paciente_activo"] else "Inactivo")])
    cuerpo += seccion("Profesional", [("Nombre", ficha["profesional"]), ("DNI", ficha["profesional_dni"]),
        ("Matrícula", ficha["matricula"]), ("Especialidad", ficha["especialidad"]), ("Email", ficha["profesional_email"]),
        ("Estado de la ficha", "Activo" if ficha["profesional_activo"] else "Inactivo")])
    cuerpo += seccion("Medicamento", [("Nombre / código", f"{ficha['farmaco']} / {ficha['farmaco_codigo']}"),
        ("Principio activo", ficha["farmaco_principio"]), ("Presentación", ficha["farmaco_presentacion"]),
        ("Concentración", ficha["farmaco_concentracion"])])
    if ficha["snomed_id"] is not None:
        cuerpo += seccion("Diagnóstico (catálogo local)", [("Código", ficha["snomed_codigo"]), ("Término", ficha["snomed"])])
    cuerpo += seccion("Dosificación e indicaciones", [("Dosis", ficha["dosis"]), ("Vía", ficha["via_administracion"]),
        ("Frecuencia", ficha["frecuencia"]), ("Duración", ficha["duracion"]), ("Cantidad", ficha["cantidad"]),
        ("Inicio", ficha["fecha_inicio"]), ("Fin", ficha["fecha_fin"]), ("Indicaciones", ficha["indicaciones"])])
    estado = "ACTIVA" if ficha["activo"] else "ANULADA"
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Prescripción {ficha['id']} — {estado}</title>
<style>
body {{font: 15px Arial,sans-serif; color:#163044; background:#edf2f5; margin:0; padding:24px}}
main {{max-width:820px; margin:auto; background:white; padding:32px}}
header {{border-bottom:3px solid #16465b; padding-bottom:16px}} h1 {{font-size:25px; margin:8px 0}}
h2 {{font-size:17px; margin:0 0 12px}} section {{padding:16px 0; border-bottom:1px solid #dbe3e8; break-inside:avoid}}
dl {{display:grid; grid-template-columns:170px 1fr; gap:7px 12px; margin:0}} dt {{font-weight:bold}}
dd {{margin:0; white-space:pre-wrap; overflow-wrap:anywhere}} .estado {{font-weight:bold; border:2px solid; padding:8px; display:inline-block}}
footer {{font-size:12px; margin-top:20px}} .aviso {{font-weight:bold}}
@media print {{body {{background:white; padding:0}} main {{max-width:none; padding:0}} @page {{margin:16mm}}}}
</style></head><body><main><header><div>OPENHIS-UNLaM · Hospital Universitario San Justo</div>
<h1>Prescripción N.º {ficha['id']}</h1><p class="estado">{estado}</p>
<p>Fecha de prescripción (UTC): {escape(texto(ficha['fecha_prescripcion']))}</p></header>
{cuerpo}<footer><p class="aviso">{AVISO}</p>
<p>Generado: {datetime.now().astimezone().isoformat(timespec='seconds')}. El estado corresponde al momento de exportación.</p>
</footer></main></body></html>"""


def exportar_prescripcion(repositorio, prescripcion_id, formato, destino=RAIZ):
    """Devuelve (ruta, contenido). La escritura exclusiva evita reemplazar exportaciones."""
    generadores = {"xml": ("recetas", "receta", crear_xml), "html": ("reportes", "reporte", crear_html)}
    carpeta, prefijo, generar = generadores[formato]
    contenido = generar(repositorio.obtener_prescripcion(prescripcion_id))
    directorio = Path(destino).resolve() / carpeta
    directorio.mkdir(parents=True, exist_ok=True)
    nombre = f"{prefijo}_{prescripcion_id}_{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}.{formato}"
    ruta = directorio / nombre
    with ruta.open("x", encoding="utf-8") as archivo:
        archivo.write(contenido)
    if hasattr(repositorio, "registrar_exportacion"):
        try:
            repositorio.registrar_exportacion(prescripcion_id, ruta, formato)
        except Exception:
            ruta.unlink(missing_ok=True)
            raise
    return ruta, contenido
