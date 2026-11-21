"""Entrega 9: prácticas e identificación de recursos recibidos."""


def ampliar_intercambio(c):
    auditoria_sql = c.execute("SELECT sql FROM sqlite_master WHERE name='Auditoria'").fetchone()[0]
    if "'Q'" not in auditoria_sql:
        nuevo_sql = auditoria_sql.replace('Auditoria', 'Auditoria_e9', 1).replace("'C'", "'C','Q'")
        c.execute(nuevo_sql)
        columnas = ','.join(r['name'] for r in c.execute('PRAGMA table_info(Auditoria)'))
        c.execute(f'INSERT INTO Auditoria_e9 ({columnas}) SELECT {columnas} FROM Auditoria')
        c.execute('DROP TABLE Auditoria')
        c.execute('ALTER TABLE Auditoria_e9 RENAME TO Auditoria')
        from esquema_seguridad import ampliar_seguridad
        ampliar_seguridad(c)
    # Los profesionales externos pueden no informar nacimiento o género.
    sql = c.execute("SELECT sql FROM sqlite_master WHERE name='Profesionales'").fetchone()[0]
    if "'U'" not in sql:
        c.commit()
        c.execute("PRAGMA foreign_keys=OFF")
        try:
            c.execute("BEGIN")
            c.execute("""CREATE TABLE Profesionales_e9 (
                id INTEGER PRIMARY KEY AUTOINCREMENT, dni TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL, apellido TEXT NOT NULL, fecha_nacimiento TEXT,
                sexo TEXT NOT NULL CHECK(sexo IN ('M','F','O','U')),
                matricula TEXT UNIQUE NOT NULL, especialidad_id INTEGER NOT NULL,
                telefono TEXT,email TEXT,fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activo INTEGER DEFAULT 1,usuario_alta_id INTEGER REFERENCES Usuarios(id),
                FOREIGN KEY(especialidad_id) REFERENCES Especialidades(id))""")
            campos = [r['name'] for r in c.execute('PRAGMA table_info(Profesionales)')]
            columnas = ','.join(campos)
            sec = c.execute("SELECT seq FROM sqlite_sequence WHERE name='Profesionales'").fetchone()
            c.execute(f"INSERT INTO Profesionales_e9 ({columnas}) SELECT {columnas} FROM Profesionales")
            c.execute('DROP TABLE Profesionales')
            c.execute('ALTER TABLE Profesionales_e9 RENAME TO Profesionales')
            if sec:
                c.execute("UPDATE sqlite_sequence SET seq=MAX(seq,?) WHERE name='Profesionales'", (sec[0],))
            if c.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('La migración de profesionales violaría relaciones existentes.')
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.execute('PRAGMA foreign_keys=ON')
    c.executescript("""
        CREATE TABLE IF NOT EXISTS Practicas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL REFERENCES Pacientes(id),
            profesional_id INTEGER NOT NULL REFERENCES Profesionales(id),
            codigo TEXT NOT NULL,sistema_codigo TEXT NOT NULL,descripcion TEXT NOT NULL,
            fecha_solicitud TEXT NOT NULL,activo INTEGER DEFAULT 1,
            usuario_alta_id INTEGER REFERENCES Usuarios(id)
        );
        CREATE TABLE IF NOT EXISTS RecursosFHIR (
            id INTEGER PRIMARY KEY AUTOINCREMENT,origen TEXT NOT NULL,
            tipo TEXT NOT NULL,id_externo TEXT NOT NULL,tabla_local TEXT NOT NULL,
            registro_id INTEGER NOT NULL,contenido TEXT NOT NULL,
            fecha_importacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(origen,tipo,id_externo)
        );
        CREATE INDEX IF NOT EXISTS idx_practicas_paciente ON Practicas(paciente_id,fecha_solicitud);
    """)
    # El responsable de una observación externa es opcional. Las altas locales
    # conservan el requisito de seleccionar un profesional.
    columnas = {r['name'] for r in c.execute('PRAGMA table_info(SignosVitales)')}
    if 'origen_fhir' not in columnas:
        c.execute('ALTER TABLE SignosVitales ADD COLUMN origen_fhir TEXT')
    trigger = c.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name='signos_medico_requerido'").fetchone()
    if trigger and 'origen_fhir' not in trigger[0]:
        c.execute('DROP TRIGGER signos_medico_requerido')
    c.executescript("""
        CREATE TRIGGER IF NOT EXISTS signos_medico_requerido
        BEFORE INSERT ON SignosVitales
        WHEN NEW.medico_id IS NULL AND COALESCE(trim(NEW.origen_fhir),'')=''
        BEGIN SELECT RAISE(ABORT, 'Seleccione un profesional para registrar signos vitales.'); END;
        CREATE TRIGGER IF NOT EXISTS signos_conservar_origen_fhir
        BEFORE UPDATE OF origen_fhir ON SignosVitales
        WHEN NEW.medico_id IS NULL AND COALESCE(trim(OLD.origen_fhir),'')<>''
             AND COALESCE(trim(NEW.origen_fhir),'')=''
        BEGIN SELECT RAISE(ABORT, 'Conserve el origen FHIR del signo sin profesional informado.'); END;
    """)
