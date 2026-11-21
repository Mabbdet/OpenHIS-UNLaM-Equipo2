from concurrent.futures import ThreadPoolExecutor
import json
import sqlite3

import pytest

from datos import Repositorio, ErrorValidacion
from seguridad import AccesoDenegado
from tests.test_entrega9 import entorno
from tests.test_final import final, leer, reservar
from turnero_web import crear_app
from esquema_final import ampliar_canales_web
import portal
import servicios_final
import turnos


@pytest.fixture
def web(final):
    s,ses,r,p,pro,*_=final
    clave=portal.habilitar_acceso(r,p['id'])
    app=crear_app(s._repo.ruta,{'TESTING':True})
    cliente=app.test_client()
    token=cliente.get('/api/sesion').json['csrf']
    ingreso=cliente.post('/api/ingresar',json={'dni':p['dni'],'clave':clave},headers={'X-CSRF-Token':token})
    assert ingreso.status_code==200
    return final,app,cliente,ingreso.json['csrf'],clave


def enviar(web,ruta,datos):
    return web[2].post(ruta,json=datos,headers={'X-CSRF-Token':web[3]})


def datos_turno(f,hora='08:00'):
    return {'profesional_id':f[4]['id'],'fecha':'2030-01-08','hora_inicio':hora,'motivo':'Control ficticio desde la web'}


def test_reserva_web_confirmacion_escritorio_y_cancelacion(web):
    f,app,c,*_=web;s,ses,r,p,pro,*_=f
    huecos=c.get('/api/disponibles?fecha=2030-01-08').json['huecos']
    assert len(huecos)==6 and not any('paciente' in json.dumps(h) for h in huecos)
    resultado=enviar(web,'/api/turnos',datos_turno(f));assert resultado.status_code==201
    tid=resultado.json['turno_id'];t=leer(s,'Turnos')[0]
    assert t['canal_solicitud']=='WEB' and t['estado']=='SOLICITADO'
    assert len(turnos.disponibles(r,'2030-01-08',pro['id']))==5
    assert enviar(web,f'/api/turnos/{tid}/confirmar',{}).status_code==200
    assert leer(s,'Turnos')[0]['canal_confirmacion']=='WEB'
    turnos.cambiar_estado(r,tid,'CANCELADO',motivo='Cancelación telefónica de prueba')
    assert c.get('/api/turnos').json['turnos'][0]['estado']=='CANCELADO'


def test_cancelar_web_libera_horario_y_cola(web,monkeypatch):
    f,app,c,*_=web;s,ses,r,p,*_=f
    tid=reservar(f,confirmado=True)
    from datetime import datetime
    monkeypatch.setattr(turnos,'ahora',lambda:datetime(2030,1,7,8,1))
    turnos.generar_recordatorios(r)
    assert enviar(web,f'/api/turnos/{tid}/cancelar',{'motivo':'Cambio de disponibilidad'}).status_code==200
    assert leer(s,'ColaNotificaciones')[0]['estado']=='CANCELADA'
    assert len(c.get('/api/disponibles?fecha=2030-01-08').json['huecos'])==6


def test_reprogramacion_web_atomica_preserva_origen(web):
    f,app,c,*_=web;s=f[0];tid=reservar(f)
    assert enviar(web,f'/api/turnos/{tid}/reprogramar',datos_turno(f,'23:00')).status_code==409
    assert leer(s,'Turnos')[0]['estado']=='SOLICITADO'
    assert enviar(web,f'/api/turnos/{tid}/reprogramar',datos_turno(f)).status_code==409
    respuesta=enviar(web,f'/api/turnos/{tid}/reprogramar',datos_turno(f,'09:00'))
    assert respuesta.status_code==200
    viejos,nuevo=leer(s,'Turnos');assert viejos['estado']=='REPROGRAMADO'
    assert nuevo['turno_origen_id']==tid and nuevo['canal_solicitud']=='WEB'


def test_aislamiento_paciente_y_campos_manipulados(web):
    f,app,c,*_=web;s,ses,r,p,pro,*_=f
    otro=next(x for x in r.listar_pacientes() if x['id']!=p['id'])
    ajeno=turnos.reservar(r,otro['id'],pro['id'],'2030-01-08','10:00','Turno privado ajeno')
    assert all(t['id']!=ajeno for t in c.get('/api/turnos').json['turnos'])
    assert enviar(web,f'/api/turnos/{ajeno}/cancelar',{'motivo':'Intento ajeno'}).status_code==401
    d={**datos_turno(f),'paciente_id':otro['id'],'estado':'ATENDIDO','usuario_alta_id':1,'canal_solicitud':'TELEFONO'}
    assert enviar(web,'/api/turnos',d).status_code==201
    assert leer(s,'Turnos')[-1]['paciente_id']==p['id']
    assert leer(s,'Turnos')[-1]['estado']=='SOLICITADO'
    assert leer(s,'Turnos')[0]['estado']=='SOLICITADO'


def test_web_y_telefono_compiten_por_el_mismo_horario(web):
    f,app,c,*_=web;s,ses,r,p,pro,*_=f
    acceso=app.extensions['portal'].ingresar(p['dni'],web[-1])
    def intentar(canal):
        try:return app.extensions['portal'].reservar(acceso,datos_turno(f)) if canal=='WEB' else reservar(f)
        except ErrorValidacion:return None
    with ThreadPoolExecutor(max_workers=2) as pool:resultados=list(pool.map(intentar,['WEB','TELEFONO']))
    assert sum(x is not None for x in resultados)==1
    assert len(leer(s,'Turnos'))==1


@pytest.mark.parametrize('baja',['paciente','acceso','renovacion','servicio'])
def test_sesiones_se_revocan_en_cada_peticion(web,baja):
    f,app,c,*_=web;s,ses,r,p,*_=f
    if baja=='paciente':r.dar_baja_paciente(p['id'])
    elif baja=='acceso':portal.deshabilitar_acceso(r,p['id'])
    elif baja=='renovacion':portal.habilitar_acceso(r,p['id'])
    else:
        with s._repo.conectar() as conn:conn.execute('UPDATE Usuarios SET activo=0 WHERE id=(SELECT usuario_id FROM ConfiguracionPortal WHERE id=1)')
    assert c.get('/api/turnos').status_code==401
    assert enviar(web,'/api/turnos',datos_turno(f)).status_code==401


def test_csrf_logout_vencimiento_y_cookies(web):
    f,app,c,token,clave=web
    assert c.post('/api/turnos',json=datos_turno(f)).status_code==403
    assert c.post('/api/turnos',json=datos_turno(f),headers={'X-CSRF-Token':'otro'}).status_code==403
    assert enviar(web,'/api/salir',{}).status_code==200
    assert c.get('/api/turnos').status_code==401
    token=c.get('/api/sesion').json['csrf']
    r=c.post('/api/ingresar',json={'dni':f[3]['dni'],'clave':clave},headers={'X-CSRF-Token':token})
    assert 'HttpOnly' in r.headers['Set-Cookie'] and 'SameSite=Strict' in r.headers['Set-Cookie']
    with c.session_transaction() as ses:sid=ses['sid']
    app.extensions['accesos_portal'][sid]['vence']=0
    assert c.get('/api/turnos').status_code==401


def test_ingreso_invalido_limite_intentos_y_anonimos(web):
    f,app,*_=web;c=app.test_client();token=c.get('/api/sesion').json['csrf']
    for ruta in ['/api/turnos','/api/catalogos','/api/disponibles?fecha=2030-01-08']:assert c.get(ruta).status_code==401
    # La autenticación válida del fixture ya cuenta como un intento desde esta IP.
    for _ in range(7):assert c.post('/api/ingresar',json={'dni':'inexistente','clave':'Incorrecta'},headers={'X-CSRF-Token':token}).status_code==401
    assert c.post('/api/ingresar',json={'dni':f[3]['dni'],'clave':web[-1]},headers={'X-CSRF-Token':token}).status_code==429


def test_autoria_sin_filtrar_secretos_y_rollback(web,monkeypatch):
    f,app,c,*_=web;s=f[0]
    assert web[-1] not in json.dumps(leer(s,'Auditoria'))
    def fallar(*args,**kwargs):raise sqlite3.OperationalError('Auditoría inaccesible')
    monkeypatch.setattr(servicios_final,'_auditar',fallar)
    assert enviar(web,'/api/turnos',datos_turno(f)).status_code==409
    assert leer(s,'Turnos')==[]


@pytest.mark.parametrize('rol',['medico','enfermero'])
def test_solo_personal_autorizado_emite_claves(final,rol):
    s,ses,r,p,*_=final
    s.guardar_usuario(ses,dict(usuario=rol,password='ClavePrueba123',nombre_completo='Prueba',rol=rol))
    otro=s.repositorio(s.autenticar(rol,'ClavePrueba123'))
    with pytest.raises(AccesoDenegado):portal.habilitar_acceso(otro,p['id'])


def test_recursos_web_headers_escape_y_errores(web):
    f,app,c,*_=web
    for ruta in ['/','/static/turnero.css','/static/turnero.js']:
        r=c.get(ruta);assert r.status_code==200
        assert r.headers['X-Frame-Options']=='DENY'
        assert 'no-store' in r.headers['Cache-Control']
    assert c.get('/',headers={'Host':'sitio-ajeno.invalid'}).status_code==400
    assert enviar(web,'/api/turnos',[]).status_code==409
    assert enviar(web,'/api/turnos',datos_turno(f,'25:00')).status_code==409
    assert c.get('/api/disponibles?fecha=incorrecta').status_code==409
    assert c.post('/api/turnos',data='x'*9000,content_type='application/json',headers={'X-CSRF-Token':web[3]}).status_code==413


def test_migracion_canales_con_hijos_y_secuencia(final):
    s,ses,r,p,pro,*_=final;tid=reservar(final,confirmado=True)
    with s._repo.conectar() as c:
        c.execute('PRAGMA foreign_keys=OFF');c.execute('BEGIN')
        sql=c.execute("SELECT sql FROM sqlite_master WHERE name='Turnos'").fetchone()[0]
        antigua=sql.replace('CREATE TABLE Turnos','CREATE TABLE Turnos_antigua').replace("IN ('TELEFONO','WEB')","='TELEFONO'")
        c.execute(antigua);c.execute('INSERT INTO Turnos_antigua SELECT * FROM Turnos')
        c.execute('DROP TABLE Turnos');c.execute('ALTER TABLE Turnos_antigua RENAME TO Turnos')
        c.execute('CREATE INDEX prueba_indice_turno ON Turnos(canal_solicitud)')
        c.execute("UPDATE sqlite_sequence SET seq=90 WHERE name='Turnos'")
        c.execute('''INSERT INTO ConsultasClinicas(paciente_id,profesional_id,turno_id,fecha_hora,motivo_consulta,evaluacion,evolucion,usuario_registro_id)
            VALUES(?,?,?,'2030-01-08','Ficticio','Ficticio','Ficticio',1)''',(p['id'],pro['id'],tid))
        c.commit();c.execute('PRAGMA foreign_keys=ON')
        antes=[dict(x) for x in c.execute('SELECT * FROM Turnos')]
    Repositorio(s._repo.ruta);Repositorio(s._repo.ruta)
    with s._repo.conectar() as c:
        assert [dict(x) for x in c.execute('SELECT * FROM Turnos')]==antes
        assert c.execute('PRAGMA foreign_key_check').fetchall()==[]
        assert c.execute("SELECT 1 FROM sqlite_master WHERE name='prueba_indice_turno'").fetchone()
        assert c.execute("SELECT seq FROM sqlite_sequence WHERE name='Turnos'").fetchone()[0]==90
    assert turnos.reservar(r,p['id'],pro['id'],'2030-01-08','09:00','Prueba')==91
