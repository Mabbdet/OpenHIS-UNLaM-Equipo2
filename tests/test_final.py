from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import sqlite3

import pytest

from datos import ErrorValidacion, Repositorio
from seguridad import AccesoDenegado
from tests.test_entrega9 import entorno
import hce
import turnos
import servicios_final
from final_app import AgendaProfesionalApp, GestionTurnosApp, RecordatoriosApp, HistoriaClinicaApp


@pytest.fixture
def final(entorno,monkeypatch):
    s,sesion,r=entorno
    reloj=lambda:datetime(2030,1,7,7,0)
    monkeypatch.setattr(turnos,'ahora',reloj);monkeypatch.setattr(hce,'ahora',reloj)
    p=r.listar_pacientes()[0];pro=r.listar_profesionales()[0]
    datos=dict(profesional_id=pro['id'],dia_semana=1,hora_inicio='08:00',hora_fin='11:00',duracion_minutos=30,fecha_desde='2030-01-07')
    i=turnos.guardar_disponibilidad(r,datos)
    return s,sesion,r,p,pro,datos,i


def reservar(f,hora='08:00',confirmado=False):
    s,ses,r,p,pro,*_=f
    return turnos.reservar(r,p['id'],pro['id'],'2030-01-08',hora,'Control ficticio',confirmado=confirmado,dni=p['dni'])


def leer(s,tabla):
    with s._repo.conectar() as c:return [dict(f) for f in c.execute('SELECT * FROM '+tabla+' ORDER BY id')]


def test_disponibilidad_bloqueos_y_periodos(final):
    s,ses,r,p,pro,d,i=final
    assert len(turnos.disponibles(r,'2030-01-08',pro['id']))==6
    with pytest.raises(ErrorValidacion,match='superpone'):turnos.guardar_disponibilidad(r,{**d,'hora_inicio':'08:15'})
    turno=reservar(final)
    antes=leer(s,'Turnos')
    turnos.guardar_disponibilidad(r,{**d,'hora_inicio':'09:00','duracion_minutos':45},i)
    assert leer(s,'Turnos')==antes
    assert [f['hora_inicio'] for f in turnos.disponibles(r,'2030-01-08',pro['id'])]==['09:00','09:45']
    b=turnos.guardar_bloqueo(r,dict(profesional_id=pro['id'],fecha='2030-01-08',hora_inicio='09:10',hora_fin='09:25',motivo='Prueba'))
    assert [f['hora_inicio'] for f in turnos.disponibles(r,'2030-01-08',pro['id'])]==['09:45']
    with pytest.raises(ErrorValidacion,match='turnos registrados'):
        turnos.guardar_bloqueo(r,dict(profesional_id=pro['id'],fecha='2030-01-08',motivo='Día completo'))
    turnos.desactivar_bloqueo(r,b)
    turnos.desactivar_disponibilidad(r,i)
    assert turnos.disponibles(r,'2030-01-08',pro['id'])==[]
    turnos.cambiar_estado(r,turno,'CONFIRMADO',dni=p['dni'])
    assert turnos.agenda_diaria(r,'2030-01-08')[0]['estado']=='CONFIRMADO'


@pytest.mark.parametrize('campo,valor', [('dia_semana',7),('duracion_minutos',0),('duracion_minutos',241),('hora_inicio','8:00'),('hora_fin','24:00'),('fecha_desde','2029-01-01'),('fecha_hasta','2029-12-01')])
def test_configuracion_invalida(final,campo,valor):
    s,ses,r,p,pro,d,i=final
    antes=leer(s,'DisponibilidadProfesional')
    with pytest.raises(ErrorValidacion):turnos.guardar_disponibilidad(r,{**d,campo:valor})
    assert leer(s,'DisponibilidadProfesional')==antes


def test_dni_y_fichas_activas_se_revalidan(final):
    s,ses,r,p,pro,*_=final
    with pytest.raises(ErrorValidacion,match='DNI'):turnos.reservar(r,p['id'],pro['id'],'2030-01-08','08:00','Control',confirmado=True,dni='00000000')
    i=reservar(final)
    r.dar_baja_paciente(p['id'])
    with pytest.raises(ErrorValidacion,match='activa'):turnos.cambiar_estado(r,i,'CONFIRMADO',dni=p['dni'])
    r.reactivar_paciente(p['id']);r.dar_baja_profesional(pro['id'])
    assert turnos.disponibles(r,'2030-01-08',pro['id'])==[]
    assert len(turnos.agenda_diaria(r,'2030-01-08'))==1


def test_reservas_concurrentes_y_proteccion_sql(final):
    s,ses,r,p,pro,*_=final
    def intentar(_):
        try:return reservar(final)
        except ErrorValidacion:return None
    with ThreadPoolExecutor(max_workers=2) as pool:resultados=list(pool.map(intentar,range(2)))
    assert sum(i is not None for i in resultados)==1
    with s._repo.conectar() as c:
        with pytest.raises(sqlite3.IntegrityError,match='superpuesto'):
            c.execute('''INSERT INTO Turnos(paciente_id,profesional_id,fecha,hora_inicio,hora_fin,motivo_consulta,usuario_alta_id)
                VALUES(?,?,'2030-01-08','08:15','08:45','Prueba',?)''',(p['id'],pro['id'],s.autorizar(ses)['id']))
    assert len(leer(s,'Turnos'))==1


def test_paciente_no_puede_reservar_simultaneamente_con_otro_profesional(final):
    s,ses,r,p,pro,d,i=final
    otro=r.registrar_profesional(dict(dni='99111991',nombre='Otro',apellido='Profesional',fecha_nacimiento='1980-01-01',sexo='M',matricula='OTRO-1',especialidad_id=pro['especialidad_id']))
    turnos.guardar_disponibilidad(r,{**d,'profesional_id':otro})
    reservar(final)
    with pytest.raises(ErrorValidacion,match='disponible'):turnos.reservar(r,p['id'],otro,'2030-01-08','08:00','Control')
    assert all(f['hora_inicio']!='08:00' for f in turnos.disponibles(r,'2030-01-08',otro,paciente_id=p['id']))


def test_reprogramacion_atomica_y_cancelacion_auditadas(final):
    s,ses,r,p,pro,*_=final
    i=reservar(final,confirmado=True)
    antes=leer(s,'Turnos')
    with pytest.raises(ErrorValidacion,match='diferente'):turnos.reprogramar(r,i,pro['id'],'2030-01-08','08:00','Sin cambio')
    with pytest.raises(ErrorValidacion):turnos.reprogramar(r,i,pro['id'],'2030-01-08','23:00','Prueba')
    assert leer(s,'Turnos')==antes
    nuevo=turnos.reprogramar(r,i,pro['id'],'2030-01-08','09:00','Cambio solicitado')
    registros={f['id']:f for f in leer(s,'Turnos')}
    assert registros[i]['estado']=='REPROGRAMADO'
    assert registros[nuevo]['turno_origen_id']==i and registros[nuevo]['estado']=='SOLICITADO'
    turnos.cambiar_estado(r,nuevo,'CANCELADO',motivo='Solicitud ficticia')
    assert '09:00' in [f['hora_inicio'] for f in turnos.disponibles(r,'2030-01-08',pro['id'])]
    with pytest.raises(ErrorValidacion,match='transición'):turnos.cambiar_estado(r,nuevo,'CONFIRMADO',dni=p['dni'])
    logs=[f for f in leer(s,'Auditoria') if f['tabla_afectada']=='Turnos' and f['tipo_accion']=='M']
    assert any(json.loads(f['datos_nuevos'])['estado']=='REPROGRAMADO' for f in logs)


@pytest.mark.parametrize('estado',['ATENDIDO','AUSENTE'])
def test_asistencia_no_se_registra_antes_del_turno(final,monkeypatch,estado):
    s,ses,r,p,pro,*_=final;i=reservar(final,confirmado=True)
    with pytest.raises(ErrorValidacion,match='inicio'):turnos.cambiar_estado(r,i,estado)
    monkeypatch.setattr(turnos,'ahora',lambda:datetime(2030,1,8,8,0))
    turnos.cambiar_estado(r,i,estado)
    assert leer(s,'Turnos')[0]['estado']==estado
    with pytest.raises(ErrorValidacion):turnos.cambiar_estado(r,i,'CANCELADO',motivo='No permitido')


def test_sugerencia_elige_horario_y_profesional_sin_conflictos(final):
    s,ses,r,p,pro,d,i=final
    otro=r.registrar_profesional(dict(dni='99111991',nombre='Otro',apellido='Profesional',fecha_nacimiento='1980-01-01',sexo='M',matricula='OTRO-1',especialidad_id=pro['especialidad_id']))
    turnos.guardar_disponibilidad(r,{**d,'profesional_id':otro})
    reservar(final)
    otro_paciente=next(f for f in r.listar_pacientes() if f['id']!=p['id'])
    resultado=turnos.reservar_sugerido(r,otro_paciente['id'],pro['especialidad_id'],'2030-01-08','Control')
    assert resultado['profesional_id']==otro and resultado['hora_inicio']=='08:00'
    assert next(f for f in leer(s,'Turnos') if f['id']==resultado['turno_id'])['estado']=='SOLICITADO'


def test_recordatorios_24h_no_duplican_y_se_cancelan(final,monkeypatch):
    s,ses,r,p,pro,*_=final;i=reservar(final,confirmado=True)
    assert turnos.generar_recordatorios(r)==[]
    monkeypatch.setattr(turnos,'ahora',lambda:datetime(2030,1,7,8,0))
    with s._repo.conectar() as c:c.execute('UPDATE Pacientes SET telefono=NULL WHERE id=?',(p['id'],))
    ids=turnos.generar_recordatorios(r)
    assert len(ids)==1 and turnos.recordatorios(r)[0]['estado']=='ERROR'
    with s._repo.conectar() as c:c.execute('UPDATE Pacientes SET telefono=? WHERE id=?',('555-0000',p['id']))
    assert turnos.generar_recordatorios(r)==ids
    assert turnos.generar_recordatorios(r)==[]
    assert turnos.recordatorios(r)[0]['estado']=='PENDIENTE'
    turnos.cambiar_estado(r,i,'CANCELADO',motivo='Solicitud')
    assert turnos.recordatorios(r)[0]['estado']=='CANCELADA'
    assert len(leer(s,'ColaNotificaciones'))==1


def test_consultas_antecedentes_cronologia_y_auditoria(final):
    s,ses,r,p,pro,*_=final
    consulta=hce.guardar_consulta(r,p['id'],pro['id'],'Motivo ficticio','Evaluación ficticia','Evolución ficticia','2030-01-07 09:00')
    ant=hce.guardar_antecedente(r,p['id'],pro['id'],'PERSONAL','Descripción inicial')
    hce.guardar_antecedente(r,p['id'],pro['id'],'FAMILIAR','Ejemplo familiar')
    hce.guardar_antecedente(r,p['id'],pro['id'],'PERSONAL','Descripción corregida',ant)
    hce.anular_antecedente(r,ant)
    r.dar_baja_paciente(p['id'])
    historia=hce.linea_tiempo(r,p['id']);eventos=historia['eventos']
    assert any(e['tabla']=='ConsultasClinicas' and e['id']==consulta for e in eventos)
    assert any(e['tabla']=='AntecedentesClinicos' and e['id']==ant and e['estado']=='Inactivo / anulado' for e in eventos)
    assert [e['fecha'] for e in eventos]==sorted([e['fecha'] for e in eventos],reverse=True)
    trazas=hce.trazabilidad(r,p['id'])
    modificaciones=[a for a in trazas if a['tabla_afectada']=='AntecedentesClinicos' and a['registro_id']==ant]
    assert {a['tipo_accion'] for a in modificaciones}>={'A','M','B'}
    mod=next(a for a in modificaciones if a['tipo_accion']=='M')
    assert json.loads(mod['datos_anteriores'])['descripcion']=='Descripción inicial'
    assert json.loads(mod['datos_nuevos'])['descripcion']=='Descripción corregida'
    with pytest.raises(ErrorValidacion,match='activa'):hce.guardar_consulta(r,p['id'],pro['id'],'M','E','V')


def test_hce_conserva_autor_y_fecha_desconocidos_y_registros_anulados(final):
    s,ses,r,p,pro,*_=final
    with s._repo.conectar() as c:
        i=c.execute("INSERT INTO SignosVitales(paciente_id,fecha_hora,medico_id,origen_fhir,motivo_consulta,activo,temperatura) VALUES (?,NULL,NULL,'Origen de prueba','Histórico',0,0)",(p['id'],)).lastrowid
    evento=next(e for e in hce.linea_tiempo(r,p['id'])['eventos'] if e['tabla']=='SignosVitales' and e['id']==i)
    assert evento['fecha'] is None and evento['profesional']=='No informado en el origen'
    assert evento['detalle']['temperatura']==0 and evento['estado']=='Inactivo / anulado'


def test_consulta_vinculada_valida_paciente_profesional_y_turno(final,monkeypatch):
    s,ses,r,p,pro,*_=final;i=reservar(final,confirmado=True)
    with pytest.raises(ErrorValidacion,match='comenzó'):hce.guardar_consulta(r,p['id'],pro['id'],'M','E','V',turno_id=i)
    monkeypatch.setattr(hce,'ahora',lambda:datetime(2030,1,8,9,0))
    otro=next(f for f in r.listar_pacientes() if f['id']!=p['id'])
    with pytest.raises(ErrorValidacion,match='corresponde'):hce.guardar_consulta(r,otro['id'],pro['id'],'M','E','V',turno_id=i)
    cid=hce.guardar_consulta(r,p['id'],pro['id'],'M','E','V',turno_id=i)
    assert leer(s,'ConsultasClinicas')[0]['turno_id']==i
    trazas=hce.trazabilidad(r,otro['id'])
    assert not any(a['tabla_afectada']=='ConsultasClinicas' and a['registro_id']==cid for a in trazas)


@pytest.mark.parametrize('campo',['motivo','evaluacion','evolucion','fecha_futura'])
def test_consulta_rechaza_campos_vacios_o_futuros(final,campo):
    s,ses,r,p,pro,*_=final
    datos=dict(motivo='M',evaluacion='E',evolucion='V',fecha_hora='2030-01-07 09:00')
    if campo=='fecha_futura':datos['fecha_hora']='2099-01-01 12:00'
    else:datos[campo]=' '
    with pytest.raises(ErrorValidacion):hce.guardar_consulta(r,p['id'],pro['id'],**datos)
    assert leer(s,'ConsultasClinicas')==[]


@pytest.mark.parametrize('rol',['admin','medico','enfermero','administrativo'])
def test_permisos_de_final_en_backend_y_sesion_revocada(final,rol):
    s,ses,r,p,pro,d,i=final
    uid=s.guardar_usuario(ses,dict(usuario='nuevo',password='NuevoTest123',nombre_completo='Prueba',rol=rol))
    usuario=s.repositorio(s.autenticar('nuevo','NuevoTest123'))
    if rol=='admin':assert turnos.guardar_disponibilidad(usuario,{**d,'hora_inicio':'13:00','hora_fin':'15:00'})
    else:
        with pytest.raises(AccesoDenegado):turnos.guardar_disponibilidad(usuario,d)
    if rol in ('admin','administrativo'):assert turnos.agenda_diaria(usuario,'2030-01-08')==[]
    else:
        with pytest.raises(AccesoDenegado):turnos.agenda_diaria(usuario,'2030-01-08')
    if rol=='administrativo':
        with pytest.raises(AccesoDenegado):hce.linea_tiempo(usuario,p['id'])
    else:assert hce.linea_tiempo(usuario,p['id'])['paciente']['id']==p['id']
    if rol in ('admin','medico'):assert hce.guardar_antecedente(usuario,p['id'],pro['id'],'PERSONAL','Prueba')
    else:
        with pytest.raises(AccesoDenegado):hce.guardar_antecedente(usuario,p['id'],pro['id'],'PERSONAL','Prueba')
    s.cambiar_estado_usuario(ses,uid,False)
    with pytest.raises(AccesoDenegado):turnos.agenda_diaria(usuario,'2030-01-08')


def test_migracion_repetida_y_rollback_de_auditoria(final,monkeypatch):
    s,ses,r,p,pro,*_=final
    tablas=['Pacientes','Profesionales','SignosVitales','Prescripciones','DisponibilidadProfesional','Turnos','Auditoria']
    antes={t:leer(s,t) for t in tablas}
    Repositorio(s._repo.ruta)
    assert {t:leer(s,t) for t in tablas}==antes
    monkeypatch.setattr(servicios_final,'_auditar',lambda *a,**k:(_ for _ in ()).throw(RuntimeError('Auditoría indisponible')))
    with pytest.raises(RuntimeError):reservar(final)
    assert {t:leer(s,t) for t in tablas}==antes


def test_gui_final_operaciones_reales(final,raiz_tk):
    s,ses,r,p,pro,d,i=final
    agenda=AgendaProfesionalApp(raiz_tk,r)
    agenda.pro.seleccionar(pro['id']);agenda.fecha.set('2030-01-08')
    assert agenda.consultar_agenda()==[]
    otra=__import__('tkinter').Toplevel(raiz_tk)
    gestion=GestionTurnosApp(otra,r);gestion.paciente.seleccionar(p['id']);gestion.pro.seleccionar(pro['id'])
    gestion.fecha.set('2030-01-08');gestion.motivo.set('Prueba de interfaz');gestion.dni.set(p['dni'])
    assert len(gestion.buscar())==6
    gestion.huecos.selection_set(gestion.huecos.get_children()[0]);tid=gestion.reservar(True)
    gestion.turnos.selection_set(str(tid));gestion.cancelar('Prueba terminada')
    assert leer(s,'Turnos')[0]['estado']=='CANCELADO'
    ventana=__import__('tkinter').Toplevel(raiz_tk);historia=HistoriaClinicaApp(ventana,r)
    historia.paciente.seleccionar(p['id']);historia.pro.seleccionar(pro['id']);historia.cfecha.set('2030-01-07 09:00')
    for control in (historia.cm,historia.ce,historia.cv):control.insert('1.0','Contenido ficticio')
    cid=historia.guardar_consulta();assert cid and historia.eventos.get_children()
    assert historia.actualizar()['paciente']['id']==p['id']
    historia.aaccion.set('A - Alta');historia.mostrar_auditoria()
    assert 'ConsultasClinicas' in historia.audit.get('1.0','end')
    v=__import__('tkinter').Toplevel(raiz_tk);cola=RecordatoriosApp(v,r)
    assert cola.generar()==[]
