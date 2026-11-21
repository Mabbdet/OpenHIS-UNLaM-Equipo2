"""Interfaces del Epic 3 integradas con sesión y servicios transaccionales."""

from datetime import datetime, timezone
import json
import tkinter as tk
from tkinter import ttk, simpledialog
from tkinter.scrolledtext import ScrolledText

from datos import ErrorValidacion
from interfaz import crear_tabla
from ventanas_clinicas import VentanaBase
import turnos
import hce
import portal


def entrada(padre, titulo, fila, valor='', columna=0, ancho=22):
    ttk.Label(padre,text=titulo).grid(row=fila,column=columna,sticky='w',padx=4,pady=4)
    var=tk.StringVar(padre,value=valor)
    ttk.Entry(padre,textvariable=var,width=ancho).grid(row=fila,column=columna+1,sticky='ew',padx=4,pady=4)
    return var


class Selector:
    def __init__(self,padre,filas,etiqueta,todos=False):
        self.mapa={('Todos' if todos else 'Seleccione'):None}
        self.mapa.update({f"{f['id']} · {etiqueta(f)}":f['id'] for f in filas})
        self.control=ttk.Combobox(padre,state='readonly',values=list(self.mapa),width=48)
        self.control.current(0)
    def valor(self,obligatorio=True):
        resultado=self.mapa.get(self.control.get())
        if obligatorio and resultado is None:raise ErrorValidacion('Complete la selección.')
        return resultado
    def seleccionar(self,registro_id):
        self.control.set(next((k for k,v in self.mapa.items() if v==registro_id),'Seleccione'))


def profesionales(padre,repo,todos=False):
    return Selector(padre,repo.listar_profesionales(),lambda f:f"{f['apellido']}, {f['nombre']} · {f['matricula']}",todos)


def pacientes(padre,repo,todos_estados=False):
    return Selector(padre,repo.listar_pacientes(None if todos_estados else True),lambda f:f"{f['apellido']}, {f['nombre']} · DNI {f['dni']}"+(' · Inactivo' if not f['activo'] else ''))


def tabla(padre,columnas,altura=9):
    marco,control=crear_tabla(padre,[(k,t,ancho) for k,t,ancho in columnas],altura)
    marco.pack(fill='both',expand=True,pady=6)
    return control


def poblar(control,filas,columnas):
    control.delete(*control.get_children())
    for f in filas:control.insert('', 'end',iid=str(f['id']),values=[f.get(k,'') if f.get(k) is not None else '' for k in columnas],tags=(str(f.get('estado','')),))


def seleccionado(control):
    if not control.selection():raise ErrorValidacion('Seleccione un registro de la tabla.')
    return int(control.selection()[0])


def colores(control):
    for estado,color in [('SOLICITADO','#fff3cd'),('CONFIRMADO','#e3f0df'),('ATENDIDO','#dcecf8'),('CANCELADO','#eeeeee'),('REPROGRAMADO','#f2e7f7'),('AUSENTE','#fbe0dc')]:
        control.tag_configure(estado,background=color)


class AgendaProfesionalApp(VentanaBase):
    def __init__(self,raiz,repo):
        actor=repo.autorizar('Agenda profesional');super().__init__(raiz,repo,'Agenda profesional')
        raiz.geometry('1180x790')
        ttk.Label(self.cuerpo,text='Horarios de atención: Argentina UTC-03. Los turnos registrados conservan su fecha y horario.').pack(anchor='w',pady=4)
        self.pro=profesionales(self.cuerpo,repo);self.pro.control.pack(fill='x')
        self.tabs=ttk.Notebook(self.cuerpo);self.tabs.pack(fill='both',expand=True,pady=7)
        disp=ttk.Frame(self.tabs,padding=8);bloq=ttk.Frame(self.tabs,padding=8);dia=ttk.Frame(self.tabs,padding=8)
        for pagina,titulo in [(disp,'Disponibilidad semanal'),(bloq,'Bloqueos y excepciones'),(dia,'Agenda diaria')]:self.tabs.add(pagina,text=titulo)
        f=ttk.Frame(disp);f.pack(fill='x')
        ttk.Label(f,text='Día (lunes=0)').grid(row=0,column=0,sticky='w')
        self.dia=tk.StringVar(f,value=str(turnos.ahora().weekday()))
        ttk.Combobox(f,textvariable=self.dia,state='readonly',values=list(map(str,range(7))),width=10).grid(row=0,column=1,sticky='w')
        self.inicio=entrada(f,'Desde HH:MM',1,'08:00');self.fin=entrada(f,'Hasta HH:MM',2,'12:00')
        self.duracion=entrada(f,'Duración (minutos)',0,'30',2)
        self.desde=entrada(f,'Vigencia desde AAAA-MM-DD',1,turnos.ahora().date().isoformat(),2)
        self.hasta=entrada(f,'Vigencia hasta (opcional)',2,'',2)
        barra=ttk.Frame(disp);barra.pack(fill='x',pady=5)
        for titulo,accion in [('Registrar franja',lambda:self.guardar_disponibilidad()),('Modificar seleccionada',lambda:self.guardar_disponibilidad(True)),('Desactivar seleccionada',self.desactivar_disponibilidad)]:
            ttk.Button(barra,text=titulo,command=lambda a=accion:self.intentar(a),state='normal' if actor['rol']=='admin' else 'disabled').pack(side='left',padx=3)
        self.disponibilidad=tabla(disp,[('id','ID',45),('dia_semana','Día',50),('hora_inicio','Desde',80),('hora_fin','Hasta',80),('duracion_minutos','Minutos',75),('fecha_desde','Vigente desde',115),('fecha_hasta','Hasta',115),('activo','Activo',70)])
        self.disponibilidad.bind('<<TreeviewSelect>>',lambda e:self.cargar_disponibilidad())
        g=ttk.Frame(bloq);g.pack(fill='x')
        self.bfecha=entrada(g,'Fecha AAAA-MM-DD',0,turnos.ahora().date().isoformat())
        self.binicio=entrada(g,'Inicio HH:MM (opcional)',1);self.bfin=entrada(g,'Fin HH:MM (opcional)',2)
        self.btipo=tk.StringVar(g,value='BLOQUEO')
        ttk.Label(g,text='Tipo').grid(row=0,column=2,sticky='w');ttk.Combobox(g,textvariable=self.btipo,state='readonly',values=['BLOQUEO','VACACIONES','LICENCIA','OTRO']).grid(row=0,column=3,padx=4)
        self.bmotivo=entrada(g,'Motivo',1,'',2,45)
        ttk.Label(g,text='Ambas horas vacías: día completo. Un bloqueo no puede ocupar un turno solicitado o confirmado.').grid(row=2,column=2,columnspan=2,sticky='w')
        barra=ttk.Frame(bloq);barra.pack(fill='x',pady=5)
        for titulo,accion in [('Registrar bloqueo',self.guardar_bloqueo),('Desactivar bloqueo',self.desactivar_bloqueo)]:
            ttk.Button(barra,text=titulo,command=lambda a=accion:self.intentar(a),state='normal' if actor['rol']=='admin' else 'disabled').pack(side='left',padx=3)
        self.bloqueos=tabla(bloq,[('id','ID',45),('fecha','Fecha',110),('hora_inicio','Desde',75),('hora_fin','Hasta',75),('tipo','Tipo',110),('motivo','Motivo',260),('activo','Activo',65)])
        barra=ttk.Frame(dia);barra.pack(fill='x')
        self.fecha=tk.StringVar(dia,value=turnos.ahora().date().isoformat())
        ttk.Entry(barra,textvariable=self.fecha,width=15).pack(side='left');ttk.Button(barra,text='Consultar agenda',command=lambda:self.intentar(self.consultar_agenda)).pack(side='left',padx=6)
        self.agenda=tabla(dia,[('id','N.º',45),('hora_inicio','Desde',75),('hora_fin','Hasta',75),('paciente','Paciente',200),('profesional','Profesional',200),('estado','Estado',120),('motivo_consulta','Motivo',230)])
        colores(self.agenda)
        self.estado=tk.StringVar(raiz);ttk.Label(self.cuerpo,textvariable=self.estado).pack(anchor='w')
        ttk.Button(self.cuerpo,text='Actualizar configuración',command=lambda:self.intentar(self.refrescar)).pack(anchor='w')
        self.pro.control.bind('<<ComboboxSelected>>',lambda e:self.intentar(self.refrescar))
        self.refrescar()

    def refrescar(self):
        datos=turnos.configuracion(self.repositorio,self.pro.valor(False));self.franjas={f['id']:f for f in datos['DisponibilidadProfesional']}
        poblar(self.disponibilidad,datos['DisponibilidadProfesional'],('id','dia_semana','hora_inicio','hora_fin','duracion_minutos','fecha_desde','fecha_hasta','activo'))
        poblar(self.bloqueos,datos['BloqueosAgenda'],('id','fecha','hora_inicio','hora_fin','tipo','motivo','activo'))

    def cargar_disponibilidad(self):
        if not self.disponibilidad.selection():return
        f=self.franjas[int(self.disponibilidad.selection()[0])];self.pro.seleccionar(f['profesional_id'])
        for var,campo in [(self.dia,'dia_semana'),(self.inicio,'hora_inicio'),(self.fin,'hora_fin'),(self.duracion,'duracion_minutos'),(self.desde,'fecha_desde'),(self.hasta,'fecha_hasta')]:var.set(f[campo] if f[campo] is not None else '')

    def guardar_disponibilidad(self,modificar=False):
        i=turnos.guardar_disponibilidad(self.repositorio,dict(profesional_id=self.pro.valor(),dia_semana=self.dia.get(),hora_inicio=self.inicio.get(),hora_fin=self.fin.get(),duracion_minutos=self.duracion.get(),fecha_desde=self.desde.get(),fecha_hasta=self.hasta.get()),seleccionado(self.disponibilidad) if modificar else None)
        self.refrescar();self.estado.set(f'Franja {i} guardada. Los turnos existentes se conservaron.');return i

    def desactivar_disponibilidad(self):
        turnos.desactivar_disponibilidad(self.repositorio,seleccionado(self.disponibilidad));self.refrescar()

    def guardar_bloqueo(self):
        i=turnos.guardar_bloqueo(self.repositorio,dict(profesional_id=self.pro.valor(),fecha=self.bfecha.get(),hora_inicio=self.binicio.get(),hora_fin=self.bfin.get(),tipo=self.btipo.get(),motivo=self.bmotivo.get()))
        self.refrescar();self.estado.set(f'Bloqueo {i} registrado.');return i

    def desactivar_bloqueo(self):
        turnos.desactivar_bloqueo(self.repositorio,seleccionado(self.bloqueos));self.refrescar()

    def consultar_agenda(self):
        datos=turnos.agenda_diaria(self.repositorio,self.fecha.get(),self.pro.valor(False))
        poblar(self.agenda,datos,('id','hora_inicio','hora_fin','paciente','profesional','estado','motivo_consulta'));return datos


class GestionTurnosApp(VentanaBase):
    def __init__(self,raiz,repo):
        repo.autorizar('Turnos');super().__init__(raiz,repo,'Turnero telefónico')
        raiz.geometry('1200x820')
        self.tabs=ttk.Notebook(self.cuerpo);self.tabs.pack(fill='both',expand=True)
        reserva=ttk.Frame(self.tabs,padding=8);gestion=ttk.Frame(self.tabs,padding=8)
        self.tabs.add(reserva,text='Disponibilidad y reserva');self.tabs.add(gestion,text='Gestión de turnos')
        self.paciente=pacientes(reserva,repo);self.paciente.control.pack(fill='x',pady=3)
        self.pro=profesionales(reserva,repo,True);self.pro.control.pack(fill='x',pady=3)
        self.especialidad=Selector(reserva,repo.listar_catalogo('especialidades',solo_activos=True),lambda f:f['nombre'],True);self.especialidad.control.pack(fill='x',pady=3)
        form=ttk.Frame(reserva);form.pack(fill='x')
        self.fecha=entrada(form,'Fecha AAAA-MM-DD',0,turnos.ahora().date().isoformat())
        self.dni=entrada(form,'DNI verificado al confirmar',0,'',2)
        self.motivo=entrada(form,'Motivo',1,'',0,45);self.observaciones=entrada(form,'Observaciones',1,'',2,45)
        barra=ttk.Frame(reserva);barra.pack(fill='x',pady=4)
        for nombre,accion in [('Buscar huecos',self.buscar),('Reservar solicitado',self.reservar),('Reservar y confirmar',lambda:self.reservar(True)),('Asignar sugerido',self.sugerido)]:
            ttk.Button(barra,text=nombre,command=lambda a=accion:self.intentar(a)).pack(side='left',padx=3)
        ttk.Label(reserva,text='Argentina UTC-03. La confirmación requiere comprobar el DNI. Sugerido: primer horario, menor carga e ID del profesional; crea una solicitud.').pack(anchor='w')
        acceso=ttk.Frame(reserva);acceso.pack(fill='x',pady=4)
        ttk.Button(acceso,text='Habilitar / renovar acceso web',command=lambda:self.intentar(self.habilitar_web)).pack(side='left',padx=3)
        ttk.Button(acceso,text='Deshabilitar acceso web',command=lambda:self.intentar(self.deshabilitar_web)).pack(side='left',padx=3)
        self.huecos=tabla(reserva,[('profesional','Profesional',220),('especialidad','Especialidad',170),('fecha','Fecha',110),('hora_inicio','Desde',90),('hora_fin','Hasta',90)])
        self.estado=tk.StringVar(raiz);ttk.Label(reserva,textvariable=self.estado).pack(anchor='w')
        barra=ttk.Frame(gestion);barra.pack(fill='x')
        self.fecha_lista=tk.StringVar(raiz,value=turnos.ahora().date().isoformat())
        ttk.Entry(barra,textvariable=self.fecha_lista,width=16).pack(side='left')
        ttk.Button(barra,text='Actualizar agenda',command=lambda:self.intentar(self.actualizar)).pack(side='left',padx=5)
        self.turnos=tabla(gestion,[('id','N.º',50),('hora_inicio','Desde',80),('hora_fin','Hasta',80),('paciente','Paciente',180),('dni','DNI',100),('profesional','Profesional',180),('estado','Estado',120),('motivo_consulta','Motivo',220)])
        colores(self.turnos)
        barra=ttk.Frame(gestion);barra.pack(fill='x')
        for nombre,accion in [('Confirmar por DNI',self.confirmar),('Cancelar',self.cancelar),('Reprogramar al hueco elegido',self.reprogramar),('Atendido',lambda:self.asistencia('ATENDIDO')),('Ausente',lambda:self.asistencia('AUSENTE'))]:
            ttk.Button(barra,text=nombre,command=lambda a=accion:self.intentar(a)).pack(side='left',padx=3)
        ttk.Label(gestion,text='Para reprogramar, busque y seleccione primero un hueco en la pestaña de reserva. El paciente del turno se conserva.').pack(anchor='w',pady=6)
        self.actualizar()

    def habilitar_web(self):
        clave=portal.habilitar_acceso(self.repositorio,self.paciente.valor())
        ventana=tk.Toplevel(self.raiz);ventana.title('Acceso individual al turnero web');ventana.transient(self.raiz)
        marco=ttk.Frame(ventana,padding=20);marco.pack(fill='both',expand=True)
        ttk.Label(marco,text=self.paciente.control.get(),wraplength=500).pack(anchor='w',pady=6)
        ttk.Label(marco,text='Clave individual. Se muestra una vez. La renovación revoca los accesos anteriores.',wraplength=500).pack(anchor='w',pady=6)
        valor=tk.StringVar(ventana,value=clave)
        ttk.Entry(marco,textvariable=valor,state='readonly',width=42).pack(fill='x',pady=8)
        def copiar():ventana.clipboard_clear();ventana.clipboard_append(clave)
        ttk.Button(marco,text='Copiar clave',command=copiar).pack(side='left',padx=5)
        ttk.Button(marco,text='Cerrar',command=ventana.destroy).pack(side='right',padx=5)
        self.estado.set('Acceso web habilitado. Entregue la clave al paciente por el canal habitual.')

    def deshabilitar_web(self):
        portal.deshabilitar_acceso(self.repositorio,self.paciente.valor())
        self.estado.set('Acceso web deshabilitado y sesiones anteriores revocadas.')

    def buscar(self):
        datos=turnos.disponibles(self.repositorio,self.fecha.get(),self.pro.valor(False),self.especialidad.valor(False),self.paciente.valor(False))
        self.opciones={i:f for i,f in enumerate(datos,1)}
        poblar(self.huecos,[dict(f,id=i) for i,f in self.opciones.items()],('profesional','especialidad','fecha','hora_inicio','hora_fin'))
        self.estado.set(f'{len(datos)} huecos disponibles.');return datos

    def reservar(self,confirmado=False):
        if not hasattr(self,'opciones'):raise ErrorValidacion('Busque un hueco disponible.')
        h=self.opciones[seleccionado(self.huecos)]
        i=turnos.reservar(self.repositorio,self.paciente.valor(),h['profesional_id'],h['fecha'],h['hora_inicio'],self.motivo.get(),self.observaciones.get(),confirmado,self.dni.get())
        self.fecha_lista.set(h['fecha']);self.actualizar();self.buscar();self.estado.set(f'Turno {i} guardado.');return i

    def sugerido(self):
        resultado=turnos.reservar_sugerido(self.repositorio,self.paciente.valor(),self.especialidad.valor(),self.fecha.get(),self.motivo.get())
        self.fecha_lista.set(self.fecha.get());self.actualizar();self.buscar();self.estado.set(f"Turno {resultado['turno_id']} solicitado con {resultado['profesional']}, {resultado['hora_inicio']}.");return resultado

    def actualizar(self):
        datos=turnos.agenda_diaria(self.repositorio,self.fecha_lista.get())
        self.filas={f['id']:f for f in datos}
        poblar(self.turnos,datos,('id','hora_inicio','hora_fin','paciente','dni','profesional','estado','motivo_consulta'));return datos

    def confirmar(self,dni=None):
        i=seleccionado(self.turnos)
        dni=dni if dni is not None else simpledialog.askstring('Verificar identidad','DNI confirmado por teléfono:',parent=self.raiz)
        if dni is None:return
        turnos.cambiar_estado(self.repositorio,i,'CONFIRMADO',dni=dni);self.actualizar()

    def cancelar(self,motivo=None):
        i=seleccionado(self.turnos)
        motivo=motivo if motivo is not None else simpledialog.askstring('Cancelar turno','Motivo de cancelación:',parent=self.raiz)
        if motivo is None:return
        turnos.cambiar_estado(self.repositorio,i,'CANCELADO',motivo=motivo);self.actualizar()

    def reprogramar(self,motivo=None):
        i=seleccionado(self.turnos)
        if not hasattr(self,'opciones'):raise ErrorValidacion('Busque y seleccione un hueco nuevo.')
        h=self.opciones[seleccionado(self.huecos)]
        motivo=motivo if motivo is not None else simpledialog.askstring('Reprogramar','Motivo:',parent=self.raiz)
        if motivo is None:return
        nuevo=turnos.reprogramar(self.repositorio,i,h['profesional_id'],h['fecha'],h['hora_inicio'],motivo)
        self.actualizar();self.buscar();return nuevo

    def asistencia(self,estado):
        turnos.cambiar_estado(self.repositorio,seleccionado(self.turnos),estado);self.actualizar()


class RecordatoriosApp(VentanaBase):
    def __init__(self,raiz,repo):
        repo.autorizar('Agenda y recordatorios');super().__init__(raiz,repo,'Agenda y recordatorios')
        ttk.Label(self.cuerpo,text='Cola local de recordatorios para turnos confirmados dentro de las próximas 24 horas. No se envían SMS ni WhatsApp.',wraplength=1000).pack(anchor='w',pady=8)
        ttk.Button(self.cuerpo,text='Preparar recordatorios 24 h',command=lambda:self.intentar(self.generar)).pack(anchor='w')
        self.tabla=tabla(self.cuerpo,[('id','ID',45),('turno_id','Turno',60),('paciente','Paciente',180),('fecha','Fecha',110),('hora_inicio','Hora',75),('destinatario','Teléfono',130),('estado','Estado',100),('resultado','Resultado',280)])
        self.estado=tk.StringVar(raiz);ttk.Label(self.cuerpo,textvariable=self.estado).pack(anchor='w')
        ttk.Button(self.cuerpo,text='Actualizar cola',command=lambda:self.intentar(self.refrescar)).pack(anchor='w')
        self.refrescar()
    def refrescar(self):
        datos=turnos.recordatorios(self.repositorio);poblar(self.tabla,datos,('id','turno_id','paciente','fecha','hora_inicio','destinatario','estado','resultado'));return datos
    def generar(self):
        ids=turnos.generar_recordatorios(self.repositorio);self.refrescar();self.estado.set(f'{len(ids)} recordatorios preparados. Ningún mensaje enviado.');return ids


class HistoriaClinicaApp(VentanaBase):
    def __init__(self,raiz,repo):
        actor=repo.autorizar('Historia clínica');super().__init__(raiz,repo,'Historia clínica electrónica')
        raiz.geometry('1200x820');self.escritor=actor['rol'] in ('admin','medico')
        self.paciente=pacientes(self.cuerpo,repo,True);self.paciente.control.pack(fill='x',pady=4)
        self.paciente.control.bind('<<ComboboxSelected>>',lambda e:self.intentar(self.actualizar))
        ttk.Button(self.cuerpo,text='Consultar HCE / Actualizar',command=lambda:self.intentar(self.actualizar)).pack(anchor='w')
        self.tabs=ttk.Notebook(self.cuerpo);self.tabs.pack(fill='both',expand=True,pady=6)
        cron=ttk.Frame(self.tabs,padding=6);con=ttk.Frame(self.tabs,padding=8);ant=ttk.Frame(self.tabs,padding=8);audit=ttk.Frame(self.tabs,padding=6)
        for pagina,titulo in [(cron,'Cronología'),(con,'Consulta y evolución'),(ant,'Antecedentes'),(audit,'Trazabilidad HCE')]:self.tabs.add(pagina,text=titulo)
        self.eventos=tabla(cron,[('fecha','Fecha UTC',185),('tipo','Tipo',120),('profesional','Profesional',180),('estado','Estado',130),('resumen','Resumen',360)],7)
        self.detalle=ScrolledText(cron,height=9,wrap='word',font=('Consolas',10));self.detalle.pack(fill='both',expand=True)
        self.eventos.bind('<<TreeviewSelect>>',lambda e:self.ver_detalle())
        self.pro=profesionales(con,repo);self.pro.control.pack(fill='x')
        f=ttk.Frame(con);f.pack(fill='x')
        self.cfecha=entrada(f,'Fecha y hora UTC',0,datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M'))
        self.cturno=entrada(f,'Turno asociado (opcional)',0,'',2)
        self.cm= self._texto(con,'Motivo de consulta',2)
        self.ce= self._texto(con,'Evaluación',3)
        self.cv= self._texto(con,'Evolución',3)
        self.boton_consulta=ttk.Button(con,text='Registrar consulta y evolución',state='normal' if self.escritor else 'disabled',command=lambda:self.intentar(self.guardar_consulta));self.boton_consulta.pack(anchor='w',pady=7)
        self.apro=profesionales(ant,repo);self.apro.control.pack(fill='x')
        self.atipo=tk.StringVar(raiz,value='PERSONAL');ttk.Combobox(ant,state='readonly',textvariable=self.atipo,values=['PERSONAL','FAMILIAR']).pack(anchor='w',pady=5)
        self.adescripcion=self._texto(ant,'Descripción',3)
        barra=ttk.Frame(ant);barra.pack(fill='x',pady=5)
        for nombre,accion in [('Registrar antecedente',self.guardar_antecedente),('Modificar seleccionado',lambda:self.guardar_antecedente(True)),('Anular seleccionado',self.anular_antecedente)]:
            ttk.Button(barra,text=nombre,command=lambda a=accion:self.intentar(a),state='normal' if self.escritor else 'disabled').pack(side='left',padx=3)
        self.antecedentes=tabla(ant,[('id','ID',40),('tipo','Tipo',95),('descripcion','Descripción',440),('profesional','Profesional',190),('activo','Activo',60)],5)
        self.antecedentes.bind('<<TreeviewSelect>>',lambda e:self.cargar_antecedente())
        barra=ttk.Frame(audit);barra.pack(fill='x')
        ttk.Label(barra,text='Tipo de operación:').pack(side='left')
        self.aaccion=tk.StringVar(raiz,value='Todas')
        filtro=ttk.Combobox(barra,textvariable=self.aaccion,state='readonly',values=['Todas','A - Alta','M - Modificación','B - Baja','Q - Consulta'],width=24)
        filtro.pack(side='left',padx=8);filtro.bind('<<ComboboxSelected>>',lambda e:self.mostrar_auditoria())
        self.audit=ScrolledText(audit,wrap='word',font=('Consolas',10));self.audit.pack(fill='both',expand=True)
        self.estado=tk.StringVar(raiz);ttk.Label(self.cuerpo,textvariable=self.estado,wraplength=1100).pack(anchor='w')
        self.actualizar()

    def _texto(self,padre,titulo,altura):
        ttk.Label(padre,text=titulo).pack(anchor='w',pady=(5,0))
        control=ScrolledText(padre,height=altura,wrap='word',font=('Segoe UI',10));control.pack(fill='x',pady=3);return control

    def actualizar(self):
        pid=self.paciente.valor(False)
        if not pid:return
        historia=hce.linea_tiempo(self.repositorio,pid);self.historia={i:e for i,e in enumerate(historia['eventos'],1)}
        poblar(self.eventos,[dict(e,id=i,fecha=e['fecha'] or 'No informada / inválida') for i,e in self.historia.items()],('fecha','tipo','profesional','estado','resumen'))
        self.ants={f['id']:f for f in hce.antecedentes(self.repositorio,pid)}
        poblar(self.antecedentes,list(self.ants.values()),('id','tipo','descripcion','profesional','activo'))
        self.auditoria_filas=hce.trazabilidad(self.repositorio,pid)
        self.mostrar_auditoria()
        self.estado.set(f"HC {pid}. {len(self.historia)} eventos, incluidos registros inactivos/anulados. Fechas clínicas UTC; turnos convertidos desde Argentina UTC-03.")
        self.detalle.delete('1.0','end')
        return historia

    def mostrar_auditoria(self):
        codigo=None if self.aaccion.get()=='Todas' else self.aaccion.get()[0]
        filas=[a for a in getattr(self,'auditoria_filas',[]) if codigo is None or a['tipo_accion']==codigo]
        self.audit.delete('1.0','end');self.audit.insert('1.0','\n\n'.join(json.dumps(a,ensure_ascii=False,indent=2) for a in filas))

    def ver_detalle(self):
        if not self.eventos.selection():return
        evento=self.historia[int(self.eventos.selection()[0])]
        self.detalle.delete('1.0','end');self.detalle.insert('1.0',json.dumps(evento['detalle'],ensure_ascii=False,indent=2))

    def guardar_consulta(self):
        i=hce.guardar_consulta(self.repositorio,self.paciente.valor(),self.pro.valor(),self.cm.get('1.0','end'),self.ce.get('1.0','end'),self.cv.get('1.0','end'),self.cfecha.get(),self.cturno.get() or None)
        for control in (self.cm,self.ce,self.cv):control.delete('1.0','end')
        self.actualizar();self.estado.set(f'Consulta {i} registrada y auditada.');return i

    def cargar_antecedente(self):
        if not self.antecedentes.selection():return
        f=self.ants[int(self.antecedentes.selection()[0])];self.apro.seleccionar(f['profesional_id']);self.atipo.set(f['tipo'])
        self.adescripcion.delete('1.0','end');self.adescripcion.insert('1.0',f['descripcion'])

    def guardar_antecedente(self,modificar=False):
        i=hce.guardar_antecedente(self.repositorio,self.paciente.valor(),self.apro.valor(),self.atipo.get(),self.adescripcion.get('1.0','end'),seleccionado(self.antecedentes) if modificar else None)
        self.adescripcion.delete('1.0','end');self.actualizar();return i

    def anular_antecedente(self):
        hce.anular_antecedente(self.repositorio,seleccionado(self.antecedentes));self.actualizar()
