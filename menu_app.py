"""Navegación común y arranque de los módulos independientes de OpenHIS."""

import sqlite3
import tkinter as tk
from tkinter import ttk

from datos import ErrorValidacion, Repositorio
from interfaz import AplicacionPacientes, mostrar_error
from signos_app import SignosApp
from ventanas_clinicas import ProfesionalesApp, PrescripcionesApp, TablasMaestrasApp, VentanaBase


MODULOS = {"Pacientes": lambda raiz, repo: AplicacionPacientes(raiz, repo, modo="crud"),
           "Profesionales": ProfesionalesApp, "Signos vitales": SignosApp,
           "Prescripciones": PrescripcionesApp, "Tablas maestras": TablasMaestrasApp}


class MenuApp(VentanaBase):
    def __init__(self, raiz, repositorio=None):
        super().__init__(raiz, repositorio, "Menú principal")
        raiz.geometry("760x600")
        raiz.minsize(700, 540)
        self.ventanas = {}
        ttk.Label(self.cuerpo, text="Seleccione el módulo de trabajo. Todos comparten la misma base de datos.", wraplength=650).pack(anchor="w", pady=12)
        for nombre in MODULOS:
            ttk.Button(self.cuerpo, text=nombre, command=lambda n=nombre: self.abrir(n)).pack(fill="x", pady=8, ipady=5)
        ttk.Label(self.cuerpo, text="Proyecto académico · Alejandro · Entrega 5", foreground="#526773").pack(anchor="w", pady=16)

    def abrir(self, nombre):
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
        except (ErrorValidacion, sqlite3.Error) as error:
            mostrar_error(self.raiz, error)
            ventana.destroy()


def ejecutar_modulo(nombre=None):
    raiz = tk.Tk()
    try:
        repositorio = Repositorio()
        if nombre is None:
            MenuApp(raiz, repositorio)
        else:
            MODULOS[nombre](raiz, repositorio)
    except (ErrorValidacion, sqlite3.Error) as error:
        mostrar_error(raiz, error)
        raiz.destroy()
        return
    raiz.mainloop()
