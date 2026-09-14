"""Interfaz Tkinter compartida; cada entrada habilita su incremento académico."""

import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from datos import (
    CAMPOS_EDITABLES, CAMPOS_PACIENTE, CAMPOS_SIGNOS, ETIQUETAS,
    ErrorValidacion, Repositorio,
)


def mostrar_error(ventana, error):
    texto = str(error) if isinstance(error, ErrorValidacion) else "No se pudo completar la operación en la base de datos."
    messagebox.showerror("No se pudo guardar o consultar", texto, parent=ventana)


def crear_tabla(contenedor, columnas, altura=10):
    marco = ttk.Frame(contenedor)
    marco.columnconfigure(0, weight=1)
    marco.rowconfigure(0, weight=1)
    tabla = ttk.Treeview(marco, columns=[c[0] for c in columnas], show="headings", height=altura, selectmode="browse")
    for identificador, titulo, ancho in columnas:
        tabla.heading(identificador, text=titulo)
        tabla.column(identificador, width=ancho, minwidth=55, stretch=True)
    vertical = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
    horizontal = ttk.Scrollbar(marco, orient="horizontal", command=tabla.xview)
    tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    tabla.grid(row=0, column=0, sticky="nsew")
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal.grid(row=1, column=0, sticky="ew")
    return marco, tabla


class FormularioPaciente(tk.Toplevel):
    def __init__(self, aplicacion, paciente=None):
        super().__init__(aplicacion.raiz)
        self.aplicacion = aplicacion
        self.paciente = paciente
        self.title("Modificar paciente" if paciente else "Registrar paciente")
        self.resizable(False, False)
        self.transient(aplicacion.raiz)
        contenido = ttk.Frame(self, padding=20)
        contenido.pack(fill="both", expand=True)
        titulo = f"HC {paciente['id']} · {paciente['nombre']} {paciente['apellido']}" if paciente else "Nuevo paciente"
        ttk.Label(contenido, text=titulo, style="Seccion.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        campos = CAMPOS_EDITABLES if paciente else CAMPOS_PACIENTE
        self.campos = {}
        primer_control = None
        for fila, campo in enumerate(campos, start=1):
            requerido = campo in ("dni", "nombre", "apellido", "fecha_nacimiento", "sexo")
            ttk.Label(contenido, text=ETIQUETAS[campo] + (" *" if requerido else "")).grid(row=fila, column=0, sticky="w", padx=(0, 16), pady=5)
            variable = tk.StringVar(self, value=(paciente.get(campo) or "") if paciente else "")
            self.campos[campo] = variable
            if campo == "sexo":
                control = ttk.Combobox(contenido, textvariable=variable, values=("M", "F"), state="readonly", width=35)
            else:
                control = ttk.Entry(contenido, textvariable=variable, width=38)
            control.grid(row=fila, column=1, sticky="ew", pady=5)
            primer_control = primer_control or control
        pie = "Solo se modifican contacto, domicilio y obra social." if paciente else "* Campos obligatorios"
        ttk.Label(contenido, text=pie).grid(row=len(campos) + 1, column=0, columnspan=2, sticky="w", pady=(12, 8))
        botones = ttk.Frame(contenido)
        botones.grid(row=len(campos) + 2, column=0, columnspan=2, sticky="e")
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="left", padx=4)
        ttk.Button(botones, text="Guardar cambios" if paciente else "Registrar", command=self.guardar).pack(side="left", padx=4)
        self.bind("<Escape>", lambda evento: self.destroy())
        self.grab_set()
        primer_control.focus_set()

    def guardar(self):
        entrada = {campo: variable.get() for campo, variable in self.campos.items()}
        try:
            if self.paciente:
                paciente_id = self.paciente["id"]
                self.aplicacion.repositorio.modificar_paciente(paciente_id, entrada)
                mensaje = "Datos del paciente modificados con éxito."
            else:
                paciente_id = self.aplicacion.repositorio.registrar_paciente(entrada)
                mensaje = f"PACIENTE REGISTRADO CON ÉXITO\nNúmero de Historia Clínica: {paciente_id}"
        except (ErrorValidacion, sqlite3.Error) as error:
            mostrar_error(self, error)
            return
        self.aplicacion.refrescar(seleccionar=paciente_id)
        messagebox.showinfo("Operación exitosa", mensaje, parent=self)
        self.destroy()


class VentanaSignos(tk.Toplevel):
    def __init__(self, aplicacion, paciente):
        super().__init__(aplicacion.raiz)
        self.aplicacion = aplicacion
        self.paciente = paciente
        self.title("Signos vitales e historial")
        self.geometry("890x680")
        self.minsize(780, 600)
        self.transient(aplicacion.raiz)
        contenido = ttk.Frame(self, padding=18)
        contenido.pack(fill="both", expand=True)
        ttk.Label(contenido, text=f"HC {paciente['id']} · {paciente['nombre']} {paciente['apellido']} · DNI {paciente['dni']}", style="Seccion.TLabel").pack(anchor="w", pady=(0, 12))
        formulario = ttk.LabelFrame(contenido, text="Nuevo registro", padding=12)
        formulario.pack(fill="x")
        formulario.columnconfigure(1, weight=1)
        self.campos = {}
        for fila, campo in enumerate(CAMPOS_SIGNOS):
            ttk.Label(formulario, text=ETIQUETAS[campo]).grid(row=fila, column=0, sticky="w", padx=(0, 12), pady=3)
            variable = tk.StringVar(self)
            self.campos[campo] = variable
            ttk.Entry(formulario, textvariable=variable, width=25).grid(row=fila, column=1, sticky="w", pady=3)
        ttk.Label(formulario, text="Motivo de consulta *").grid(row=5, column=0, sticky="nw", padx=(0, 12), pady=5)
        self.motivo = tk.Text(formulario, height=3, width=55, wrap="word", font=("Segoe UI", 10))
        self.motivo.grid(row=5, column=1, sticky="ew", pady=5)
        ttk.Label(formulario, text="* Obligatorio. Fecha y hora automáticas (UTC).").grid(row=6, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Button(formulario, text="Guardar signos vitales", command=self.guardar).grid(row=7, column=0, columnspan=2, sticky="e", pady=4)
        ttk.Label(contenido, text="Historial · últimos 10 registros", style="Seccion.TLabel").pack(anchor="w", pady=(16, 6))
        marco, self.historial = crear_tabla(contenido, [
            ("fecha", "Fecha/hora (UTC)", 150), ("presion", "Presión (mmHg)", 100),
            ("fc", "FC (lpm)", 65), ("temp", "Temp. (°C)", 80),
            ("sat", "SatO2 (%)", 75), ("motivo", "Motivo", 240),
        ], altura=7)
        marco.pack(fill="both", expand=True)
        self.resumen = tk.StringVar(self)
        ttk.Label(contenido, textvariable=self.resumen).pack(anchor="w", pady=5)
        ttk.Button(contenido, text="Cerrar", command=self.destroy).pack(anchor="e")
        self.bind("<Escape>", lambda evento: self.destroy())
        self.grab_set()
        self.refrescar()

    def refrescar(self):
        registros = self.aplicacion.repositorio.historial_signos(self.paciente["id"])
        self.historial.delete(*self.historial.get_children())
        for registro in registros:
            def mostrar(campo):
                valor = registro[campo]
                return "—" if valor is None else valor
            self.historial.insert("", "end", iid=str(registro["id"]), values=(
                registro["fecha_hora"], f"{mostrar('presion_sistolica')}/{mostrar('presion_diastolica')}",
                mostrar("frecuencia_cardiaca"), mostrar("temperatura"),
                mostrar("saturacion_oxigeno"), registro["motivo_consulta"],
            ))
        self.resumen.set(f"{len(registros)} registro(s) mostrado(s)." if registros else "Sin registros de signos vitales.")

    def guardar(self):
        entrada = {campo: variable.get() for campo, variable in self.campos.items()}
        entrada["motivo_consulta"] = self.motivo.get("1.0", "end-1c")
        try:
            self.aplicacion.repositorio.registrar_signos(self.paciente["id"], entrada)
            self.refrescar()
        except (ErrorValidacion, sqlite3.Error) as error:
            mostrar_error(self, error)
            return
        for variable in self.campos.values():
            variable.set("")
        self.motivo.delete("1.0", "end")
        messagebox.showinfo("Registro exitoso", "Signos vitales registrados con éxito.", parent=self)


class AplicacionPacientes:
    def __init__(self, raiz, repositorio=None, modo="signos"):
        if modo not in ("basico", "crud", "signos"):
            raise ValueError("Modo de interfaz desconocido")
        self.raiz = raiz
        self.repositorio = repositorio if repositorio is not None else Repositorio()
        self.modo = modo
        raiz.title("OpenHIS-UNLaM · Gestión de pacientes")
        raiz.geometry("1050x680")
        raiz.minsize(850, 580)
        estilo = ttk.Style(raiz)
        estilo.theme_use("clam")
        estilo.configure("TLabel", font=("Segoe UI", 10))
        estilo.configure("TButton", font=("Segoe UI", 10), padding=(10, 6))
        estilo.configure("Titulo.TLabel", font=("Segoe UI", 19, "bold"), foreground="#16465b")
        estilo.configure("Seccion.TLabel", font=("Segoe UI", 11, "bold"))
        estilo.configure("Treeview", font=("Segoe UI", 10), rowheight=28)
        estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        contenido = ttk.Frame(raiz, padding=20)
        contenido.pack(fill="both", expand=True)
        ttk.Label(contenido, text="HOSPITAL UNIVERSITARIO SAN JUSTO", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(contenido, text="Sistema de gestión de pacientes").pack(anchor="w", pady=(2, 16))
        herramientas = ttk.Frame(contenido)
        herramientas.pack(fill="x", pady=(0, 12))
        ttk.Button(herramientas, text="Registrar", command=self.registrar).pack(side="left", padx=(0, 14))
        ttk.Label(herramientas, text="DNI:").pack(side="left", padx=(0, 6))
        self.dni = tk.StringVar(raiz)
        busqueda = ttk.Entry(herramientas, textvariable=self.dni, width=20)
        busqueda.pack(side="left", padx=(0, 6))
        busqueda.bind("<Return>", lambda evento: self.buscar())
        ttk.Button(herramientas, text="Buscar", command=self.buscar).pack(side="left", padx=4)
        ttk.Button(herramientas, text="Ver todos", command=self.refrescar).pack(side="left", padx=4)
        self.botones_seleccion = []
        if modo in ("crud", "signos"):
            for texto, accion in (("Modificar", self.modificar), ("Eliminar", self.eliminar)):
                boton = ttk.Button(herramientas, text=texto, command=accion, state="disabled")
                boton.pack(side="left", padx=4)
                self.botones_seleccion.append(boton)
        if modo == "signos":
            boton = ttk.Button(herramientas, text="Signos", command=self.signos, state="disabled")
            boton.pack(side="left", padx=4)
            self.botones_seleccion.append(boton)
        marco, self.tabla = crear_tabla(contenido, [
            ("hc", "HC", 60), ("dni", "DNI", 100), ("nombre", "Nombre", 155),
            ("apellido", "Apellido", 155), ("telefono", "Teléfono", 130),
            ("obra", "Obra social", 210),
        ])
        marco.pack(fill="both", expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self.mostrar_detalle)
        self.tabla.bind("<Double-1>", self.doble_clic)
        self.estado = tk.StringVar(raiz)
        ttk.Label(contenido, textvariable=self.estado).pack(anchor="w", pady=6)
        ttk.Label(contenido, text="Ficha del paciente seleccionado", style="Seccion.TLabel").pack(anchor="w", pady=(10, 6))
        self.detalle = tk.Text(contenido, height=7, wrap="word", state="disabled", font=("Segoe UI", 10), relief="flat", padx=12, pady=10)
        self.detalle.pack(fill="x")
        ayuda = "Seleccione una fila para ver la ficha. Doble clic para registrar signos vitales." if modo == "signos" else "Seleccione una fila para ver la ficha completa."
        ttk.Label(contenido, text=ayuda).pack(anchor="w", pady=(8, 0))
        self.refrescar()

    def _detalle(self, texto):
        self.detalle.configure(state="normal")
        self.detalle.delete("1.0", "end")
        self.detalle.insert("1.0", texto)
        self.detalle.configure(state="disabled")

    def _listar(self, pacientes, seleccionar=None):
        self.tabla.delete(*self.tabla.get_children())
        for paciente in pacientes:
            self.tabla.insert("", "end", iid=str(paciente["id"]), values=(
                paciente["id"], paciente["dni"], paciente["nombre"], paciente["apellido"],
                paciente["telefono"] or "—", paciente["obra_social"] or "—",
            ))
        self.estado.set(f"{len(pacientes)} paciente(s) mostrado(s).")
        if seleccionar is not None and self.tabla.exists(str(seleccionar)):
            self.tabla.selection_set(str(seleccionar))
            self.tabla.focus(str(seleccionar))
            self.tabla.see(str(seleccionar))
        self.mostrar_detalle()

    def refrescar(self, seleccionar=None):
        try:
            self._listar(self.repositorio.listar_pacientes(), seleccionar)
            self.dni.set("")
        except sqlite3.Error as error:
            mostrar_error(self.raiz, error)

    def seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            raise ErrorValidacion("Seleccione un paciente del listado.")
        return self.repositorio.obtener_paciente(int(seleccion[0]))

    def mostrar_detalle(self, evento=None):
        seleccionado = bool(self.tabla.selection())
        for boton in self.botones_seleccion:
            boton.configure(state="normal" if seleccionado else "disabled")
        if not seleccionado:
            self._detalle("Seleccione un paciente para consultar su ficha.")
            return
        try:
            paciente = self.seleccionado()
        except (ErrorValidacion, sqlite3.Error) as error:
            self._detalle(str(error))
            for boton in self.botones_seleccion:
                boton.configure(state="disabled")
            return
        def valor(campo):
            return paciente[campo] or "Sin informar"
        self._detalle(
            f"HC: {paciente['id']}    |    DNI: {paciente['dni']}    |    {paciente['nombre']} {paciente['apellido']}\n"
            f"Nacimiento: {paciente['fecha_nacimiento']}    |    Sexo: {paciente['sexo']}\n"
            f"Teléfono: {valor('telefono')}    |    Email: {valor('email')}\n"
            f"Domicilio: {valor('domicilio')}\n"
            f"Obra social: {valor('obra_social')}\n"
            f"Fecha de registro (UTC): {paciente['fecha_registro']}"
        )

    def registrar(self):
        return FormularioPaciente(self)

    def buscar(self):
        try:
            paciente = self.repositorio.buscar_paciente(self.dni.get())
            self._listar([paciente] if paciente else [], paciente["id"] if paciente else None)
            if paciente is None:
                messagebox.showinfo("Búsqueda", "Paciente no encontrado.", parent=self.raiz)
        except (ErrorValidacion, sqlite3.Error) as error:
            mostrar_error(self.raiz, error)

    def modificar(self):
        try:
            return FormularioPaciente(self, self.seleccionado())
        except (ErrorValidacion, sqlite3.Error) as error:
            mostrar_error(self.raiz, error)

    def eliminar(self):
        try:
            paciente = self.seleccionado()
            confirmado = messagebox.askyesno(
                "Confirmar eliminación",
                f"¿Eliminar a {paciente['nombre']} {paciente['apellido']} (HC {paciente['id']})?\n"
                "Se eliminarán también todos sus registros de signos vitales. Esta acción no se puede deshacer.",
                parent=self.raiz,
            )
            if not confirmado:
                return
            cantidad = self.repositorio.eliminar_paciente(paciente["id"])
            self.refrescar()
            messagebox.showinfo("Eliminación exitosa", f"Paciente eliminado. Registros de signos vitales eliminados: {cantidad}.", parent=self.raiz)
        except (ErrorValidacion, sqlite3.Error) as error:
            mostrar_error(self.raiz, error)

    def signos(self):
        try:
            return VentanaSignos(self, self.seleccionado())
        except (ErrorValidacion, sqlite3.Error) as error:
            mostrar_error(self.raiz, error)

    def doble_clic(self, evento):
        fila = self.tabla.identify_row(evento.y)
        if not fila:
            return
        self.tabla.selection_set(fila)
        if self.modo == "signos":
            self.signos()
        else:
            self.mostrar_detalle()


def ejecutar(modo="signos"):
    raiz = tk.Tk()
    try:
        AplicacionPacientes(raiz, modo=modo)
    except sqlite3.Error as error:
        mostrar_error(raiz, error)
        raiz.destroy()
        return
    raiz.mainloop()
