"""Ventanas de tablas maestras, profesionales y prescripciones — Entrega 4."""

import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from datos import CATALOGOS, ETIQUETAS, ErrorValidacion, Repositorio
from interfaz import crear_tabla, mostrar_error


TITULOS = {
    **ETIQUETAS, "codigo": "Código", "descripcion": "Descripción", "termino": "Término",
    "categoria": "Categoría", "principio_activo": "Principio activo", "presentacion": "Presentación",
    "concentracion": "Concentración", "via_administracion": "Vía de administración",
    "matricula": "Matrícula", "especialidad_id": "Especialidad", "paciente_id": "Paciente",
    "profesional_id": "Profesional", "farmaco_id": "Fármaco", "snomed_id": "SNOMED (opcional)",
    "dosis": "Dosis", "frecuencia": "Frecuencia", "duracion": "Duración",
    "cantidad": "Cantidad", "indicaciones": "Indicaciones", "fecha_inicio": "Inicio (AAAA-MM-DD)",
    "fecha_fin": "Fin (AAAA-MM-DD)",
}


def opciones_especialidades(repositorio, incluir=None):
    return {fila["id"]: f"{fila['codigo']} · {fila['nombre']}" + (" (inactiva)" if not fila["activo"] else "")
            for fila in repositorio.listar_catalogo("especialidades") if fila["activo"] or fila["id"] == incluir}


def opciones_profesionales(repositorio):
    return {fila["id"]: f"{fila['apellido']}, {fila['nombre']} · Mat. {fila['matricula']}"
            for fila in repositorio.listar_profesionales()}


class FormularioClinico(tk.Toplevel):
    def __init__(self, padre, titulo, campos, guardar, inicial=None, opciones=None, requeridos=(), nota="", al_guardar=None):
        super().__init__(padre)
        self.title(titulo)
        self.transient(padre)
        self.resizable(True, False)
        self.guardar_datos = guardar
        self.al_guardar = al_guardar
        self.opciones = opciones or {}
        self.campos = {}
        inicial = inicial or {}
        cuerpo = ttk.Frame(self, padding=18)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(1, weight=1)
        ttk.Label(cuerpo, text=titulo, font=("Segoe UI", 13, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        for fila, campo in enumerate(campos, start=1):
            ttk.Label(cuerpo, text=TITULOS.get(campo, campo) + (" *" if campo in requeridos else "")).grid(row=fila, column=0, sticky="w", padx=(0, 16), pady=4)
            valor = inicial.get(campo)
            valor = "" if valor is None else valor
            if campo in self.opciones:
                valor = self.opciones[campo].get(valor, "")
            variable = tk.StringVar(self, value=valor)
            self.campos[campo] = variable
            if campo in self.opciones:
                lista = list(self.opciones[campo].values())
                control = ttk.Combobox(cuerpo, textvariable=variable, values=([""] if campo not in requeridos else []) + lista, state="readonly", width=58)
            else:
                control = ttk.Entry(cuerpo, textvariable=variable, width=60)
            control.grid(row=fila, column=1, sticky="ew", pady=4)
        ttk.Label(cuerpo, text="* Campos obligatorios" + ("\n" + nota if nota else ""), wraplength=650).grid(row=len(campos)+1, column=0, columnspan=2, sticky="w", pady=10)
        botones = ttk.Frame(cuerpo)
        botones.grid(row=len(campos)+2, column=0, columnspan=2, sticky="e")
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="left", padx=4)
        ttk.Button(botones, text="Guardar", command=self.guardar).pack(side="left", padx=4)
        self.bind("<Escape>", lambda e: self.destroy())
        self.grab_set()

    def guardar(self):
        entrada = {campo: variable.get() for campo, variable in self.campos.items()}
        for campo, opciones in self.opciones.items():
            entrada[campo] = next((identificador for identificador, etiqueta in opciones.items() if etiqueta == entrada[campo]), None)
        try:
            registro_id = self.guardar_datos(entrada)
        except (ErrorValidacion, sqlite3.Error) as error:
            mostrar_error(self, error)
            return
        if self.al_guardar:
            self.al_guardar(registro_id)
        messagebox.showinfo("Operación exitosa", f"{self.title()}: operación realizada con éxito.", parent=self)
        self.destroy()


class VentanaBase:
    def __init__(self, raiz, repositorio, titulo):
        self.raiz = raiz
        self.repositorio = repositorio if repositorio is not None else Repositorio()
        raiz.title(f"OpenHIS-UNLaM · {titulo}")
        raiz.geometry("1080x680")
        raiz.minsize(850, 580)
        estilo = ttk.Style(raiz)
        estilo.theme_use("clam")
        estilo.configure("TButton", padding=(9, 5), font=("Segoe UI", 10))
        estilo.configure("TLabel", font=("Segoe UI", 10))
        estilo.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        self.cuerpo = ttk.Frame(raiz, padding=18)
        self.cuerpo.pack(fill="both", expand=True)
        ttk.Label(self.cuerpo, text="HOSPITAL UNIVERSITARIO SAN JUSTO", font=("Segoe UI", 17, "bold"), foreground="#16465b").pack(anchor="w")
        ttk.Label(self.cuerpo, text=titulo, font=("Segoe UI", 12)).pack(anchor="w", pady=(4, 14))
        self.estado = tk.StringVar(raiz)

    def intentar(self, operacion):
        try:
            return operacion()
        except (ErrorValidacion, sqlite3.Error) as error:
            mostrar_error(self.raiz, error)

    @staticmethod
    def seleccionado(tabla, filas):
        seleccion = tabla.selection()
        if not seleccion:
            raise ErrorValidacion("Seleccione un registro del listado.")
        fila = filas.get(int(seleccion[0]))
        if fila is None:
            raise ErrorValidacion("Actualice el listado y seleccione un registro.")
        return fila


class TablasMaestrasApp(VentanaBase):
    def __init__(self, raiz, repositorio=None):
        super().__init__(raiz, repositorio, "Tablas maestras")
        self.tablas, self.filas, self.filtros = {}, {}, {}
        self.pestanas = ttk.Notebook(self.cuerpo)
        self.pestanas.pack(fill="both", expand=True)
        for catalogo, titulo in (("especialidades", "Especialidades"), ("snomed", "SNOMED CT local"), ("farmacos", "Fármacos")):
            pagina = ttk.Frame(self.pestanas, padding=12)
            self.pestanas.add(pagina, text=titulo)
            barra = ttk.Frame(pagina)
            barra.pack(fill="x", pady=(0, 10))
            ttk.Button(barra, text="Registrar", command=lambda c=catalogo: self.registrar(c)).pack(side="left", padx=4)
            if catalogo == "especialidades":
                ttk.Button(barra, text="Modificar", command=self.modificar).pack(side="left", padx=4)
                ttk.Button(barra, text="Desactivar", command=self.desactivar).pack(side="left", padx=4)
            if catalogo == "snomed":
                self.filtros[catalogo] = tk.StringVar(raiz)
                ttk.Label(barra, text="Término:").pack(side="left", padx=(14, 4))
                entrada = ttk.Entry(barra, textvariable=self.filtros[catalogo], width=25)
                entrada.pack(side="left", padx=4)
                entrada.bind("<Return>", lambda e: self.intentar(lambda: self.refrescar("snomed")))
                ttk.Button(barra, text="Buscar", command=lambda: self.intentar(lambda: self.refrescar("snomed"))).pack(side="left", padx=4)
            ttk.Button(barra, text="Ver todos / Actualizar", command=lambda c=catalogo: self.ver_todos(c)).pack(side="left", padx=4)
            _, campos, _ = CATALOGOS[catalogo]
            columnas = [("id", "ID", 50)] + [(campo, TITULOS.get(campo, campo), 180 if campo != "codigo" else 100) for campo in campos] + [("activo", "Estado", 85)]
            marco, tabla = crear_tabla(pagina, columnas, altura=13)
            marco.pack(fill="both", expand=True)
            self.tablas[catalogo] = tabla
            self.refrescar(catalogo)
        ttk.Label(self.cuerpo, textvariable=self.estado).pack(anchor="w", pady=8)
        ttk.Label(self.cuerpo, text="Catálogos educativos locales. La desactivación conserva las relaciones existentes.").pack(anchor="w")

    def refrescar(self, catalogo, seleccionar=None):
        filtro = self.filtros[catalogo].get() if catalogo in self.filtros else ""
        filas = self.repositorio.listar_catalogo(catalogo, filtro)
        self.filas[catalogo] = {fila["id"]: fila for fila in filas}
        tabla = self.tablas[catalogo]
        tabla.delete(*tabla.get_children())
        for fila in filas:
            tabla.insert("", "end", iid=str(fila["id"]), values=[fila["id"]] + [fila[c] or "—" for c in CATALOGOS[catalogo][1]] + ["Activa" if fila["activo"] else "Inactiva"])
        if seleccionar is not None and tabla.exists(str(seleccionar)):
            tabla.selection_set(str(seleccionar))
            tabla.see(str(seleccionar))
        self.estado.set(f"{len(filas)} registro(s) en {catalogo}.")

    def ver_todos(self, catalogo):
        if catalogo in self.filtros:
            self.filtros[catalogo].set("")
        self.intentar(lambda: self.refrescar(catalogo))

    def registrar(self, catalogo):
        _, campos, etiqueta = CATALOGOS[catalogo]
        return FormularioClinico(self.raiz, f"Alta de {catalogo}", campos,
            lambda datos: self.repositorio.guardar_catalogo(catalogo, datos), requeridos=("codigo", etiqueta),
            al_guardar=lambda registro_id: self.refrescar(catalogo, registro_id))

    def modificar(self):
        def abrir():
            fila = self.seleccionado(self.tablas["especialidades"], self.filas["especialidades"])
            return FormularioClinico(self.raiz, "Modificar especialidad", CATALOGOS["especialidades"][1],
                lambda datos: self.repositorio.guardar_catalogo("especialidades", datos, fila["id"]), inicial=fila,
                requeridos=("codigo", "nombre"), al_guardar=lambda registro_id: self.refrescar("especialidades", registro_id))
        return self.intentar(abrir)

    def desactivar(self):
        def aplicar():
            fila = self.seleccionado(self.tablas["especialidades"], self.filas["especialidades"])
            if messagebox.askyesno("Desactivar especialidad", f"¿Desactivar {fila['nombre']}?\nNo se podrá asignar a nuevos profesionales.", parent=self.raiz):
                self.repositorio.desactivar_especialidad(fila["id"])
                self.refrescar("especialidades", fila["id"])
                messagebox.showinfo("Operación exitosa", "Especialidad desactivada.", parent=self.raiz)
        self.intentar(aplicar)


class ProfesionalesApp(VentanaBase):
    def __init__(self, raiz, repositorio=None):
        super().__init__(raiz, repositorio, "Gestión de profesionales")
        barra = ttk.Frame(self.cuerpo)
        barra.pack(fill="x", pady=(0, 10))
        ttk.Button(barra, text="Registrar", command=self.registrar).pack(side="left", padx=4)
        ttk.Label(barra, text="DNI:").pack(side="left", padx=(12, 4))
        self.dni = tk.StringVar(raiz)
        entrada = ttk.Entry(barra, textvariable=self.dni, width=16)
        entrada.pack(side="left", padx=4)
        entrada.bind("<Return>", lambda e: self.buscar())
        for texto, accion in (("Buscar", self.buscar), ("Ver todos", lambda: self.intentar(self.refrescar)), ("Modificar", self.modificar), ("Eliminar", self.eliminar), ("Actualizar especialidades", self.actualizar_especialidades)):
            ttk.Button(barra, text=texto, command=accion).pack(side="left", padx=3)
        marco, self.tabla = crear_tabla(self.cuerpo, [("id", "Registro", 65), ("dni", "DNI", 95), ("nombre", "Nombre", 130), ("apellido", "Apellido", 130), ("matricula", "Matrícula", 110), ("especialidad", "Especialidad", 190), ("telefono", "Teléfono", 110)])
        marco.pack(fill="both", expand=True)
        self.detalle = tk.StringVar(raiz, value="Seleccione un profesional.")
        ttk.Label(self.cuerpo, textvariable=self.detalle, wraplength=950).pack(anchor="w", pady=12)
        ttk.Label(self.cuerpo, textvariable=self.estado).pack(anchor="w")
        self.tabla.bind("<<TreeviewSelect>>", self.mostrar_detalle)
        self.refrescar()

    def refrescar(self, seleccionar=None, filas=None):
        self.filas = {fila["id"]: fila for fila in (self.repositorio.listar_profesionales() if filas is None else filas)}
        self.tabla.delete(*self.tabla.get_children())
        for fila in self.filas.values():
            self.tabla.insert("", "end", iid=str(fila["id"]), values=[fila[c] or "—" for c in ("id", "dni", "nombre", "apellido", "matricula", "especialidad", "telefono")])
        if seleccionar is not None and self.tabla.exists(str(seleccionar)):
            self.tabla.selection_set(str(seleccionar))
            self.tabla.see(str(seleccionar))
        self.estado.set(f"{len(self.filas)} profesional(es) mostrado(s).")
        self.mostrar_detalle()

    def mostrar_detalle(self, evento=None):
        if not self.tabla.selection():
            self.detalle.set("Seleccione un profesional.")
            return
        fila = self.seleccionado(self.tabla, self.filas)
        self.detalle.set(f"{fila['nombre']} {fila['apellido']} · DNI {fila['dni']} · Matrícula {fila['matricula']}\n"
            f"Nacimiento: {fila['fecha_nacimiento']} · Sexo: {fila['sexo']} · Especialidad: {fila['especialidad']}"
            f"{' (inactiva)' if not fila['especialidad_activa'] else ''}\n"
            f"Teléfono: {fila['telefono'] or 'Sin informar'} · Email: {fila['email'] or 'Sin informar'}\n"
            f"Fecha de registro (UTC): {fila['fecha_registro']}")

    def registrar(self):
        def abrir():
            especialidades = opciones_especialidades(self.repositorio)
            if not especialidades:
                raise ErrorValidacion("Registre una especialidad activa en Tablas maestras antes de dar de alta un profesional.")
            campos = ("dni", "nombre", "apellido", "fecha_nacimiento", "sexo", "matricula", "especialidad_id", "telefono", "email")
            return FormularioClinico(self.raiz, "Alta de profesional", campos, self.repositorio.registrar_profesional,
                opciones={"sexo": {"M": "M", "F": "F"}, "especialidad_id": especialidades}, requeridos=campos[:7],
                nota="La vigencia de la matrícula debe verificarse por el procedimiento de la institución.", al_guardar=self.refrescar)
        return self.intentar(abrir)

    def buscar(self):
        def aplicar():
            fila = self.repositorio.buscar_profesional(self.dni.get())
            self.refrescar(fila["id"] if fila else None, [fila] if fila else [])
            if not fila:
                messagebox.showinfo("Búsqueda", "Profesional no encontrado.", parent=self.raiz)
        self.intentar(aplicar)

    def modificar(self):
        def abrir():
            fila = self.seleccionado(self.tabla, self.filas)
            return FormularioClinico(self.raiz, "Modificar profesional", ("telefono", "email", "especialidad_id"),
                lambda datos: (self.repositorio.modificar_profesional(fila["id"], datos), fila["id"])[1], inicial=fila,
                opciones={"especialidad_id": opciones_especialidades(self.repositorio, fila["especialidad_id"])},
                requeridos=("especialidad_id",), al_guardar=self.refrescar)
        return self.intentar(abrir)

    def eliminar(self):
        def aplicar():
            fila = self.seleccionado(self.tabla, self.filas)
            if messagebox.askyesno("Eliminar profesional", f"¿Eliminar a {fila['nombre']} {fila['apellido']}?", parent=self.raiz):
                self.repositorio.eliminar_profesional(fila["id"])
                self.refrescar()
                messagebox.showinfo("Operación exitosa", "Profesional eliminado.", parent=self.raiz)
        self.intentar(aplicar)

    def actualizar_especialidades(self):
        def aplicar():
            self.refrescar()
            cantidad = len(opciones_especialidades(self.repositorio))
            self.estado.set(f"Especialidades actualizadas: {cantidad} activa(s). Se cargarán al abrir los formularios.")
        self.intentar(aplicar)


class PrescripcionesApp(VentanaBase):
    def __init__(self, raiz, repositorio=None):
        super().__init__(raiz, repositorio, "Prescripciones")
        barra = ttk.Frame(self.cuerpo)
        barra.pack(fill="x", pady=(0, 10))
        ttk.Button(barra, text="Registrar prescripción", command=self.registrar).pack(side="left", padx=4)
        ttk.Label(barra, text="DNI del paciente:").pack(side="left", padx=(12, 4))
        self.dni = tk.StringVar(raiz)
        entrada = ttk.Entry(barra, textvariable=self.dni, width=15)
        entrada.pack(side="left", padx=4)
        entrada.bind("<Return>", lambda e: self.buscar())
        for texto, accion in (("Buscar", self.buscar), ("Ver todos", lambda: self.intentar(self.refrescar)), ("Ver detalle", self.ver_detalle), ("Anular", self.anular)):
            ttk.Button(barra, text=texto, command=accion).pack(side="left", padx=3)
        marco, self.tabla = crear_tabla(self.cuerpo, [("id", "ID", 50), ("fecha", "Fecha/hora (UTC)", 155), ("paciente", "Paciente", 180), ("profesional", "Profesional", 180), ("farmaco", "Fármaco", 150), ("estado", "Estado", 85)])
        marco.pack(fill="both", expand=True)
        ttk.Label(self.cuerpo, textvariable=self.estado).pack(anchor="w", pady=10)
        ttk.Label(self.cuerpo, text="La anulación conserva la prescripción y sus relaciones.").pack(anchor="w")
        self.tabla.bind("<Double-1>", lambda e: self.ver_detalle() if self.tabla.identify_row(e.y) else None)
        self.refrescar()

    def refrescar(self, seleccionar=None, paciente_id=None):
        self.filas = {fila["id"]: fila for fila in self.repositorio.listar_prescripciones(paciente_id)}
        self.tabla.delete(*self.tabla.get_children())
        for fila in self.filas.values():
            self.tabla.insert("", "end", iid=str(fila["id"]), values=(fila["id"], fila["fecha_prescripcion"], fila["paciente"], fila["profesional"], fila["farmaco"], "Activa" if fila["activo"] else "Anulada"))
        if seleccionar is not None and self.tabla.exists(str(seleccionar)):
            self.tabla.selection_set(str(seleccionar))
            self.tabla.see(str(seleccionar))
        self.estado.set(f"{len(self.filas)} prescripción(es) mostrada(s).")

    def registrar(self):
        def abrir():
            opciones = {
                "paciente_id": {p["id"]: f"{p['apellido']}, {p['nombre']} · DNI {p['dni']}" for p in self.repositorio.listar_pacientes()},
                "profesional_id": opciones_profesionales(self.repositorio),
                "farmaco_id": {f["id"]: f"{f['codigo']} · {f['nombre']} · {f['concentracion'] or ''}" for f in self.repositorio.listar_catalogo("farmacos", solo_activos=True)},
                "snomed_id": {s["id"]: f"{s['codigo']} · {s['termino']}" for s in self.repositorio.listar_catalogo("snomed", solo_activos=True)},
            }
            for campo in ("paciente_id", "profesional_id", "farmaco_id"):
                if not opciones[campo]:
                    raise ErrorValidacion(f"No hay opciones de {TITULOS[campo].lower()}. Complete los datos antes de prescribir.")
            campos = ("paciente_id", "profesional_id", "farmaco_id", "snomed_id", "dosis", "via_administracion", "frecuencia", "duracion", "cantidad", "indicaciones", "fecha_inicio", "fecha_fin")
            return FormularioClinico(self.raiz, "Alta de prescripción", campos, self.repositorio.registrar_prescripcion,
                opciones=opciones, requeridos=("paciente_id", "profesional_id", "farmaco_id", "dosis", "via_administracion", "frecuencia"), al_guardar=self.refrescar)
        return self.intentar(abrir)

    def buscar(self):
        def aplicar():
            paciente = self.repositorio.buscar_paciente(self.dni.get())
            if paciente is None:
                self.refrescar(paciente_id=-1)
                messagebox.showinfo("Búsqueda", "Paciente no encontrado.", parent=self.raiz)
            else:
                self.refrescar(paciente_id=paciente["id"])
        self.intentar(aplicar)

    def ver_detalle(self):
        def abrir():
            seleccion = self.seleccionado(self.tabla, self.filas)
            fila = self.repositorio.obtener_prescripcion(seleccion["id"])
            ventana = tk.Toplevel(self.raiz)
            ventana.title(f"Detalle de prescripción {fila['id']}")
            ventana.transient(self.raiz)
            ventana.geometry("760x560")
            texto = tk.Text(ventana, wrap="word", font=("Segoe UI", 11), padx=18, pady=18)
            texto.pack(fill="both", expand=True)
            valores = [
                ("Prescripción", fila["id"]), ("Estado", "Activa" if fila["activo"] else "Anulada"),
                ("Paciente", f"{fila['paciente']} · DNI {fila['paciente_dni']}"),
                ("Profesional", f"{fila['profesional']} · Matrícula {fila['matricula']}"),
                ("Fármaco", f"{fila['farmaco']} · {fila['farmaco_codigo']}"),
                ("SNOMED", f"{fila['snomed_codigo']} · {fila['snomed']}" if fila["snomed_id"] else "Sin informar"),
            ] + [(TITULOS[c], fila[c]) for c in ("dosis", "via_administracion", "frecuencia", "duracion", "cantidad", "indicaciones", "fecha_inicio", "fecha_fin")] + [("Fecha/hora (UTC)", fila["fecha_prescripcion"])]
            texto.insert("1.0", "\n\n".join(f"{etiqueta}: {valor if valor is not None and valor != '' else 'Sin informar'}" for etiqueta, valor in valores))
            texto.configure(state="disabled")
            ttk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(pady=8)
            ventana.grab_set()
            return ventana
        return self.intentar(abrir)

    def anular(self):
        def aplicar():
            fila = self.seleccionado(self.tabla, self.filas)
            if messagebox.askyesno("Anular prescripción", f"¿Anular la prescripción {fila['id']} de {fila['paciente']}?", parent=self.raiz):
                self.repositorio.anular_prescripcion(fila["id"])
                self.refrescar(fila["id"])
                messagebox.showinfo("Operación exitosa", "Prescripción anulada. Se conserva su detalle.", parent=self.raiz)
        self.intentar(aplicar)


def ejecutar_clinica(tipo):
    raiz = tk.Tk()
    try:
        {"maestras": TablasMaestrasApp, "profesionales": ProfesionalesApp, "prescripciones": PrescripcionesApp}[tipo](raiz)
    except (ErrorValidacion, sqlite3.Error) as error:
        mostrar_error(raiz, error)
        raiz.destroy()
        return
    raiz.mainloop()
