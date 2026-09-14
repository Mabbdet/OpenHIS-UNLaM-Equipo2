import tkinter as tk

import pytest

from interfaz import AplicacionPacientes


@pytest.mark.parametrize("modo,acciones", [("basico", 0), ("crud", 2), ("signos", 3)])
def test_interfaz_carga_y_busca_paciente(repositorio, datos_paciente, modo, acciones):
    try:
        raiz = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"Tk no está disponible en este entorno: {error}")
    raiz.withdraw()
    try:
        paciente_id = repositorio.registrar_paciente(datos_paciente)
        app = AplicacionPacientes(raiz, repositorio, modo=modo)
        app.dni.set(datos_paciente["dni"])
        app.buscar()
        raiz.update_idletasks()
        assert app.tabla.selection() == (str(paciente_id),)
        assert datos_paciente["nombre"] in app.detalle.get("1.0", "end")
        assert len(app.botones_seleccion) == acciones
    finally:
        raiz.destroy()
