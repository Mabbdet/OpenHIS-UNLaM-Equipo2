"""Cierre del Epic 2: preanálisis FHIR y herramientas DICOM con visor."""

import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from PIL import ImageTk

from datos import ErrorValidacion
from entrega9_app import BaseE9, FHIRApp
import fhir
import dicom
import dicom_visor

RAIZ=Path(__file__).resolve().parent


class FHIRConfirmApp(FHIRApp):
    def __init__(self,raiz,repositorio):
        super().__init__(raiz,repositorio)
        raiz.title('OpenHIS-UNLaM · FHIR: análisis y confirmación')
        raiz.geometry('1120x780')
        self.plan=None
        for w in self.cuerpo.winfo_children():
            if isinstance(w,ttk.Button) and w.cget('text')=='Importar JSON / XML':
                w.configure(text='Analizar y mostrar JSON / XML')
        self.boton_confirmar=ttk.Button(self.cuerpo,text='Confirmar e importar a Salud.db',state='disabled',command=lambda:self.intentar(self.confirmar))
        self.boton_confirmar.pack(side='bottom',fill='x',pady=8)
        self.origen.trace_add('write',lambda *a:self.invalidar())

    def invalidar(self):
        self.plan=None;self.boton_confirmar.configure(state='disabled')

    def importar(self,archivo=None):
        return self.analizar(archivo)

    def analizar(self,archivo=None):
        self.invalidar()
        archivo=archivo or filedialog.askopenfilename(parent=self.raiz,filetypes=[('FHIR','*.json *.xml')],initialdir=RAIZ/'intercambio')
        if not archivo:return
        self.texto.delete('1.0','end')
        try:self.plan=fhir.preparar_importacion(self.repositorio,archivo,self.origen.get())
        except (ValueError,OSError) as error:
            self.mostrar({'importacion_bloqueada':str(error),'base_modificada':False});raise
        self.mostrar({'archivo':self.plan.archivo,'base_modificada':False,'acciones_previstas':self.plan.resumen,
                      'FHIR':json.loads(self.plan.contenido_json)})
        self.boton_confirmar.configure(state='normal')
        return self.plan

    def confirmar(self):
        if self.plan is None:raise ErrorValidacion('Analice primero el archivo.')
        if not messagebox.askyesno('Confirmar importación','¿Aplicar las acciones revisadas a Salud.db?\nEl lote se guardará completo o se revertirá si falla.',parent=self.raiz):return
        plan=self.plan;self.invalidar()
        resultado=fhir.confirmar_importacion(self.repositorio,plan,confirmado=True)
        self.mostrar({'importacion_completada':resultado})
        self.pacientes=self.repositorio.listar_pacientes(None)
        self.paciente['values']=[f"{f['dni']} · {f['apellido']}, {f['nombre']}" for f in self.pacientes]
        self.profesionales=self.repositorio.listar_profesionales()
        self.profesional['values']=[f"{f['matricula']} · {f['apellido']}" for f in self.profesionales]
        return resultado


class DICOMVisorApp(BaseE9):
    def __init__(self,raiz,repositorio):
        repositorio.autorizar('DICOM')
        super().__init__(raiz,repositorio,'Herramientas DICOM y visor')
        raiz.geometry('1200x850')
        self.libro=ttk.Notebook(self.cuerpo);self.libro.pack(fill='both',expand=True)
        self.conversion=ttk.Frame(self.libro,padding=10);self.anonimo=ttk.Frame(self.libro,padding=10);self.visor=ttk.Frame(self.libro,padding=10)
        for pagina,titulo in [(self.conversion,'JPG/PNG a DICOM'),(self.anonimo,'Anonimizar DICOM'),(self.visor,'Visor DICOM')]:self.libro.add(pagina,text=titulo)
        self.imagen=tk.StringVar(raiz);self.archivo=tk.StringVar(raiz);self.ruta_visor=tk.StringVar(raiz)
        self.campos={k:tk.StringVar(raiz,value=v) for k,v in {
            'patient_name':'','patient_id':'','birth_date':'','sex':'','study_date':'','study_time':'',
            'study_description':'','series_description':'Secondary Capture','study_id':'','accession_number':'',
            'referring_physician':'','performing_physician':'','institution':'Hospital Universitario San Justo',
            'institution_address':'San Justo - Buenos Aires','modality':'OT'}.items()}
        self._selector_archivo(self.conversion,self.imagen,'Imagen JPG/PNG',self.elegir_imagen)
        self.pacientes=repositorio.listar_pacientes();self.profesionales=repositorio.listar_profesionales()
        self.selector_paciente=ttk.Combobox(self.conversion,state='readonly',values=['Sin vincular']+[f"{f['dni']} · {f['apellido']}, {f['nombre']}" for f in self.pacientes])
        self.selector_paciente.pack(fill='x',pady=4);self.selector_paciente.current(0)
        self.selector_paciente.bind('<<ComboboxSelected>>',lambda e:self.cargar_paciente())
        self.selector_profesional=ttk.Combobox(self.conversion,state='readonly',values=['Profesional no informado']+[f"{f['matricula']} · {f['apellido']}" for f in self.profesionales])
        self.selector_profesional.pack(fill='x',pady=4);self.selector_profesional.current(0)
        self.selector_profesional.bind('<<ComboboxSelected>>',lambda e:self.cargar_profesional())
        formulario=ttk.Frame(self.conversion);formulario.pack(fill='x',pady=5)
        etiquetas={'patient_name':'Paciente','patient_id':'ID / DNI','birth_date':'Nacimiento AAAA-MM-DD','sex':'Sexo M/F/O',
            'study_date':'Estudio AAAA-MM-DD','study_time':'Hora HH:MM','study_description':'Descripción estudio','series_description':'Descripción serie',
            'study_id':'ID estudio','accession_number':'N.º acceso','referring_physician':'Profesional solicitante','performing_physician':'Profesional realizador',
            'institution':'Institución','institution_address':'Dirección institución','modality':'Modalidad'}
        for i,(k,var) in enumerate(self.campos.items()):
            fila,col=i//2,(i%2)*2
            ttk.Label(formulario,text=etiquetas[k]).grid(row=fila,column=col,sticky='w',padx=4,pady=4)
            ttk.Entry(formulario,textvariable=var,width=32).grid(row=fila,column=col+1,sticky='ew',padx=6,pady=4)
        formulario.columnconfigure(1,weight=1);formulario.columnconfigure(3,weight=1)
        ttk.Button(self.conversion,text='Convertir y guardar DICOM',command=lambda:self.intentar(self.convertir)).pack(anchor='w',pady=10)
        ttk.Label(self.conversion,text='Secondary Capture. Los datos elegidos se guardan como metadatos identificatorios; anonimice una copia antes de compartir.',wraplength=1000).pack(anchor='w')
        self._selector_archivo(self.anonimo,self.archivo,'DICOM de origen',self.elegir_dicom)
        ttk.Label(self.anonimo,text=dicom.AVISO,wraplength=1000).pack(anchor='w',pady=14)
        ttk.Button(self.anonimo,text='Anonimizar y guardar copia',command=lambda:self.intentar(self.anonimizar)).pack(anchor='w')
        self.salida=tk.StringVar(raiz);ttk.Label(self.anonimo,textvariable=self.salida,wraplength=1000).pack(anchor='w',pady=15)
        self._selector_archivo(self.visor,self.ruta_visor,'Archivo DICOM',self.elegir_visor)
        ttk.Button(self.visor,text='Mostrar metadatos e imagen',command=lambda:self.intentar(self.visualizar)).pack(anchor='w',pady=5)
        panel=ttk.Panedwindow(self.visor,orient='horizontal');panel.pack(fill='both',expand=True)
        meta=ttk.Frame(panel);vista=ttk.Frame(panel);panel.add(meta,weight=3);panel.add(vista,weight=2)
        self.texto=ScrolledText(meta,wrap='none',font=('Consolas',9));self.texto.pack(fill='both',expand=True)
        horizontal=ttk.Scrollbar(meta,orient='horizontal',command=self.texto.xview)
        horizontal.pack(fill='x');self.texto.configure(xscrollcommand=horizontal.set)
        self.imagen_label=ttk.Label(vista,text='Abra una imagen DICOM.',anchor='center');self.imagen_label.pack(fill='both',expand=True)
        self.aviso=tk.StringVar(raiz);ttk.Label(vista,textvariable=self.aviso,wraplength=390).pack(fill='x',pady=8)
        ttk.Label(self.visor,text='Vista previa básica no diagnóstica. La última visualización se registra en Auditoria; el archivo se conserva intacto.').pack(anchor='w',pady=8)
        self.imagen_tk=None

    def _selector_archivo(self,padre,var,titulo,accion):
        barra=ttk.Frame(padre);barra.pack(fill='x',pady=6)
        ttk.Label(barra,text=titulo).pack(side='left');ttk.Entry(barra,textvariable=var).pack(side='left',fill='x',expand=True,padx=8)
        ttk.Button(barra,text='Examinar',command=accion).pack(side='left')

    def cargar_paciente(self):
        i=self.selector_paciente.current()-1
        datos={} if i<0 else self.pacientes[i]
        for k,v in {'patient_name':f"{datos.get('apellido','')}^{datos.get('nombre','')}" if datos else '',
                    'patient_id':datos.get('dni',''),'birth_date':datos.get('fecha_nacimiento',''),
                    'sex':datos.get('sexo','') if datos.get('sexo') in ('M','F','O') else ''}.items():self.campos[k].set(v or '')

    def cargar_profesional(self):
        i=self.selector_profesional.current()-1
        valor='' if i<0 else f"{self.profesionales[i]['apellido']}^{self.profesionales[i]['nombre']}"
        self.campos['referring_physician'].set(valor);self.campos['performing_physician'].set(valor)

    def elegir_imagen(self):
        p=filedialog.askopenfilename(parent=self.raiz,initialdir=RAIZ/'IMAGENES/RX',filetypes=[('Imagen','*.jpg *.jpeg *.png')])
        if p:self.imagen.set(p)

    def elegir_dicom(self):
        p=filedialog.askopenfilename(parent=self.raiz,initialdir=RAIZ/'IMAGENES/RX/DICOM',filetypes=[('DICOM','*.dcm')])
        if p:self.archivo.set(p)

    def elegir_visor(self):
        p=filedialog.askopenfilename(parent=self.raiz,initialdir=RAIZ/'IMAGENES/RX/DICOM',filetypes=[('DICOM','*.dcm')])
        if p:self.ruta_visor.set(p);self.intentar(self.visualizar)

    def convertir(self,destino=None):
        destino=destino or filedialog.asksaveasfilename(parent=self.raiz,initialdir=RAIZ/'IMAGENES/RX/DICOM',defaultextension='.dcm')
        if not destino:return
        ruta=dicom.convertir(self.repositorio,self.imagen.get(),destino,metadatos={k:v.get() for k,v in self.campos.items()})
        self.archivo.set(str(ruta));self.ruta_visor.set(str(ruta));self.visualizar();return ruta

    def anonimizar(self,destino=None):
        destino=destino or filedialog.asksaveasfilename(parent=self.raiz,initialdir=RAIZ/'IMAGENES/RX/DICOM',defaultextension='.dcm')
        if not destino:return
        ruta=dicom.anonimizar(self.repositorio,self.archivo.get(),destino)
        self.salida.set(f'Copia anonimizada: {ruta}');self.ruta_visor.set(str(ruta));self.visualizar();return ruta

    def visualizar(self):
        resultado=dicom_visor.visualizar(self.repositorio,self.ruta_visor.get())
        self.libro.select(self.visor)
        self.texto.delete('1.0','end');self.texto.insert('1.0',resultado['metadatos']);self.aviso.set(resultado['aviso'])
        if resultado['imagen'] is None:
            self.imagen_tk=None;self.imagen_label.configure(image='',text='Metadatos disponibles.\nNo se pudo previsualizar la imagen.')
        else:
            im=resultado['imagen'].copy();im.thumbnail((440,520))
            self.imagen_tk=ImageTk.PhotoImage(im,master=self.raiz);self.imagen_label.configure(image=self.imagen_tk,text='')
        return resultado
