"""Módulo independiente de signos vitales, con historial y estados reversibles."""

import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from datos import CAMPOS_SIGNOS, ETIQUETAS, ErrorValidacion
from interfaz import crear_tabla
from ventanas_clinicas import FormularioClinico, VentanaBase, opciones_profesionales


class SignosApp(VentanaBase):
    def __init__(self, raiz, repositorio=None):
        super().__init__(raiz, repositorio, "Signos vitales")
        barra = ttk.Frame(self.cuerpo)
        barra.pack(fill="x", pady=(0, 10))
        ttk.Button(barra, text="Registrar signos", command=self.registrar).pack(side="left", padx=4)
        ttk.Label(barra, text="DNI del paciente:").pack(side="left", padx=(12, 4))
        self.dni = tk.StringVar(raiz)
        entrada = ttk.Entry(barra, textvariable=self.dni, width=16)
        entrada.pack(side="left", padx=4)
        entrada.bind("<Return>", lambda e: self.buscar())
        for texto, accion in (("Buscar historial", self.buscar), ("Ver detalle", self.ver_detalle), ("Anular", self.anular), ("Reactivar", self.reactivar)):
            ttk.Button(barra, text=texto, command=accion).pack(side="left", padx=4)
        self.filtros_estado()
        self.contexto = tk.StringVar(raiz, value="Todos los pacientes")
        ttk.Label(self.cuerpo, textvariable=self.contexto).pack(anchor="w", pady=(0, 8))
        marco, self.tabla = crear_tabla(self.cuerpo, [("id", "ID", 55), ("fecha", "Fecha/hora (UTC)", 155),
            ("paciente", "Paciente", 180), ("dni", "DNI", 100), ("profesional", "Profesional", 170),
            ("presion", "Presión", 85), ("motivo", "Motivo", 200), ("activo", "Estado", 85)])
        marco.pack(fill="both", expand=True)
        self.tabla.bind("<Double-1>", lambda e: self.ver_detalle() if self.tabla.identify_row(e.y) else None)
        ttk.Label(self.cuerpo, textvariable=self.estado).pack(anchor="w", pady=10)
        ttk.Label(self.cuerpo, text="La anulación y la reactivación conservan los datos, el autor y la fecha del registro.").pack(anchor="w")
        self.refrescar()

    def refrescar(self, seleccionar=None, paciente_id=None):
        if seleccionar is not None:
            self.activos = bool(self.repositorio.obtener_signo(seleccionar)["activo"])
        registros = self.repositorio.listar_signos(paciente_id, self.activos)
        self.filas = {r["id"]: r for r in registros}
        self.tabla.delete(*self.tabla.get_children())
        for r in registros:
            presion = f"{r['presion_sistolica'] if r['presion_sistolica'] is not None else '—'}/{r['presion_diastolica'] if r['presion_diastolica'] is not None else '—'}"
            self.tabla.insert("", "end", iid=str(r["id"]), values=(r["id"], r["fecha_hora"], r["paciente"], r["paciente_dni"],
                r["profesional"] or "Sin autor (histórico)", presion, r["motivo_consulta"], "Activo" if r["activo"] else "Anulado"))
        if seleccionar is not None and self.tabla.exists(str(seleccionar)):
            self.tabla.selection_set(str(seleccionar))
            self.tabla.see(str(seleccionar))
        self.estado.set(f"{len(registros)} registro(s) mostrado(s). Sin límite de historial.")
        if paciente_id is None:
            self.contexto.set("Todos los pacientes")

    def registrar(self):
        def abrir():
            pacientes = {p["id"]: f"{p['apellido']}, {p['nombre']} · DNI {p['dni']}" for p in self.repositorio.listar_pacientes()}
            profesionales = opciones_profesionales(self.repositorio)
            if not pacientes or not profesionales:
                raise ErrorValidacion("Registre o reactive al menos un paciente y un profesional antes de cargar signos.")
            def guardar(datos):
                return self.repositorio.registrar_signos(datos["paciente_id"], {**datos, "medico_id": datos["profesional_id"]})
            return FormularioClinico(self.raiz, "Alta de signos vitales",
                ("paciente_id", "profesional_id") + CAMPOS_SIGNOS + ("motivo_consulta",), guardar,
                opciones={"paciente_id": pacientes, "profesional_id": profesionales},
                requeridos=("paciente_id", "profesional_id", "motivo_consulta"),
                nota="Las mediciones son opcionales. Fecha y hora automáticas (UTC).", al_guardar=self.refrescar)
        return self.intentar(abrir)

    def buscar(self):
        def aplicar():
            paciente = self.repositorio.buscar_paciente(self.dni.get())
            self.activos = None
            self.refrescar(paciente_id=paciente["id"] if paciente else -1)
            if paciente:
                self.contexto.set(f"Historial completo · HC {paciente['id']} · {paciente['nombre']} {paciente['apellido']} · {'Activo' if paciente['activo'] else 'Inactivo'}")
            else:
                self.contexto.set("Paciente no encontrado")
                messagebox.showinfo("Búsqueda", "Paciente no encontrado.", parent=self.raiz)
        self.intentar(aplicar)

    def ver_detalle(self):
        def abrir():
            fila = self.seleccionado(self.tabla, self.filas)
            fila = self.repositorio.obtener_signo(fila["id"])
            ventana = tk.Toplevel(self.raiz)
            ventana.title(f"Detalle de signos vitales {fila['id']}")
            ventana.geometry("760x600")
            ventana.transient(self.raiz)
            contenido = ScrolledText(ventana, wrap="word", font=("Segoe UI", 11), padx=16, pady=16)
            contenido.pack(fill="both", expand=True)
            valores = [("Registro", fila["id"]), ("Estado", "Activo" if fila["activo"] else "Anulado"),
                ("Paciente", f"{fila['paciente']} · DNI {fila['paciente_dni']} · {'Activo' if fila['paciente_activo'] else 'Inactivo'}"),
                ("Profesional", f"{fila['profesional'] or 'Sin autor (histórico)'} · {'Activo' if fila['profesional_activo'] else 'Inactivo / sin autor'}"),
                ("Fecha/hora (UTC)", fila["fecha_hora"])]
            valores += [(ETIQUETAS[c], fila[c]) for c in CAMPOS_SIGNOS + ("motivo_consulta",)]
            contenido.insert("1.0", "\n\n".join(f"{k}: {v if v is not None else 'Sin informar'}" for k, v in valores))
            contenido.configure(state="disabled")
            ttk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(pady=8)
            return ventana
        return self.intentar(abrir)

    def cambiar_estado(self, activo):
        def aplicar():
            fila = self.seleccionado(self.tabla, self.filas)
            verbo = "Reactivar" if activo else "Anular"
            if messagebox.askyesno(f"{verbo} signos vitales", f"¿{verbo} el registro {fila['id']}?\nSolo cambia su estado. Las fichas relacionadas se conservan sin cambios.", parent=self.raiz):
                accion = self.repositorio.reactivar_signo if activo else self.repositorio.anular_signo
                accion(fila["id"])
                self.refrescar(fila["id"])
                messagebox.showinfo("Operación exitosa", "Registro reactivado." if activo else "Registro anulado. Se conservan sus datos.", parent=self.raiz)
        self.intentar(aplicar)

    def anular(self):
        self.cambiar_estado(False)

    def reactivar(self):
        self.cambiar_estado(True)
