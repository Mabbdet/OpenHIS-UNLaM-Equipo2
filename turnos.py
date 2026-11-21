"""Agenda y turnero telefónico. Horas de atención en Argentina UTC-03 fijo."""

from datetime import datetime, timedelta
from datos import ErrorValidacion, identificador, validar_dni
from servicios_final import (ahora, fecha, hora, texto, operacion, personas,
                             insertar, cambiar, fila, auditar_consulta)

OCUPADOS = ('SOLICITADO', 'CONFIRMADO')


def _futura(valor):
    d = fecha(valor)
    if d < ahora().date(): raise ErrorValidacion('La fecha debe ser actual o futura.')
    return d.isoformat()


def guardar_disponibilidad(repo, datos, registro_id=None):
    with operacion(repo, 'Configurar agenda') as (c, actor):
        pro = identificador(datos.get('profesional_id'), 'un profesional');personas(c, profesional_id=pro)
        try: dia, duracion = int(datos['dia_semana']), int(datos['duracion_minutos'])
        except (ValueError, TypeError, KeyError): raise ErrorValidacion('Indique día y duración válidos.') from None
        if not 0 <= dia <= 6 or not 5 <= duracion <= 240: raise ErrorValidacion('Día 0–6 y duración entre 5 y 240 minutos.')
        inicio, fin = hora(datos.get('hora_inicio')), hora(datos.get('hora_fin'))
        if _minutos(fin)-_minutos(inicio) < duracion: raise ErrorValidacion('La franja debe contener al menos un turno completo.')
        desde = _futura(datos.get('fecha_desde') or ahora().date().isoformat())
        hasta = fecha(datos['fecha_hasta']).isoformat() if datos.get('fecha_hasta') else None
        if hasta and hasta < desde: raise ErrorValidacion('El fin de vigencia precede al inicio.')
        if registro_id and not fila(c,'DisponibilidadProfesional',registro_id)['activo']:
            raise ErrorValidacion('La franja está inactiva; registre una nueva disponibilidad.')
        if c.execute('''SELECT 1 FROM DisponibilidadProfesional WHERE activo=1 AND profesional_id=? AND dia_semana=?
             AND hora_inicio<? AND hora_fin>? AND fecha_desde<=? AND COALESCE(fecha_hasta,'9999-12-31')>=? AND id<>?''',
             (pro,dia,fin,inicio,hasta or '9999-12-31',desde,registro_id or 0)).fetchone():
            raise ErrorValidacion('La disponibilidad se superpone con otra franja vigente.')
        valores=dict(profesional_id=pro,dia_semana=dia,hora_inicio=inicio,hora_fin=fin,duracion_minutos=duracion,fecha_desde=desde,fecha_hasta=hasta)
        if registro_id:
            cambiar(c,actor,'DisponibilidadProfesional',registro_id,valores);return registro_id
        return insertar(c,actor,'DisponibilidadProfesional',valores)


def desactivar_disponibilidad(repo, registro_id):
    with operacion(repo,'Configurar agenda') as (c,actor):
        if not fila(c,'DisponibilidadProfesional',registro_id)['activo']: raise ErrorValidacion('La franja ya está inactiva.')
        cambiar(c,actor,'DisponibilidadProfesional',registro_id,{'activo':0},'B')


def guardar_bloqueo(repo, datos):
    with operacion(repo,'Configurar agenda') as (c,actor):
        pro=identificador(datos.get('profesional_id'),'un profesional');personas(c,profesional_id=pro)
        dia=_futura(datos.get('fecha'));inicio=hora(datos['hora_inicio']) if datos.get('hora_inicio') else None
        fin=hora(datos['hora_fin']) if datos.get('hora_fin') else None
        if bool(inicio)!=bool(fin) or (inicio and inicio>=fin): raise ErrorValidacion('Complete ambas horas en orden o deje ambas vacías para bloquear el día.')
        tipo=datos.get('tipo','BLOQUEO')
        if tipo not in ('BLOQUEO','VACACIONES','LICENCIA','OTRO'): raise ErrorValidacion('Tipo de bloqueo no válido.')
        if c.execute("SELECT 1 FROM Turnos WHERE profesional_id=? AND fecha=? AND estado IN ('SOLICITADO','CONFIRMADO') AND hora_inicio<? AND hora_fin>?",
                     (pro,dia,fin or '24:00',inicio or '00:00')).fetchone():
            raise ErrorValidacion('Hay turnos registrados en ese intervalo. Reprográmelos antes de bloquear.')
        return insertar(c,actor,'BloqueosAgenda',dict(profesional_id=pro,fecha=dia,hora_inicio=inicio,hora_fin=fin,tipo=tipo,motivo=texto(datos.get('motivo'),'el motivo')))


def desactivar_bloqueo(repo, registro_id):
    with operacion(repo,'Configurar agenda') as (c,actor):
        if not fila(c,'BloqueosAgenda',registro_id)['activo']: raise ErrorValidacion('El bloqueo ya está inactivo.')
        cambiar(c,actor,'BloqueosAgenda',registro_id,{'activo':0},'B')


def configuracion(repo, profesional_id=None):
    with operacion(repo,'Agenda profesional') as (c,actor):
        condicion=' WHERE profesional_id=?' if profesional_id else ''
        args=(identificador(profesional_id,'un profesional'),) if profesional_id else ()
        resultado={t:[dict(r) for r in c.execute(f'SELECT * FROM {t}'+condicion+' ORDER BY id DESC',args)] for t in ('DisponibilidadProfesional','BloqueosAgenda')}
        auditar_consulta(c,actor,'DisponibilidadProfesional',datos={'profesional_id':profesional_id})
        return resultado


def _minutos(h):
    hh,mm=map(int,h.split(':'));return hh*60+mm


def _hora(minutos):
    return f'{minutos//60:02}:{minutos%60:02}'


def _huecos(c, dia, profesional_id=None, especialidad_id=None, paciente_id=None):
    filtros=['d.activo=1','p.activo=1','e.activo=1','d.dia_semana=?','d.fecha_desde<=?','(d.fecha_hasta IS NULL OR d.fecha_hasta>=?)']
    args=[fecha(dia).weekday(),dia,dia]
    for campo,valor in [('p.id',profesional_id),('e.id',especialidad_id)]:
        if valor: filtros.append(campo+'=?');args.append(identificador(valor,'un filtro'))
    franjas=c.execute('''SELECT d.*,p.nombre||' '||p.apellido AS profesional,e.nombre AS especialidad
        FROM DisponibilidadProfesional d JOIN Profesionales p ON p.id=d.profesional_id
        JOIN Especialidades e ON e.id=p.especialidad_id WHERE '''+' AND '.join(filtros),args).fetchall()
    turnos=c.execute("SELECT * FROM Turnos WHERE fecha=? AND estado IN ('SOLICITADO','CONFIRMADO')",(dia,)).fetchall()
    bloqueos=c.execute('SELECT * FROM BloqueosAgenda WHERE fecha=? AND activo=1',(dia,)).fetchall()
    resultado=[];momento=ahora()
    for f in franjas:
        for minuto in range(_minutos(f['hora_inicio']),_minutos(f['hora_fin'])-f['duracion_minutos']+1,f['duracion_minutos']):
            inicio,fin=_hora(minuto),_hora(minuto+f['duracion_minutos'])
            if datetime.fromisoformat(dia+'T'+inicio)<=momento: continue
            if any(t['hora_inicio']<fin and t['hora_fin']>inicio and (t['profesional_id']==f['profesional_id'] or (paciente_id and t['paciente_id']==paciente_id)) for t in turnos):continue
            if any(b['profesional_id']==f['profesional_id'] and (b['hora_inicio'] is None or (b['hora_inicio']<fin and b['hora_fin']>inicio)) for b in bloqueos):continue
            resultado.append(dict(profesional_id=f['profesional_id'],profesional=f['profesional'],especialidad=f['especialidad'],fecha=dia,hora_inicio=inicio,hora_fin=fin,
                ocupacion=sum(t['profesional_id']==f['profesional_id'] for t in turnos)))
    return sorted(resultado,key=lambda f:(f['hora_inicio'],f['ocupacion'],f['profesional_id']))


def disponibles(repo, dia, profesional_id=None, especialidad_id=None, paciente_id=None):
    with operacion(repo,'Turnos') as (c,actor):
        dia=fecha(dia).isoformat()
        if paciente_id:personas(c,paciente_id=paciente_id)
        resultado=_huecos(c,dia,profesional_id,especialidad_id,paciente_id)
        auditar_consulta(c,actor,'Turnos',datos={'disponibles':dia,'profesional_id':profesional_id,'especialidad_id':especialidad_id})
        return resultado


def agenda_diaria(repo, dia, profesional_id=None):
    with operacion(repo,'Agenda profesional') as (c,actor):
        dia=fecha(dia).isoformat();args=[dia]
        filtro=''
        if profesional_id:filtro=' AND t.profesional_id=?';args.append(identificador(profesional_id,'un profesional'))
        filas=c.execute('''SELECT t.*,p.nombre||' '||p.apellido AS paciente,p.dni,
            r.nombre||' '||r.apellido AS profesional FROM Turnos t
            JOIN Pacientes p ON p.id=t.paciente_id JOIN Profesionales r ON r.id=t.profesional_id
            WHERE t.fecha=?'''+filtro+' ORDER BY t.hora_inicio,t.id',args).fetchall()
        auditar_consulta(c,actor,'Turnos',datos={'agenda_diaria':dia})
        return [dict(f) for f in filas]


def _identidad(c,paciente_id,dni):
    paciente=c.execute('SELECT dni FROM Pacientes WHERE id=?',(paciente_id,)).fetchone()
    if paciente is None or validar_dni(dni)!=paciente['dni']:raise ErrorValidacion('El DNI verificado no corresponde al paciente del turno.')


def _crear(c,actor,paciente_id,profesional_id,dia,inicio,motivo,observaciones='',confirmado=False,dni='',turno_origen_id=None,canal='TELEFONO'):
    if canal not in ('TELEFONO','WEB'):raise ErrorValidacion('Canal de solicitud inválido.')
    paciente_id=identificador(paciente_id,'un paciente');profesional_id=identificador(profesional_id,'un profesional')
    personas(c,paciente_id,profesional_id);dia=_futura(dia);inicio=hora(inicio)
    hueco=next((h for h in _huecos(c,dia,profesional_id,paciente_id=paciente_id) if h['hora_inicio']==inicio),None)
    if not hueco:raise ErrorValidacion('El horario dejó de estar disponible. Actualice los huecos.')
    if confirmado:_identidad(c,paciente_id,dni)
    valores=dict(paciente_id=paciente_id,profesional_id=profesional_id,fecha=dia,hora_inicio=inicio,hora_fin=hueco['hora_fin'],
        motivo_consulta=texto(motivo,'el motivo de consulta',2000),observaciones=str(observaciones or '').strip(),turno_origen_id=turno_origen_id,
        estado='CONFIRMADO' if confirmado else 'SOLICITADO',canal_solicitud=canal)
    if confirmado:valores.update(canal_confirmacion=canal,fecha_confirmacion=ahora().isoformat())
    return insertar(c,actor,'Turnos',valores)


def reservar(repo,paciente_id,profesional_id,dia,inicio,motivo,observaciones='',confirmado=False,dni=''):
    with operacion(repo,'Turnos') as (c,actor):
        return _crear(c,actor,paciente_id,profesional_id,dia,inicio,motivo,observaciones,confirmado,dni)


def reservar_sugerido(repo,paciente_id,especialidad_id,dia,motivo):
    with operacion(repo,'Turnos') as (c,actor):
        paciente_id=identificador(paciente_id,'un paciente');especialidad_id=identificador(especialidad_id,'una especialidad')
        personas(c,paciente_id=paciente_id);dia=_futura(dia)
        huecos=_huecos(c,dia,especialidad_id=especialidad_id,paciente_id=paciente_id)
        if not huecos:raise ErrorValidacion('No hay huecos para esa especialidad y fecha.')
        elegido=huecos[0]
        i=_crear(c,actor,paciente_id,elegido['profesional_id'],dia,elegido['hora_inicio'],motivo)
        return {**elegido,'turno_id':i}


def _cancelar_recordatorios(c,actor,turno_id,motivo):
    for r in c.execute("SELECT id FROM ColaNotificaciones WHERE turno_id=? AND estado IN ('PENDIENTE','ERROR')",(turno_id,)).fetchall():
        cambiar(c,actor,'ColaNotificaciones',r['id'],{'estado':'CANCELADA','resultado':motivo})


def cambiar_estado(repo,turno_id,estado,dni='',motivo=''):
    with operacion(repo,'Turnos') as (c,actor):
        anterior=fila(c,'Turnos',turno_id)
        transiciones={'SOLICITADO':{'CONFIRMADO','CANCELADO'},'CONFIRMADO':{'CANCELADO','ATENDIDO','AUSENTE'}}
        if estado not in transiciones.get(anterior['estado'],set()):raise ErrorValidacion('La transición de estado no está permitida.')
        datos={'estado':estado,'fecha_actualizacion':ahora().isoformat()}
        if estado=='CONFIRMADO':
            personas(c,anterior['paciente_id'],anterior['profesional_id']);_identidad(c,anterior['paciente_id'],dni)
            if datetime.fromisoformat(anterior['fecha']+'T'+anterior['hora_inicio'])<=ahora():raise ErrorValidacion('No se confirma un turno ya iniciado.')
            datos.update(canal_confirmacion='TELEFONO',fecha_confirmacion=ahora().isoformat())
        elif estado in ('ATENDIDO','AUSENTE'):
            if datetime.fromisoformat(anterior['fecha']+'T'+anterior['hora_inicio'])>ahora():raise ErrorValidacion('La asistencia se registra desde el inicio del turno.')
        else:
            datos['observaciones']=(anterior['observaciones'] or '')+'\nCancelación: '+texto(motivo,'el motivo de cancelación',2000)
        cambiar(c,actor,'Turnos',turno_id,datos)
        if estado!='CONFIRMADO':_cancelar_recordatorios(c,actor,turno_id,'Turno '+estado.lower())


def reprogramar(repo,turno_id,profesional_id,dia,inicio,motivo):
    with operacion(repo,'Turnos') as (c,actor):
        anterior=fila(c,'Turnos',turno_id)
        if anterior['estado'] not in OCUPADOS:raise ErrorValidacion('Solo se reprograman turnos solicitados o confirmados.')
        if (anterior['profesional_id'],anterior['fecha'],anterior['hora_inicio'])==(profesional_id,str(dia),str(inicio)):
            raise ErrorValidacion('Seleccione un horario o profesional diferente para reprogramar.')
        razon=texto(motivo,'el motivo de reprogramación',2000)
        cambiar(c,actor,'Turnos',turno_id,{'estado':'REPROGRAMADO','fecha_actualizacion':ahora().isoformat(),
            'observaciones':(anterior['observaciones'] or '')+'\nReprogramación: '+razon})
        nuevo=_crear(c,actor,anterior['paciente_id'],profesional_id,dia,inicio,anterior['motivo_consulta'],razon,turno_origen_id=turno_id)
        _cancelar_recordatorios(c,actor,turno_id,'Turno reprogramado')
        return nuevo


def generar_recordatorios(repo):
    with operacion(repo,'Agenda y recordatorios') as (c,actor):
        momento=ahora();ids=[]
        for t in c.execute('''SELECT t.*,p.telefono,p.nombre,p.apellido FROM Turnos t JOIN Pacientes p ON p.id=t.paciente_id
                WHERE t.estado='CONFIRMADO' ORDER BY t.fecha,t.hora_inicio''').fetchall():
            inicio=datetime.fromisoformat(t['fecha']+'T'+t['hora_inicio'])
            if not momento<inicio<=momento+timedelta(hours=24):continue
            telefono=str(t['telefono'] or '').strip()
            datos=dict(turno_id=t['id'],destinatario=telefono or None,
                mensaje=f"Recordatorio de turno: {t['fecha']} a las {t['hora_inicio']}.",programada_para=(inicio-timedelta(hours=24)).isoformat(),
                estado='PENDIENTE' if telefono else 'ERROR',resultado='Cola local; no se envió ningún mensaje.' if telefono else 'Sin teléfono de contacto; no se realizó envío.')
            previo=c.execute('SELECT * FROM ColaNotificaciones WHERE turno_id=?',(t['id'],)).fetchone()
            if previo:
                if previo['estado'] in ('PENDIENTE','ERROR') and any(previo[k]!=v for k,v in datos.items()):
                    cambiar(c,actor,'ColaNotificaciones',previo['id'],datos);ids.append(previo['id'])
                continue
            ids.append(insertar(c,actor,'ColaNotificaciones',datos))
        return ids


def recordatorios(repo):
    with operacion(repo,'Agenda y recordatorios') as (c,actor):
        resultado=[dict(r) for r in c.execute('''SELECT n.*,t.fecha,t.hora_inicio,p.nombre||' '||p.apellido AS paciente
            FROM ColaNotificaciones n JOIN Turnos t ON t.id=n.turno_id JOIN Pacientes p ON p.id=t.paciente_id ORDER BY t.fecha,t.hora_inicio,n.id''')]
        auditar_consulta(c,actor,'ColaNotificaciones')
        return resultado
