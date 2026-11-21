"""Acceso de pacientes al turnero. La identidad y el alcance se validan en cada transacción."""

from contextlib import contextmanager
from datetime import datetime
import secrets

from datos import Repositorio, ErrorValidacion, identificador
from seguridad import AccesoDenegado, hashear_password, verificar_password, _auditar
from servicios_final import operacion, personas, fila, cambiar, auditar_consulta, texto
import turnos


def habilitar_acceso(repo,paciente_id):
    """Emite una clave individual. Solo se devuelve una vez y nunca se audita en claro."""
    clave=secrets.token_urlsafe(18)
    password_hash=hashear_password(clave)
    with operacion(repo,'Turnos') as (c,actor):
        paciente_id=identificador(paciente_id,'un paciente');personas(c,paciente_id=paciente_id)
        c.execute('''INSERT INTO AccesosPortal(paciente_id,password_hash,usuario_alta_id) VALUES(?,?,?)
            ON CONFLICT(paciente_id) DO UPDATE SET password_hash=excluded.password_hash,
            version=AccesosPortal.version+1,activo=1,usuario_alta_id=excluded.usuario_alta_id,fecha_actualizacion=CURRENT_TIMESTAMP''',
            (paciente_id,password_hash,actor['id']))
        _auditar(c,actor,'AccesosPortal',paciente_id,'A',nuevo={'paciente_id':paciente_id,'accion':'Clave emitida o renovada; se revocan las sesiones anteriores.'})
    return clave


def deshabilitar_acceso(repo,paciente_id):
    with operacion(repo,'Turnos') as (c,actor):
        paciente_id=identificador(paciente_id,'un paciente')
        c.execute('UPDATE AccesosPortal SET activo=0,version=version+1,fecha_actualizacion=CURRENT_TIMESTAMP WHERE paciente_id=?',(paciente_id,))
        _auditar(c,actor,'AccesosPortal',paciente_id,'B',nuevo={'paciente_id':paciente_id,'activo':0})


class Portal:
    def __init__(self,ruta):
        self.repo=Repositorio(ruta)
        self._hash_ficticio=hashear_password(secrets.token_urlsafe(32))
        with self.repo.conectar() as c:
            c.execute('BEGIN IMMEDIATE')
            configuracion=c.execute('SELECT usuario_id FROM ConfiguracionPortal WHERE id=1').fetchone()
            if configuracion is None:
                # Cuenta técnica sin contraseña conocida ni acceso entregado a pacientes.
                nombre='portal_web_'+secrets.token_hex(6)
                uid=c.execute("INSERT INTO Usuarios(usuario,password_hash,nombre_completo,rol) VALUES(?,?,?,'administrativo')",
                    (nombre,hashear_password(secrets.token_urlsafe(48)),'Servicio del turnero web')).lastrowid
                c.execute('UPDATE Usuarios SET usuario_alta_id=? WHERE id=?',(uid,uid))
                c.execute('INSERT INTO ConfiguracionPortal(id,usuario_id) VALUES(1,?)',(uid,))
                _auditar(c,{'id':uid,'usuario':nombre},'Usuarios',uid,'A',nuevo={'cuenta_tecnica':'Turnero web','rol':'administrativo'})

    def _actor(self,c):
        a=c.execute('''SELECT u.id,u.usuario,u.rol,u.activo FROM Usuarios u
            JOIN ConfiguracionPortal p ON p.usuario_id=u.id WHERE p.id=1''').fetchone()
        if not a or not a['activo'] or a['rol']!='administrativo':raise AccesoDenegado('El servicio web está deshabilitado.')
        return dict(a)

    def ingresar(self,dni,clave):
        with self.repo.conectar() as c:
            c.execute('BEGIN IMMEDIATE');actor=self._actor(c)
            p=c.execute('''SELECT p.id,p.nombre,p.apellido,p.activo,a.password_hash,a.version,a.activo AS acceso_activo
                FROM Pacientes p JOIN AccesosPortal a ON a.paciente_id=p.id WHERE p.dni=?''',(str(dni).strip(),)).fetchone()
            valida=verificar_password(clave,p['password_hash'] if p else self._hash_ficticio)
            if not p or not valida or not p['activo'] or not p['acceso_activo']:
                raise AccesoDenegado('DNI o clave incorrectos, o acceso deshabilitado.')
            _auditar(c,actor,'Pacientes',p['id'],'L',referencia='Ingreso del paciente al portal web')
            return {'paciente_id':p['id'],'version':p['version']}

    @contextmanager
    def operacion(self,sesion):
        with self.repo.conectar() as c:
            c.execute('BEGIN IMMEDIATE');actor=self._actor(c)
            p=c.execute('''SELECT p.*,a.version,a.activo AS acceso_activo FROM Pacientes p
                JOIN AccesosPortal a ON a.paciente_id=p.id WHERE p.id=?''',(sesion['paciente_id'],)).fetchone()
            if not p or not p['activo'] or not p['acceso_activo'] or p['version']!=sesion['version']:
                raise AccesoDenegado('El acceso venció o fue deshabilitado. Ingrese nuevamente.')
            yield c,actor,dict(p)

    def identidad(self,sesion):
        with self.operacion(sesion) as (c,a,p):return {'nombre':p['nombre'],'apellido':p['apellido']}

    def catalogos(self,sesion):
        with self.operacion(sesion) as (c,a,p):
            return {'especialidades':[dict(x) for x in c.execute('SELECT id,nombre FROM Especialidades WHERE activo=1 ORDER BY nombre')],
                'profesionales':[dict(x) for x in c.execute('''SELECT p.id,p.nombre,p.apellido,p.especialidad_id FROM Profesionales p
                    JOIN Especialidades e ON e.id=p.especialidad_id WHERE p.activo=1 AND e.activo=1 ORDER BY p.apellido,p.nombre''')]}

    def disponibles(self,sesion,dia,profesional_id=None,especialidad_id=None):
        with self.operacion(sesion) as (c,a,p):
            dia=turnos._futura(dia)
            huecos=turnos._huecos(c,dia,profesional_id,especialidad_id,p['id'])
            auditar_consulta(c,a,'Pacientes',p['id'],{'portal_web':'Disponibilidad','fecha':dia})
            return [{k:v for k,v in h.items() if k!='ocupacion'} for h in huecos]

    def mis_turnos(self,sesion):
        with self.operacion(sesion) as (c,a,p):
            filas=c.execute('''SELECT t.id,t.fecha,t.hora_inicio,t.hora_fin,t.estado,t.motivo_consulta,t.turno_origen_id,
                t.canal_solicitud,t.canal_confirmacion,r.nombre||' '||r.apellido AS profesional,e.nombre AS especialidad
                FROM Turnos t JOIN Profesionales r ON r.id=t.profesional_id JOIN Especialidades e ON e.id=r.especialidad_id
                WHERE t.paciente_id=? ORDER BY t.fecha DESC,t.hora_inicio DESC,t.id DESC''',(p['id'],)).fetchall()
            auditar_consulta(c,a,'Pacientes',p['id'],{'portal_web':'Mis turnos'})
            return [dict(f,gestionable=f['estado'] in turnos.OCUPADOS and datetime.fromisoformat(f['fecha']+'T'+f['hora_inicio'])>turnos.ahora()) for f in filas]

    def reservar(self,sesion,datos):
        with self.operacion(sesion) as (c,a,p):
            return turnos._crear(c,a,p['id'],datos.get('profesional_id'),datos.get('fecha'),datos.get('hora_inicio'),datos.get('motivo'),canal='WEB')

    def gestionar(self,sesion,turno_id,accion,datos):
        with self.operacion(sesion) as (c,a,p):
            t=fila(c,'Turnos',turno_id)
            if t['paciente_id']!=p['id']:raise AccesoDenegado('El turno no está disponible para este acceso.')
            if t['estado'] not in turnos.OCUPADOS or datetime.fromisoformat(t['fecha']+'T'+t['hora_inicio'])<=turnos.ahora():
                raise ErrorValidacion('El turno ya no admite cambios desde el portal.')
            cambios={'fecha_actualizacion':turnos.ahora().isoformat()}
            if accion=='confirmar':
                if t['estado']!='SOLICITADO':raise ErrorValidacion('El turno ya está confirmado.')
                personas(c,p['id'],t['profesional_id'])
                cambios.update(estado='CONFIRMADO',canal_confirmacion='WEB',fecha_confirmacion=turnos.ahora().isoformat())
            elif accion in ('cancelar','reprogramar'):
                razon=texto(datos.get('motivo'),'el motivo del cambio',2000)
                cambios.update(estado='CANCELADO' if accion=='cancelar' else 'REPROGRAMADO',observaciones=(t['observaciones'] or '')+'\nPortal web: '+razon)
            else:raise ErrorValidacion('Operación inválida.')
            if accion=='reprogramar':
                pro=identificador(datos.get('profesional_id'),'un profesional')
                if (pro,datos.get('fecha'),datos.get('hora_inicio'))==(t['profesional_id'],t['fecha'],t['hora_inicio']):
                    raise ErrorValidacion('Seleccione un horario o profesional diferente.')
            cambiar(c,a,'Turnos',t['id'],cambios)
            if accion!='confirmar':turnos._cancelar_recordatorios(c,a,t['id'],'Cambio desde el portal web')
            if accion=='reprogramar':
                return turnos._crear(c,a,p['id'],pro,datos.get('fecha'),datos.get('hora_inicio'),t['motivo_consulta'],razon,turno_origen_id=t['id'],canal='WEB')
            return t['id']

    def salir(self,sesion):
        with self.operacion(sesion) as (c,a,p):_auditar(c,a,'Pacientes',p['id'],'X',referencia='Salida del portal web')
