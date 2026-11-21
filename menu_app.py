"""Navegación con login obligatorio y permisos por rol (HU-07)."""

import sqlite3
import tkinter as tk
from tkinter import ttk

from datos import ErrorValidacion
from interfaz import AplicacionPacientes, mostrar_error
from seguridad import Seguridad, PERMISOS
from seguridad_app import AuditoriaApp, LoginApp, UsuariosApp
from entrega9_app import IntervencionesApp, FHIRApp, DICOMApp
from entrega10_app import FHIRConfirmApp, DICOMVisorApp
from signos_app import SignosApp
from ventanas_clinicas import ProfesionalesApp, PrescripcionesApp, TablasMaestrasApp, VentanaBase

MODULOS = {"Pacientes": lambda raiz, repo: AplicacionPacientes(raiz, repo, modo="crud"),
           "Profesionales": ProfesionalesApp, "Signos vitales": SignosApp,
           "Prescripciones": PrescripcionesApp, "Tablas maestras": TablasMaestrasApp,
           "Usuarios": UsuariosApp, "Auditoría": AuditoriaApp,
           'Intervenciones': IntervencionesApp, 'FHIR': FHIRConfirmApp, 'DICOM': DICOMVisorApp}


class MenuApp(VentanaBase):
    def __init__(self, raiz, repositorio, al_salir=None):
        actor = repositorio.autorizar()
        super().__init__(raiz, repositorio, "Menú principal")
        raiz.geometry("760x760")
        raiz.minsize(700, 700)
        self.ventanas, self.botones = {}, {}
        ttk.Label(self.cuerpo, text=f"{actor['nombre_completo']} ({actor['usuario']}) · Rol: {actor['rol']}").pack(anchor="w", pady=10)
        panel=ttk.Frame(self.cuerpo);panel.pack(fill='both',expand=True)
        panel.columnconfigure(0,weight=1);panel.columnconfigure(1,weight=1)
        cantidad=0
        for nombre in MODULOS:
            if actor["rol"] in PERMISOS[nombre]:
                boton = ttk.Button(panel, text=nombre, command=lambda n=nombre: self.intentar(lambda: self.abrir(n)))
                boton.grid(row=cantidad//2,column=cantidad%2,sticky='ew',padx=5,pady=8,ipady=8)
                cantidad+=1
                self.botones[nombre] = boton
        if al_salir:
            ttk.Button(self.cuerpo, text="Cerrar sesión", command=al_salir).pack(fill="x", pady=12)
        ttk.Label(self.cuerpo, text="Proyecto académico · Alejandro · Entrega 10", foreground="#526773").pack(anchor="w", pady=12)

    def abrir(self, nombre):
        self.repositorio.autorizar(nombre)
        if nombre in self.ventanas and self.ventanas[nombre].raiz.winfo_exists():
            app = self.ventanas[nombre]
            app.raiz.deiconify()
            app.raiz.lift()
            return app
        ventana = tk.Toplevel(self.raiz)
        try:
            app = MODULOS[nombre](ventana, self.repositorio)
            self.ventanas[nombre] = app
            return app
        except (ErrorValidacion, sqlite3.Error):
            ventana.destroy()
            raise


def ejecutar_modulo(nombre=None, modo="crud"):
    raiz = tk.Tk()
    sesion_actual = [None]
    try:
        servicio = Seguridad()

        def salir(cerrar=False):
            try:
                servicio.cerrar_sesion(sesion_actual[0])
            except sqlite3.Error as error:
                mostrar_error(raiz, error)
                return
            sesion_actual[0] = None
            for hijo in raiz.winfo_children():
                hijo.destroy()
            if cerrar:
                raiz.destroy()
            else:
                LoginApp(raiz, servicio, ingresar)

        def ingresar(sesion):
            sesion_actual[0] = sesion
            repo = servicio.repositorio(sesion)
            try:
                if nombre is None:
                    MenuApp(raiz, repo, al_salir=salir)
                else:
                    repo.autorizar(nombre)
                    app = AplicacionPacientes(raiz, repo, modo=modo) if nombre == "Pacientes" else MODULOS[nombre](raiz, repo)
                    ttk.Button(app.cuerpo, text="Cerrar sesión", command=salir).pack(side="bottom", pady=6)
            except (ErrorValidacion, sqlite3.Error) as error:
                mostrar_error(raiz, error)
                salir()

        raiz.protocol("WM_DELETE_WINDOW", lambda: salir(cerrar=True))
        LoginApp(raiz, servicio, ingresar)
    except (ErrorValidacion, sqlite3.Error) as error:
        mostrar_error(raiz, error)
        raiz.destroy()
        return
    raiz.mainloop()
