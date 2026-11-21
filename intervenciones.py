"""Consulta consolidada y trazable de intervenciones existentes."""

from datos import ErrorValidacion


def consultar(repositorio, paciente_id):
    from seguridad import _auditar
    servicio = repositorio._servicio
    with servicio._repo.conectar() as c:
        c.execute('BEGIN IMMEDIATE')
        actor = servicio._actor(c, repositorio._sesion, 'Intervenciones')
        servicio._repo.transaccion = c
        try:
            paciente = servicio._repo.obtener_paciente(paciente_id)
            signos = servicio._repo.listar_signos(paciente_id, activos=None)
            recetas = servicio._repo.listar_prescripciones(paciente_id, activos=None)
            practicas = [dict(f) for f in c.execute('''SELECT p.*,r.nombre||' '||r.apellido AS profesional
                FROM Practicas p JOIN Profesionales r ON r.id=p.profesional_id
                WHERE paciente_id=? ORDER BY fecha_solicitud DESC,id DESC''', (paciente_id,))]
            # Q = consulta: se migra la restricción del log de forma compatible en E9.
            _auditar(c, actor, 'Pacientes', paciente_id, 'Q', nuevo={'consulta_intervenciones': True})
            return dict(paciente=paciente, signos=signos, prescripciones=recetas, practicas=practicas)
        finally:
            servicio._repo.transaccion = None


def registrar_practica(repositorio, paciente_id, profesional_id, codigo, descripcion):
    from seguridad import _auditar
    if not str(codigo).strip() or not str(descripcion).strip():
        raise ErrorValidacion('Complete código y descripción de la práctica.')
    servicio = repositorio._servicio
    with servicio._repo.conectar() as c:
        c.execute('BEGIN IMMEDIATE')
        actor = servicio._actor(c, repositorio._sesion, 'FHIR')
        servicio._repo._paciente_activo(c, paciente_id)
        servicio._repo._profesional_existente(c, profesional_id, activo=True)
        i = c.execute('''INSERT INTO Practicas (paciente_id,profesional_id,codigo,sistema_codigo,
            descripcion,fecha_solicitud,usuario_alta_id) VALUES (?,?,?,'urn:openhis:practicas',?,CURRENT_TIMESTAMP,?)''',
            (paciente_id, profesional_id, codigo.strip(), descripcion.strip(), actor['id'])).lastrowid
        _auditar(c, actor, 'Practicas', i, 'A', nuevo={'codigo': codigo, 'paciente_id': paciente_id})
        return i
