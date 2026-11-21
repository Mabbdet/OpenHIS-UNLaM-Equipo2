"""Interfaces autenticadas de consulta, intercambio e imágenes de Entrega 9."""

import json
from datetime import datetime
from pathlib import Path
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

from datos import ErrorValidacion
from interfaz import crear_tabla
from ventanas_clinicas import VentanaBase
import intervenciones
import fhir
import dicom

RAIZ=Path(__file__).resolve().parent


class BaseE9(VentanaBase):
    def intentar(self, operacion):
        try: return operacion()
        except (ValueError,OSError,sqlite3.Error) as error:
            messagebox.showerror('Operación no realizada',str(error),parent=self.raiz)


class IntervencionesApp(BaseE9):
    def __init__(self, raiz, repositorio):
        repositorio.autorizar('Intervenciones')
        super().__init__(raiz,repositorio,'Consulta de intervenciones')
        barra=ttk.Frame(self.cuerpo);barra.pack(fill='x',pady=8)
        self.busqueda=tk.StringVar(raiz)
        ttk.Label(barra,text='DNI, nombre o apellido:').pack(side='left')
        ttk.Entry(barra,textvariable=self.busqueda,width=28).pack(side='left',padx=8)
        ttk.Button(barra,text='Buscar',command=lambda:self.intentar(self.buscar)).pack(side='left')
        self.lista=ttk.Combobox(self.cuerpo,state='readonly',width=100);self.lista.pack(fill='x',pady=8)
        self.lista.bind('<<ComboboxSelected>>',lambda e:self.intentar(self.consultar))
        ttk.Button(self.cuerpo,text='Consultar / Actualizar',command=lambda:self.intentar(self.consultar)).pack(anchor='w',pady=6)
        self.texto=ScrolledText(self.cuerpo,wrap='word',font=('Consolas',10));self.texto.pack(fill='both',expand=True)
        self.buscar()

    def buscar(self):
        texto=self.busqueda.get().casefold().strip()
        self.pacientes=[f for f in self.repositorio.listar_pacientes(None) if texto in f"{f['dni']} {f['nombre']} {f['apellido']}".casefold()]
        self.lista['values']=[f"{f['apellido']}, {f['nombre']} · DNI {f['dni']} · {'Activo' if f['activo'] else 'Inactivo'}" for f in self.pacientes]
        self.lista.set('');self.texto.delete('1.0','end')
        if self.pacientes:self.lista.current(0)

    def consultar(self):
        if self.lista.current()<0:raise ErrorValidacion('Seleccione un paciente.')
        resultado=intervenciones.consultar(self.repositorio,self.pacientes[self.lista.current()]['id'])
        lineas=[f"HC {resultado['paciente']['id']} · {resultado['paciente']['nombre']} {resultado['paciente']['apellido']}",
                'Consulta registrada en auditoría. Fechas almacenadas en UTC.']
        for tabla in ('signos','prescripciones','practicas'):
            lineas += ['\n'+tabla.upper()]
            for f in resultado[tabla]:
                campos=('id','fecha_hora','fecha_prescripcion','fecha_solicitud','profesional','activo','motivo_consulta',
                        'presion_sistolica','presion_diastolica','frecuencia_cardiaca','temperatura','saturacion_oxigeno',
                        'farmaco','dosis','via_administracion','frecuencia','indicaciones','codigo','descripcion')
                lineas.append('\n'.join(f'{k}: {f[k]}' for k in campos if k in f and f[k] is not None)+'\n')
            if not resultado[tabla]:lineas.append('Sin registros.')
        self.texto.delete('1.0','end');self.texto.insert('1.0','\n'.join(lineas))
        return resultado


class FHIRApp(BaseE9):
    def __init__(self, raiz, repositorio):
        repositorio.autorizar('FHIR')
        super().__init__(raiz,repositorio,'Interoperabilidad FHIR R4')
        self.pacientes=repositorio.listar_pacientes(None);self.profesionales=repositorio.listar_profesionales()
        self.paciente=ttk.Combobox(self.cuerpo,state='readonly',values=[f"{f['dni']} · {f['apellido']}, {f['nombre']}" for f in self.pacientes]);self.paciente.pack(fill='x',pady=5)
        if self.pacientes:self.paciente.current(0)
        barra=ttk.Frame(self.cuerpo);barra.pack(fill='x',pady=6)
        for formato in ('json','xml'):
            ttk.Button(barra,text='Exportar FHIR '+formato.upper(),command=lambda f=formato:self.intentar(lambda:self.exportar(f))).pack(side='left',padx=4)
        self.origen=tk.StringVar(raiz,value='Institución externa de prueba')
        ttk.Label(self.cuerpo,text='Institución de origen para importar:').pack(anchor='w')
        ttk.Entry(self.cuerpo,textvariable=self.origen).pack(fill='x')
        ttk.Button(self.cuerpo,text='Importar JSON / XML',command=lambda:self.intentar(self.importar)).pack(anchor='w',pady=6)
        self.profesional=ttk.Combobox(self.cuerpo,state='readonly',values=[f"{f['matricula']} · {f['apellido']}" for f in self.profesionales]);self.profesional.pack(fill='x',pady=5)
        if self.profesionales:self.profesional.current(0)
        self.codigo=tk.StringVar(raiz);self.descripcion=tk.StringVar(raiz)
        campos=ttk.Frame(self.cuerpo);campos.pack(fill='x',pady=5)
        ttk.Label(campos,text='Código de práctica:').pack(side='left');ttk.Entry(campos,textvariable=self.codigo,width=20).pack(side='left',padx=5)
        ttk.Label(campos,text='Descripción:').pack(side='left');ttk.Entry(campos,textvariable=self.descripcion,width=35).pack(side='left',padx=5)
        ttk.Button(self.cuerpo,text='Registrar solicitud de práctica',command=lambda:self.intentar(self.registrar_practica)).pack(anchor='w',pady=5)
        self.texto=ScrolledText(self.cuerpo,wrap='word',font=('Consolas',9));self.texto.pack(fill='both',expand=True)

    def _paciente(self):
        if self.paciente.current()<0:raise ErrorValidacion('Seleccione un paciente.')
        return self.pacientes[self.paciente.current()]['id']

    def registrar_practica(self):
        if self.profesional.current()<0:raise ErrorValidacion('Seleccione un profesional.')
        i=intervenciones.registrar_practica(self.repositorio,self._paciente(),self.profesionales[self.profesional.current()]['id'],self.codigo.get(),self.descripcion.get())
        self.mostrar({'practica_creada':i})
        return i

    def mostrar(self, resultado):
        self.texto.delete('1.0','end');self.texto.insert('1.0',json.dumps(resultado,ensure_ascii=False,indent=2))

    def exportar(self, formato='json', destino=None):
        destino=destino or filedialog.asksaveasfilename(parent=self.raiz,defaultextension='.'+formato,initialfile='FHIR_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.'+formato)
        if not destino:return
        resultado=fhir.exportar(self.repositorio,self._paciente(),destino,formato)
        self.mostrar(resultado);return resultado

    def importar(self, archivo=None):
        archivo=archivo or filedialog.askopenfilename(parent=self.raiz,filetypes=[('FHIR','*.json *.xml')])
        if not archivo:return
        resultado=fhir.importar(self.repositorio,archivo,self.origen.get());self.mostrar(resultado);return resultado


class DICOMApp(BaseE9):
    def __init__(self, raiz, repositorio):
        repositorio.autorizar('DICOM')
        super().__init__(raiz,repositorio,'Imágenes DICOM')
        self.imagen=tk.StringVar(raiz);self.archivo=tk.StringVar(raiz)
        for etiqueta,var,selector in [('Imagen JPG/PNG',self.imagen,self.elegir_imagen),('Archivo DICOM',self.archivo,self.elegir_dicom)]:
            barra=ttk.Frame(self.cuerpo);barra.pack(fill='x',pady=5)
            ttk.Label(barra,text=etiqueta,width=20).pack(side='left');ttk.Entry(barra,textvariable=var).pack(side='left',fill='x',expand=True)
            ttk.Button(barra,text='Examinar',command=selector).pack(side='left',padx=5)
        barra=ttk.Frame(self.cuerpo);barra.pack(fill='x',pady=6)
        self.nacimiento=tk.StringVar(raiz);self.estudio=tk.StringVar(raiz);self.sexo=tk.StringVar(raiz)
        for texto,var in [('Año nacimiento',self.nacimiento),('Año estudio',self.estudio)]:
            ttk.Label(barra,text=texto).pack(side='left');ttk.Entry(barra,textvariable=var,width=8).pack(side='left',padx=6)
        ttk.Label(barra,text='Sexo').pack(side='left');ttk.Combobox(barra,textvariable=self.sexo,values=('','M','F','O'),state='readonly',width=5).pack(side='left')
        barra=ttk.Frame(self.cuerpo);barra.pack(fill='x',pady=6)
        for titulo,accion in [('Convertir JPG/PNG',self.convertir),('Anonimizar DICOM',self.anonimizar),('Ver metadatos',self.ver_metadatos)]:
            ttk.Button(barra,text=titulo,command=lambda a=accion:self.intentar(a)).pack(side='left',padx=4)
        ttk.Label(self.cuerpo,text=dicom.AVISO,wraplength=950,foreground='#8a3b12').pack(anchor='w',pady=8)
        self.texto=ScrolledText(self.cuerpo,wrap='word',font=('Consolas',9));self.texto.pack(fill='both',expand=True)

    def elegir_imagen(self):
        p=filedialog.askopenfilename(parent=self.raiz,filetypes=[('Imagen','*.png *.jpg *.jpeg')])
        if p:self.imagen.set(p)

    def elegir_dicom(self):
        p=filedialog.askopenfilename(parent=self.raiz,filetypes=[('DICOM','*.dcm')])
        if p:self.archivo.set(p)

    def convertir(self, destino=None):
        destino=destino or filedialog.asksaveasfilename(parent=self.raiz,defaultextension='.dcm')
        if not destino:return
        ruta=dicom.convertir(self.repositorio,self.imagen.get(),destino,self.nacimiento.get(),self.estudio.get(),self.sexo.get())
        self.archivo.set(str(ruta));self.ver_metadatos();return ruta

    def anonimizar(self, destino=None):
        destino=destino or filedialog.asksaveasfilename(parent=self.raiz,defaultextension='.dcm')
        if not destino:return
        ruta=dicom.anonimizar(self.repositorio,self.archivo.get(),destino)
        self.archivo.set(str(ruta));self.ver_metadatos();return ruta

    def ver_metadatos(self):
        resultado=dicom.metadatos(self.repositorio,self.archivo.get())
        self.texto.delete('1.0','end');self.texto.insert('1.0',json.dumps(resultado,ensure_ascii=False,indent=2));return resultado
