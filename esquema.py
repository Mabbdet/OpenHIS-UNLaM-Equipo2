"""Ampliación de SQLite para Entrega 4, preservando los registros anteriores."""


def ampliar_esquema(conexion):
    conexion.executescript("""
        CREATE TABLE IF NOT EXISTS Especialidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL, descripcion TEXT,
            activo INTEGER DEFAULT 1, fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS SnomedCT (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL, termino TEXT NOT NULL, descripcion TEXT, categoria TEXT,
            activo INTEGER DEFAULT 1, fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS Farmacos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL, principio_activo TEXT,
            presentacion TEXT, concentracion TEXT, via_administracion TEXT,
            activo INTEGER DEFAULT 1, fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS Profesionales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dni TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL, apellido TEXT NOT NULL,
            fecha_nacimiento TEXT NOT NULL, sexo TEXT NOT NULL CHECK (sexo IN ('M', 'F')),
            matricula TEXT UNIQUE NOT NULL, especialidad_id INTEGER NOT NULL,
            telefono TEXT, email TEXT, fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (especialidad_id) REFERENCES Especialidades(id)
        );
        CREATE TABLE IF NOT EXISTS Prescripciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL, profesional_id INTEGER NOT NULL,
            farmaco_id INTEGER NOT NULL, snomed_id INTEGER,
            dosis TEXT NOT NULL, via_administracion TEXT NOT NULL, frecuencia TEXT NOT NULL,
            duracion TEXT, cantidad INTEGER, indicaciones TEXT,
            fecha_prescripcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_inicio TEXT, fecha_fin TEXT, activo INTEGER DEFAULT 1,
            FOREIGN KEY (paciente_id) REFERENCES Pacientes(id),
            FOREIGN KEY (profesional_id) REFERENCES Profesionales(id),
            FOREIGN KEY (farmaco_id) REFERENCES Farmacos(id),
            FOREIGN KEY (snomed_id) REFERENCES SnomedCT(id)
        );
        CREATE INDEX IF NOT EXISTS idx_prescripciones_paciente ON Prescripciones(paciente_id);
        CREATE INDEX IF NOT EXISTS idx_prescripciones_profesional ON Prescripciones(profesional_id);
        CREATE INDEX IF NOT EXISTS idx_prescripciones_farmaco ON Prescripciones(farmaco_id);
        CREATE INDEX IF NOT EXISTS idx_prescripciones_fecha ON Prescripciones(fecha_prescripcion);
    """)
    relaciones = conexion.execute("PRAGMA foreign_key_list(SignosVitales)").fetchall()
    if not any(fila["from"] == "medico_id" and fila["table"] == "Profesionales" for fila in relaciones):
        # No se inventa quién registró una medición histórica sin autor.
        # La FK acepta esos NULL heredados, pero los triggers prohíben nuevas altas sin médico.
        conexion.execute("BEGIN")
        secuencia = conexion.execute("SELECT seq FROM sqlite_sequence WHERE name='SignosVitales'").fetchone()
        conexion.execute("""
            CREATE TABLE SignosVitales_nueva (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                presion_sistolica INTEGER, presion_diastolica INTEGER,
                frecuencia_cardiaca INTEGER, temperatura REAL, saturacion_oxigeno INTEGER,
                motivo_consulta TEXT, medico_id INTEGER,
                FOREIGN KEY (paciente_id) REFERENCES Pacientes(id),
                FOREIGN KEY (medico_id) REFERENCES Profesionales(id)
            )
        """)
        conexion.execute("INSERT INTO SignosVitales_nueva SELECT * FROM SignosVitales")
        conexion.execute("DROP TABLE SignosVitales")
        conexion.execute("ALTER TABLE SignosVitales_nueva RENAME TO SignosVitales")
        if secuencia:
            conexion.execute("UPDATE sqlite_sequence SET seq=MAX(seq,?) WHERE name='SignosVitales'", (secuencia[0],))
        conexion.execute("CREATE INDEX idx_signos_paciente_fecha ON SignosVitales(paciente_id, fecha_hora DESC, id DESC)")
        conexion.commit()
    conexion.executescript("""
        CREATE TRIGGER IF NOT EXISTS signos_medico_requerido
        BEFORE INSERT ON SignosVitales WHEN NEW.medico_id IS NULL
        BEGIN SELECT RAISE(ABORT, 'Seleccione un profesional para registrar signos vitales.'); END;
        CREATE TRIGGER IF NOT EXISTS signos_no_quitar_medico
        BEFORE UPDATE OF medico_id ON SignosVitales
        WHEN NEW.medico_id IS NULL AND OLD.medico_id IS NOT NULL
        BEGIN SELECT RAISE(ABORT, 'No se puede quitar el profesional del registro.'); END;
    """)
