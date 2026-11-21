"""Epic 3: migración aditiva y repetible de agendas, turnos e historia clínica."""


def ampliar_final(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS DisponibilidadProfesional (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profesional_id INTEGER NOT NULL REFERENCES Profesionales(id),
        dia_semana INTEGER NOT NULL CHECK(dia_semana BETWEEN 0 AND 6),
        hora_inicio TEXT NOT NULL, hora_fin TEXT NOT NULL,
        duracion_minutos INTEGER NOT NULL CHECK(duracion_minutos BETWEEN 5 AND 240),
        fecha_desde TEXT NOT NULL, fecha_hasta TEXT,
        activo INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0,1)),
        usuario_alta_id INTEGER NOT NULL REFERENCES Usuarios(id),
        fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK(hora_inicio < hora_fin), CHECK(fecha_hasta IS NULL OR fecha_desde<=fecha_hasta)
    );
    CREATE INDEX IF NOT EXISTS idx_disponibilidad_prof ON DisponibilidadProfesional(profesional_id,dia_semana,activo);
    CREATE TABLE IF NOT EXISTS BloqueosAgenda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profesional_id INTEGER NOT NULL REFERENCES Profesionales(id),
        fecha TEXT NOT NULL, hora_inicio TEXT, hora_fin TEXT,
        tipo TEXT NOT NULL CHECK(tipo IN ('BLOQUEO','VACACIONES','LICENCIA','OTRO')),
        motivo TEXT NOT NULL CHECK(length(trim(motivo))>0),
        activo INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0,1)),
        usuario_alta_id INTEGER NOT NULL REFERENCES Usuarios(id),
        fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK((hora_inicio IS NULL AND hora_fin IS NULL) OR
              (hora_inicio IS NOT NULL AND hora_fin IS NOT NULL AND hora_inicio<hora_fin))
    );
    CREATE INDEX IF NOT EXISTS idx_bloqueos_prof_fecha ON BloqueosAgenda(profesional_id,fecha,activo);
    CREATE TABLE IF NOT EXISTS Turnos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL REFERENCES Pacientes(id),
        profesional_id INTEGER NOT NULL REFERENCES Profesionales(id),
        fecha TEXT NOT NULL, hora_inicio TEXT NOT NULL, hora_fin TEXT NOT NULL,
        estado TEXT NOT NULL DEFAULT 'SOLICITADO'
          CHECK(estado IN ('SOLICITADO','CONFIRMADO','CANCELADO','REPROGRAMADO','ATENDIDO','AUSENTE')),
        motivo_consulta TEXT NOT NULL CHECK(length(trim(motivo_consulta))>0), observaciones TEXT,
        canal_solicitud TEXT NOT NULL DEFAULT 'TELEFONO' CHECK(canal_solicitud IN ('TELEFONO','WEB')),
        canal_confirmacion TEXT CHECK(canal_confirmacion IN ('TELEFONO','WEB')), fecha_confirmacion TEXT,
        turno_origen_id INTEGER REFERENCES Turnos(id),
        usuario_alta_id INTEGER NOT NULL REFERENCES Usuarios(id),
        fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK(hora_inicio<hora_fin)
    );
    CREATE INDEX IF NOT EXISTS idx_turnos_prof_fecha ON Turnos(profesional_id,fecha,estado);
    CREATE INDEX IF NOT EXISTS idx_turnos_paciente ON Turnos(paciente_id,fecha);
    CREATE TABLE IF NOT EXISTS ColaNotificaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT, turno_id INTEGER NOT NULL REFERENCES Turnos(id),
        tipo TEXT NOT NULL DEFAULT 'RECORDATORIO_24H' CHECK(tipo='RECORDATORIO_24H'),
        destinatario TEXT, mensaje TEXT NOT NULL, programada_para TEXT NOT NULL,
        estado TEXT NOT NULL CHECK(estado IN ('PENDIENTE','ERROR','CANCELADA')),
        resultado TEXT NOT NULL,
        usuario_alta_id INTEGER NOT NULL REFERENCES Usuarios(id),
        fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(turno_id,tipo)
    );
    CREATE TABLE IF NOT EXISTS ConsultasClinicas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL REFERENCES Pacientes(id),
        profesional_id INTEGER NOT NULL REFERENCES Profesionales(id),
        turno_id INTEGER REFERENCES Turnos(id), fecha_hora TEXT NOT NULL,
        motivo_consulta TEXT NOT NULL CHECK(length(trim(motivo_consulta))>0),
        evaluacion TEXT NOT NULL CHECK(length(trim(evaluacion))>0),
        evolucion TEXT NOT NULL CHECK(length(trim(evolucion))>0),
        usuario_registro_id INTEGER NOT NULL REFERENCES Usuarios(id),
        fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_consultas_paciente ON ConsultasClinicas(paciente_id,fecha_hora);
    CREATE TABLE IF NOT EXISTS AntecedentesClinicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL REFERENCES Pacientes(id),
        profesional_id INTEGER NOT NULL REFERENCES Profesionales(id),
        tipo TEXT NOT NULL CHECK(tipo IN ('PERSONAL','FAMILIAR')),
        descripcion TEXT NOT NULL CHECK(length(trim(descripcion))>0),
        activo INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0,1)),
        usuario_registro_id INTEGER NOT NULL REFERENCES Usuarios(id),
        fecha_registro TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, fecha_actualizacion TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_antecedentes_paciente ON AntecedentesClinicos(paciente_id,activo);
    """)
    ampliar_canales_web(c)
    # La base también protege el intervalo, incluso con escritores concurrentes.
    for evento in ('INSERT', 'UPDATE'):
        distinto = 'AND t.id<>NEW.id' if evento == 'UPDATE' else ''
        c.executescript(f"""
        CREATE TRIGGER IF NOT EXISTS turnos_no_solapar_{evento.lower()}
        BEFORE {evento} ON Turnos WHEN NEW.estado IN ('SOLICITADO','CONFIRMADO')
        BEGIN
          SELECT CASE WHEN EXISTS(SELECT 1 FROM Turnos t
            WHERE t.fecha=NEW.fecha AND t.estado IN ('SOLICITADO','CONFIRMADO')
              AND (t.profesional_id=NEW.profesional_id OR t.paciente_id=NEW.paciente_id)
              AND NEW.hora_inicio<t.hora_fin AND NEW.hora_fin>t.hora_inicio {distinto})
            THEN RAISE(ABORT,'Turno superpuesto para el profesional o el paciente.') END;
        END;
        """)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS AccesosPortal (
        paciente_id INTEGER PRIMARY KEY REFERENCES Pacientes(id),
        password_hash TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
        activo INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0,1)),
        usuario_alta_id INTEGER NOT NULL REFERENCES Usuarios(id),
        fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS ConfiguracionPortal (
        id INTEGER PRIMARY KEY CHECK(id=1),
        usuario_id INTEGER NOT NULL UNIQUE REFERENCES Usuarios(id)
    );
    """)


def ampliar_canales_web(c):
    """Reconstruye el CHECK antiguo sin cambiar IDs, relaciones, índices ni secuencia."""
    sql=c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Turnos'").fetchone()[0]
    if "'WEB'" in sql:return
    if c.in_transaction:raise RuntimeError('La migración de canales requiere una conexión sin transacción.')
    import re
    fk=c.execute('PRAGMA foreign_keys').fetchone()[0]
    c.execute('PRAGMA foreign_keys=OFF')
    try:
        c.execute('BEGIN IMMEDIATE')
        # Otra instancia puede haber completado la migración mientras se esperaba el bloqueo.
        sql=c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Turnos'").fetchone()[0]
        if "'WEB'" not in sql:
            objetos=[r[0] for r in c.execute("SELECT sql FROM sqlite_master WHERE tbl_name='Turnos' AND type IN ('index','trigger') AND sql IS NOT NULL")]
            secuencia=c.execute("SELECT seq FROM sqlite_sequence WHERE name='Turnos'").fetchone()
            nueva=re.sub(r'CREATE TABLE\s+["`\[]?Turnos["`\]]?', 'CREATE TABLE Turnos_web_nueva',sql,count=1,flags=re.I)
            for campo in ('canal_solicitud','canal_confirmacion'):
                nueva=nueva.replace(campo+"='TELEFONO'",campo+" IN ('TELEFONO','WEB')")
            c.execute(nueva)
            columnas=','.join('"'+r['name']+'"' for r in c.execute('PRAGMA table_info(Turnos)'))
            c.execute(f'INSERT INTO Turnos_web_nueva ({columnas}) SELECT {columnas} FROM Turnos')
            c.execute('DROP TABLE Turnos')
            c.execute('ALTER TABLE Turnos_web_nueva RENAME TO Turnos')
            for objeto in objetos:c.execute(objeto)
            if secuencia:c.execute("UPDATE sqlite_sequence SET seq=MAX(seq,?) WHERE name='Turnos'",(secuencia[0],))
            if c.execute('PRAGMA foreign_key_check').fetchall():raise RuntimeError('La migración de canales dejó referencias inválidas.')
        c.commit()
    except BaseException:
        c.rollback();raise
    finally:c.execute('PRAGMA foreign_keys='+str(fk))
