"""Operaciones internas de Epic 3: sesión vigente, transacción y auditoría juntas."""

from contextlib import contextmanager
from datetime import datetime, timezone, timedelta, date
import sqlite3

from datos import ErrorValidacion, identificador
from seguridad import _auditar

ZONA_TURNOS = timezone(timedelta(hours=-3), 'Argentina UTC-03')
TABLAS = {'DisponibilidadProfesional', 'BloqueosAgenda', 'Turnos', 'ColaNotificaciones',
          'ConsultasClinicas', 'AntecedentesClinicos'}


def ahora():
    return datetime.now(ZONA_TURNOS).replace(tzinfo=None, microsecond=0)


def fecha(valor):
    try:
        texto = str(valor).strip()
        d = date.fromisoformat(texto)
        if d.isoformat() != texto: raise ValueError
        return d
    except (ValueError, TypeError):
        raise ErrorValidacion('Use una fecha válida AAAA-MM-DD.') from None


def hora(valor):
    try:
        texto = str(valor).strip()
        h = datetime.strptime(texto, '%H:%M')
        if h.strftime('%H:%M') != texto: raise ValueError
        return texto
    except (ValueError, TypeError):
        raise ErrorValidacion('Use una hora válida HH:MM.') from None


def texto(valor, etiqueta, maximo=10000):
    valor = str(valor or '').strip()
    if not valor or len(valor) > maximo:
        raise ErrorValidacion(f'Complete {etiqueta} (hasta {maximo} caracteres).')
    return valor


@contextmanager
def operacion(repo, permiso):
    servicio = repo._servicio
    with servicio._repo.conectar() as c:
        c.execute('BEGIN IMMEDIATE')
        actor = servicio._actor(c, repo._sesion, permiso)
        try:
            yield c, actor
        except sqlite3.IntegrityError as error:
            raise ErrorValidacion(str(error)) from error


def fila(c, tabla, registro_id):
    if tabla not in TABLAS: raise ValueError('Tabla no admitida.')
    r = c.execute(f'SELECT * FROM {tabla} WHERE id=?', (identificador(registro_id, 'un registro'),)).fetchone()
    if r is None: raise ErrorValidacion('El registro no existe. Actualice el listado.')
    return dict(r)


def personas(c, paciente_id=None, profesional_id=None):
    for tabla, valor in (('Pacientes', paciente_id), ('Profesionales', profesional_id)):
        if valor is not None:
            r = c.execute(f'SELECT activo FROM {tabla} WHERE id=?', (identificador(valor, 'una ficha'),)).fetchone()
            if r is None or r['activo'] != 1:
                raise ErrorValidacion(f'Seleccione una ficha activa de {tabla}.')


def insertar(c, actor, tabla, datos):
    if tabla not in TABLAS: raise ValueError('Tabla no admitida.')
    autor = 'usuario_registro_id' if tabla in ('ConsultasClinicas','AntecedentesClinicos') else 'usuario_alta_id'
    datos = {**datos, autor: actor['id']}
    campos = ','.join(datos)
    registro_id = c.execute(f'INSERT INTO {tabla} ({campos}) VALUES ({",".join("?" for _ in datos)})', tuple(datos.values())).lastrowid
    _auditar(c, actor, tabla, registro_id, 'A', nuevo=fila(c, tabla, registro_id))
    return registro_id


def cambiar(c, actor, tabla, registro_id, datos, accion='M'):
    anterior = fila(c, tabla, registro_id)
    c.execute(f'UPDATE {tabla} SET {",".join(k+"=?" for k in datos)} WHERE id=?', (*datos.values(), registro_id))
    _auditar(c, actor, tabla, registro_id, accion, anterior, fila(c, tabla, registro_id))


def auditar_consulta(c, actor, tabla, registro_id=None, datos=None):
    _auditar(c, actor, tabla, registro_id, 'Q', nuevo=datos)
