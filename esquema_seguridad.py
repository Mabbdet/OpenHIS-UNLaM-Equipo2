"""Migración repetible de HU-07; no asigna autores a los datos históricos."""

TABLAS_AUDITADAS = ("Pacientes", "Profesionales", "SignosVitales", "Prescripciones",
                    "Especialidades", "SnomedCT", "Farmacos", "Usuarios")


def ampliar_seguridad(conexion):
    conexion.executescript("""
        CREATE TABLE IF NOT EXISTS Usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, nombre_completo TEXT NOT NULL, email TEXT,
            rol TEXT NOT NULL CHECK(rol IN ('admin','medico','enfermero','administrativo')),
            activo INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0,1)),
            ultimo_acceso TIMESTAMP, fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS Auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL,
            usuario_nombre TEXT, tabla_afectada TEXT NOT NULL, registro_id INTEGER,
            tipo_accion TEXT NOT NULL CHECK(tipo_accion IN ('A','M','B','R','L','X','E','I','C','Q')),
            descripcion TEXT, datos_anteriores TEXT, datos_nuevos TEXT,
            fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            origen_sistema TEXT, origen_id_externo TEXT, payload_referencia TEXT,
            FOREIGN KEY(usuario_id) REFERENCES Usuarios(id)
        );
        CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON Usuarios(rol);
        CREATE INDEX IF NOT EXISTS idx_usuarios_activo ON Usuarios(activo);
        CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON Auditoria(usuario_id);
        CREATE INDEX IF NOT EXISTS idx_auditoria_tabla ON Auditoria(tabla_afectada);
        CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON Auditoria(fecha_hora);
        CREATE INDEX IF NOT EXISTS idx_auditoria_tipo ON Auditoria(tipo_accion);
        CREATE INDEX IF NOT EXISTS idx_auditoria_registro ON Auditoria(tabla_afectada,registro_id);
        CREATE INDEX IF NOT EXISTS idx_auditoria_origen ON Auditoria(origen_sistema);
        CREATE INDEX IF NOT EXISTS idx_auditoria_externo ON Auditoria(origen_id_externo);
    """)
    for tabla in TABLAS_AUDITADAS:
        campos = {r["name"] for r in conexion.execute(f"PRAGMA table_info({tabla})")}
        if "usuario_alta_id" not in campos:
            conexion.execute(f"ALTER TABLE {tabla} ADD COLUMN usuario_alta_id INTEGER REFERENCES Usuarios(id)")
    campos = {r["name"] for r in conexion.execute("PRAGMA table_info(Usuarios)")}
    if "version_sesion" not in campos:
        conexion.execute("ALTER TABLE Usuarios ADD COLUMN version_sesion INTEGER NOT NULL DEFAULT 0")
