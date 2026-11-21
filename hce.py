"""Historia clínica: consultas, antecedentes, cronología y auditoría por paciente."""

from datetime import datetime, timezone

from datos import ErrorValidacion, identificador
from servicios_final import (operacion, insertar, cambiar, fila, personas, texto,
                             auditar_consulta, ahora, ZONA_TURNOS)


def _paciente(c,paciente_id):
    p=c.execute('SELECT * FROM Pacientes WHERE id=?',(identificador(paciente_id,'un paciente'),)).fetchone()
    if p is None:raise ErrorValidacion('El paciente no existe.')
    return dict(p)


def _instante(valor):
    try:
        dt=datetime.fromisoformat(str(valor).replace('Z','+00:00'))
        if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError,TypeError):raise ErrorValidacion('Fecha y hora clínica inválidas; use AAAA-MM-DD HH:MM (UTC).') from None


def guardar_consulta(repo,paciente_id,profesional_id,motivo,evaluacion,evolucion,fecha_hora=None,turno_id=None):
    with operacion(repo,'Registrar HCE') as (c,actor):
        paciente_id=identificador(paciente_id,'un paciente');profesional_id=identificador(profesional_id,'un profesional')
        personas(c,paciente_id,profesional_id)
        momento=_instante(fecha_hora) if fecha_hora else ahora().replace(tzinfo=ZONA_TURNOS).astimezone(timezone.utc)
        if momento>ahora().replace(tzinfo=ZONA_TURNOS).astimezone(timezone.utc):raise ErrorValidacion('La consulta no puede tener fecha futura.')
        if turno_id:
            turno_id=identificador(turno_id,'un turno');turno=fila(c,'Turnos',turno_id)
            if (turno['paciente_id'],turno['profesional_id'])!=(paciente_id,profesional_id):raise ErrorValidacion('El turno no corresponde al paciente y profesional elegidos.')
            if turno['estado'] not in ('CONFIRMADO','ATENDIDO'):raise ErrorValidacion('Vincule un turno confirmado o atendido.')
            if datetime.fromisoformat(turno['fecha']+'T'+turno['hora_inicio'])>ahora():raise ErrorValidacion('El turno todavía no comenzó.')
        return insertar(c,actor,'ConsultasClinicas',dict(paciente_id=paciente_id,profesional_id=profesional_id,turno_id=turno_id or None,
            fecha_hora=momento.isoformat().replace('+00:00','Z'),motivo_consulta=texto(motivo,'el motivo'),
            evaluacion=texto(evaluacion,'la evaluación'),evolucion=texto(evolucion,'la evolución')))


def guardar_antecedente(repo,paciente_id,profesional_id,tipo,descripcion,registro_id=None):
    with operacion(repo,'Registrar HCE') as (c,actor):
        paciente_id=identificador(paciente_id,'un paciente');profesional_id=identificador(profesional_id,'un profesional')
        personas(c,paciente_id,profesional_id)
        if tipo not in ('PERSONAL','FAMILIAR'):raise ErrorValidacion('Seleccione antecedente personal o familiar.')
        valores=dict(paciente_id=paciente_id,profesional_id=profesional_id,tipo=tipo,descripcion=texto(descripcion,'la descripción'))
        if registro_id:
            anterior=fila(c,'AntecedentesClinicos',registro_id)
            if anterior['paciente_id']!=paciente_id:raise ErrorValidacion('El antecedente pertenece a otro paciente.')
            if not anterior['activo']:raise ErrorValidacion('El antecedente está inactivo; conserve su historial y registre uno nuevo.')
            valores['fecha_actualizacion']=datetime.now(timezone.utc).isoformat()
            cambiar(c,actor,'AntecedentesClinicos',registro_id,valores);return registro_id
        return insertar(c,actor,'AntecedentesClinicos',valores)


def anular_antecedente(repo,registro_id):
    with operacion(repo,'Registrar HCE') as (c,actor):
        if not fila(c,'AntecedentesClinicos',registro_id)['activo']:raise ErrorValidacion('El antecedente ya está inactivo.')
        cambiar(c,actor,'AntecedentesClinicos',registro_id,{'activo':0,'fecha_actualizacion':datetime.now(timezone.utc).isoformat()},'B')


def antecedentes(repo,paciente_id):
    with operacion(repo,'Historia clínica') as (c,actor):
        _paciente(c,paciente_id)
        resultado=[dict(f) for f in c.execute('''SELECT a.*,p.nombre||' '||p.apellido AS profesional FROM AntecedentesClinicos a
            LEFT JOIN Profesionales p ON p.id=a.profesional_id WHERE a.paciente_id=? ORDER BY a.fecha_registro DESC,a.id DESC''',(paciente_id,))]
        auditar_consulta(c,actor,'Pacientes',paciente_id,{'antecedentes_clinicos':True})
        return resultado


def linea_tiempo(repo,paciente_id):
    with operacion(repo,'Historia clínica') as (c,actor):
        paciente=_paciente(c,paciente_id);eventos=[]
        fuentes=[('ConsultasClinicas','fecha_hora','profesional_id','Consulta médica','motivo_consulta'),
                 ('SignosVitales','fecha_hora','medico_id','Signos vitales','motivo_consulta'),
                 ('Prescripciones','fecha_prescripcion','profesional_id','Prescripción','dosis'),
                 ('Practicas','fecha_solicitud','profesional_id','Práctica','descripcion'),
                 ('AntecedentesClinicos','fecha_registro','profesional_id','Antecedente','descripcion')]
        for tabla,fecha_campo,prof_campo,tipo,resumen_campo in fuentes:
            for f in c.execute(f'''SELECT r.*,p.nombre||' '||p.apellido AS profesional FROM {tabla} r
                LEFT JOIN Profesionales p ON p.id=r.{prof_campo} WHERE r.paciente_id=?''',(paciente_id,)):
                detalle=dict(f)
                if tabla=='Prescripciones':
                    medicamento=c.execute('SELECT nombre FROM Farmacos WHERE id=?',(f['farmaco_id'],)).fetchone()
                    detalle['farmaco']=medicamento[0] if medicamento else 'No informado'
                try: fecha_evento=_instante(f[fecha_campo]).isoformat().replace('+00:00','Z')
                except ErrorValidacion: fecha_evento=None
                eventos.append(dict(tabla=tabla,id=f['id'],fecha=fecha_evento,
                    tipo=tipo,resumen=str(detalle.get('farmaco') or f[resumen_campo] or tipo),
                    profesional=f['profesional'] or 'No informado en el origen',estado='Activo' if detalle.get('activo',1) else 'Inactivo / anulado',detalle=detalle))
        for f in c.execute('''SELECT t.*,p.nombre||' '||p.apellido AS profesional FROM Turnos t
            LEFT JOIN Profesionales p ON p.id=t.profesional_id WHERE t.paciente_id=?''',(paciente_id,)):
            momento=datetime.fromisoformat(f['fecha']+'T'+f['hora_inicio']).replace(tzinfo=ZONA_TURNOS).astimezone(timezone.utc)
            eventos.append(dict(tabla='Turnos',id=f['id'],fecha=momento.isoformat().replace('+00:00','Z'),tipo='Turno',
                resumen=f['motivo_consulta'],profesional=f['profesional'] or 'No informado',estado=f['estado'],detalle=dict(f)))
        eventos.sort(key=lambda e:(_instante(e['fecha']) if e['fecha'] else datetime.min.replace(tzinfo=timezone.utc),e['tabla'],e['id']),reverse=True)
        auditar_consulta(c,actor,'Pacientes',paciente_id,{'historia_clinica':True,'eventos':len(eventos)})
        return {'paciente':paciente,'eventos':eventos}


def trazabilidad(repo,paciente_id):
    with operacion(repo,'Historia clínica') as (c,actor):
        _paciente(c,paciente_id)
        auditar_consulta(c,actor,'Pacientes',paciente_id,{'trazabilidad_hce':True})
        tablas=('ConsultasClinicas','AntecedentesClinicos','SignosVitales','Prescripciones','Practicas','Turnos')
        condiciones=["(a.tabla_afectada='Pacientes' AND a.registro_id=?)"]
        for t in tablas:
            condiciones.append(f"(a.tabla_afectada='{t}' AND EXISTS(SELECT 1 FROM {t} r WHERE r.id=a.registro_id AND r.paciente_id=?))")
        return [dict(r) for r in c.execute('SELECT a.* FROM Auditoria a WHERE '+' OR '.join(condiciones)+' ORDER BY a.id DESC',(paciente_id,)*(len(tablas)+1))]
