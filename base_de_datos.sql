-- BOAR - Sistema de Registro y Gestion de Incidencias
-- Esquema SQLite basado en models.py del segundo parcial

PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

CREATE TABLE vivienda (
    id INTEGER NOT NULL PRIMARY KEY,
    identificacion VARCHAR(60) NOT NULL UNIQUE,
    sector VARCHAR(100) NOT NULL
);

CREATE TABLE ubicacion (
    id INTEGER NOT NULL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL UNIQUE,
    tipo VARCHAR(60) NOT NULL DEFAULT 'COMUN'
);

CREATE TABLE categoria (
    id INTEGER NOT NULL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE usuario (
    id INTEGER NOT NULL PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL,
    apellido VARCHAR(80) NOT NULL,
    email VARCHAR(180) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(13) NOT NULL CHECK (rol IN ('RESIDENTE', 'ADMINISTRADOR', 'OPERATIVO')),
    activo BOOLEAN NOT NULL DEFAULT 1,
    vivienda_id INTEGER,
    FOREIGN KEY (vivienda_id) REFERENCES vivienda(id)
);

CREATE TABLE incidencia (
    id INTEGER NOT NULL PRIMARY KEY,
    reportante_id INTEGER NOT NULL,
    ubicacion_id INTEGER NOT NULL,
    categoria_id INTEGER NOT NULL,
    responsable_id INTEGER,
    descripcion TEXT NOT NULL,
    fecha_hora DATETIME NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'REGISTRADA',
    prioridad VARCHAR(12),
    privada BOOLEAN NOT NULL DEFAULT 0,
    motivo_rechazo TEXT,
    FOREIGN KEY (reportante_id) REFERENCES usuario(id),
    FOREIGN KEY (ubicacion_id) REFERENCES ubicacion(id),
    FOREIGN KEY (categoria_id) REFERENCES categoria(id),
    FOREIGN KEY (responsable_id) REFERENCES usuario(id)
);

CREATE TABLE evento (
    id INTEGER NOT NULL PRIMARY KEY,
    incidencia_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    accion VARCHAR(80) NOT NULL,
    detalle TEXT,
    fecha_hora DATETIME NOT NULL,
    FOREIGN KEY (incidencia_id) REFERENCES incidencia(id),
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);

CREATE TABLE comunicacion (
    id INTEGER NOT NULL PRIMARY KEY,
    incidencia_id INTEGER NOT NULL,
    autor_id INTEGER NOT NULL,
    mensaje TEXT NOT NULL,
    fecha_hora DATETIME NOT NULL,
    FOREIGN KEY (incidencia_id) REFERENCES incidencia(id),
    FOREIGN KEY (autor_id) REFERENCES usuario(id)
);

CREATE TABLE nota_interna (
    id INTEGER NOT NULL PRIMARY KEY,
    incidencia_id INTEGER NOT NULL,
    autor_id INTEGER NOT NULL,
    texto TEXT NOT NULL,
    fecha_hora DATETIME NOT NULL,
    FOREIGN KEY (incidencia_id) REFERENCES incidencia(id),
    FOREIGN KEY (autor_id) REFERENCES usuario(id)
);

CREATE TABLE fotografia (
    id INTEGER NOT NULL PRIMARY KEY,
    incidencia_id INTEGER NOT NULL,
    ruta_archivo VARCHAR(255) NOT NULL,
    fecha_carga DATETIME NOT NULL,
    FOREIGN KEY (incidencia_id) REFERENCES incidencia(id)
);

CREATE TABLE notificacion (
    id INTEGER NOT NULL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    incidencia_id INTEGER,
    mensaje TEXT NOT NULL,
    leida BOOLEAN NOT NULL DEFAULT 0,
    fecha_hora DATETIME NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id),
    FOREIGN KEY (incidencia_id) REFERENCES incidencia(id)
);

CREATE TABLE incidencia_vinculada (
    principal_id INTEGER NOT NULL,
    vinculada_id INTEGER NOT NULL,
    fecha_vinculacion DATETIME NOT NULL,
    PRIMARY KEY (principal_id, vinculada_id),
    FOREIGN KEY (principal_id) REFERENCES incidencia(id),
    FOREIGN KEY (vinculada_id) REFERENCES incidencia(id)
);

COMMIT;