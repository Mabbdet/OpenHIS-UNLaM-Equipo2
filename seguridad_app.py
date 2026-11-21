"""Pantallas de login, usuarios y consulta de auditoría."""

import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText

from datos import ErrorValidacion
from interfaz import crear_tabla, mostrar_error
from seguridad import ROLES
from ventanas_clinicas import FormularioClinico, TITULOS, VentanaBase

TITULOS.update({"usuario": "Usuario", "nombre_completo": "Nombre completo", "rol": "Rol", "password": "Contraseña"})


class LoginApp:
    def __init__(self, raiz, servicio, al_ingresar):
        self.raiz, self.servicio, self.al_ingresar = raiz, servicio, al_ingresar
        raiz.title("OpenHIS-UNLaM · Ingreso")
        raiz.geometry("540x440")
        raiz.minsize(500, 420)
        self.cuerpo = ttk.Frame(raiz, padding=32)
        self.cuerpo.pack(fill="both", expand=True)
        self.inicial = servicio.requiere_admin_inicial()
        ttk.Label(self.cuerpo, text="OpenHIS-UNLaM", font=("Segoe UI", 22, "bold")).pack(anchor="w", pady=12)
        ttk.Label(self.cuerpo, text="Crear administrador inicial" if self.inicial else "Ingresar al sistema", font=("Segoe UI", 13)).pack(anchor="w", pady=8)
        self.usuario, self.password, self.nombre = (tk.StringVar(raiz) for _ in range(3))
        for etiqueta, variable, oculto in [("Usuario", self.usuario, False), ("Contraseña (mínimo 8 caracteres)", self.password, True)] + ([("Nombre completo", self.nombre, False)] if self.inicial else []):
            ttk.Label(self.cuerpo, text=etiqueta).pack(anchor="w", pady=(8, 2))
            control = ttk.Entry(self.cuerpo, textvariable=variable, show="*" if oculto else "")
            control.pack(fill="x")
        self.estado = tk.StringVar(raiz)
        ttk.Label(self.cuerpo, textvariable=self.estado, foreground="#a32222", wraplength=450).pack(anchor="w", pady=10)
        ttk.Button(self.cuerpo, text="Crear e ingresar" if self.inicial else "Ingresar", command=self.ingresar).pack(anchor="e", pady=8)
        raiz.bind("<Return>", self.ingresar)

    def ingresar(self, evento=None):
        try:
            if self.inicial:
                self.servicio.crear_admin_inicial(self.usuario.get(), self.password.get(), self.nombre.get())
                self.inicial = False
            sesion = self.servicio.autenticar(self.usuario.get(), self.password.get())
        except (ErrorValidacion, sqlite3.Error) as error:
            self.estado.set(str(error))
            self.password.set("")
            return
        self.password.set("")
        self.raiz.unbind("<Return>")
        self.cuerpo.destroy()
        self.al_ingresar(sesion)


class UsuariosApp(VentanaBase):
    def __init__(self, raiz, repositorio):
        repositorio.autorizar("Usuarios")
        super().__init__(raiz, repositorio, "Usuarios")
        self.servicio, self.sesion = repositorio._servicio, repositorio._sesion
        self.filtros_estado()
        barra = ttk.Frame(self.cuerpo)
        barra.pack(fill="x", pady=8)
        for nombre, accion in (("Nuevo usuario", self.registrar), ("Modificar", self.modificar),
                               ("Cambiar contraseña", self.password), ("Desactivar", lambda: self.cambiar_estado(0)),
                               ("Reactivar", lambda: self.cambiar_estado(1))):
            ttk.Button(barra, text=nombre, command=lambda a=accion: self.intentar(a)).pack(side="left", padx=3)
        marco, self.tabla = crear_tabla(self.cuerpo, (("id", "ID", 55), ("usuario", "Usuario", 150),
            ("nombre_completo", "Nombre completo", 230), ("rol", "Rol", 140),
            ("activo", "Activo", 65), ("ultimo_acceso", "Último acceso UTC", 190)))
        marco.pack(fill="both", expand=True)
        self.refrescar()

    def refrescar(self, seleccionar=None):
        self.filas = {f["id"]: f for f in self.servicio.listar_usuarios(self.sesion, self.activos)}
        self.tabla.delete(*self.tabla.get_children())
        for i, f in self.filas.items():
            self.tabla.insert("", "end", iid=str(i), values=(i, f["usuario"], f["nombre_completo"], f["rol"], "Sí" if f["activo"] else "No", f["ultimo_acceso"] or "Sin acceso"))
        if seleccionar in self.filas:
            self.tabla.selection_set(str(seleccionar))

    def formulario(self, fila=None):
        campos = ("usuario", "nombre_completo", "email", "rol") if fila else ("usuario", "nombre_completo", "email", "rol", "password")
        def guardar(datos):
            i = self.servicio.guardar_usuario(self.sesion, datos, fila["id"] if fila else None)
            self.refrescar(i)
            return i
        formulario = FormularioClinico(self.raiz, "Modificar usuario" if fila else "Nuevo usuario", campos, guardar,
            inicial=fila, opciones={"rol": {r: r for r in ROLES}},
            requeridos=("usuario", "nombre_completo", "rol") + (() if fila else ("password",)),
            nota="La contraseña debe tener entre 8 y 256 caracteres." if not fila else "El nombre de usuario se conserva.")
        # El formulario compartido también se usa para datos clínicos; aquí oculta la contraseña.
        for control in formulario.winfo_children()[0].winfo_children():
            if isinstance(control, ttk.Entry) and str(control.cget("textvariable")) == str(formulario.campos.get("password")):
                control.configure(show="*")
            if fila and isinstance(control, ttk.Entry) and str(control.cget("textvariable")) == str(formulario.campos["usuario"]):
                control.configure(state="disabled")
        return formulario

    def registrar(self):
        return self.formulario()

    def modificar(self):
        return self.formulario(self.seleccionado(self.tabla, self.filas))

    def password(self):
        fila = self.seleccionado(self.tabla, self.filas)
        valor = simpledialog.askstring("Cambiar contraseña", f"Nueva contraseña para {fila['usuario']}:", show="*", parent=self.raiz)
        if valor is not None:
            self.servicio.cambiar_password(self.sesion, fila["id"], valor)
            messagebox.showinfo("Contraseña actualizada", "Las sesiones de ese usuario fueron revocadas.", parent=self.raiz)

    def cambiar_estado(self, activo):
        fila = self.seleccionado(self.tabla, self.filas)
        if messagebox.askyesno("Estado de usuario", f"¿{'Reactivar' if activo else 'Desactivar'} a {fila['usuario']}?", parent=self.raiz):
            self.servicio.cambiar_estado_usuario(self.sesion, fila["id"], activo)
            self.refrescar(fila["id"])


class AuditoriaApp(VentanaBase):
    def __init__(self, raiz, repositorio):
        repositorio.autorizar("Auditoría")
        super().__init__(raiz, repositorio, "Auditoría")
        raiz.geometry("1240x700")
        self.servicio, self.sesion = repositorio._servicio, repositorio._sesion
        barra = ttk.Frame(self.cuerpo)
        barra.pack(fill="x", pady=8)
        self.tabla_filtro, self.accion = tk.StringVar(raiz), tk.StringVar(raiz)
        ttk.Label(barra, text="Tabla:").pack(side="left")
        ttk.Combobox(barra, textvariable=self.tabla_filtro, values=("", "Usuarios", "Pacientes", "Profesionales", "SignosVitales", "Prescripciones", "Especialidades", "Farmacos", "SnomedCT"), state="readonly", width=20).pack(side="left", padx=6)
        ttk.Label(barra, text="Acción:").pack(side="left")
        ttk.Combobox(barra, textvariable=self.accion, values=("", "A", "M", "B", "R", "L", "X", "E", "I", "C"), state="readonly", width=5).pack(side="left", padx=6)
        ttk.Button(barra, text="Actualizar", command=lambda: self.intentar(self.refrescar)).pack(side="left", padx=8)
        ttk.Button(barra, text="Ver detalle", command=lambda: self.intentar(self.detalle)).pack(side="left", padx=8)
        ttk.Label(self.cuerpo, text="A Alta · M Modificación · B Baja · R Reactivación · L Login · X Logout · E Exportación. Fechas en UTC.").pack(anchor="w", pady=8)
        marco, self.tabla = crear_tabla(self.cuerpo, (("id", "ID", 55), ("fecha", "Fecha UTC", 190),
            ("usuario", "Usuario autor", 180), ("tabla", "Tabla", 180),
            ("registro", "Registro", 80), ("accion", "Acción", 80)))
        marco.pack(fill="both", expand=True)
        self.refrescar()

    def refrescar(self):
        self.filas = {f["id"]: f for f in self.servicio.listar_auditoria(self.sesion, tabla=self.tabla_filtro.get(), accion=self.accion.get())}
        self.tabla.delete(*self.tabla.get_children())
        for i, f in self.filas.items():
            self.tabla.insert("", "end", iid=str(i), values=(i, f["fecha_hora"], f["usuario_nombre"], f["tabla_afectada"], f["registro_id"], f["tipo_accion"]))

    def detalle(self):
        fila = self.seleccionado(self.tabla, self.filas)
        ventana = tk.Toplevel(self.raiz)
        ventana.title(f"Auditoría #{fila['id']}")
        texto = ScrolledText(ventana, width=105, height=30, wrap="word")
        texto.pack(fill="both", expand=True)
        texto.insert("1.0", "\n\n".join(f"{k}: {v}" for k, v in fila.items()))
        texto.configure(state="disabled")
        return ventana
