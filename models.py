
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ==========================================
# USUARIOS Y HERENCIA
# ==========================================

class Usuario(db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    apellido = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(180), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(
        db.Enum("RESIDENTE", "ADMINISTRADOR", "OPERATIVO"),
        nullable=False
    )
    activo = db.Column(db.Boolean, nullable=False, default=True)
    vivienda_id = db.Column(
        db.Integer, db.ForeignKey("vivienda.id"), nullable=True
    )

    vivienda = db.relationship("Vivienda", back_populates="residentes")

    __mapper_args__ = {"polymorphic_on": rol}

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def obtener_tipo_usuario(self):
        return self.rol

    def obtener_nombre_completo(self):
        return f"{self.nombre} {self.apellido}"


class Residente(Usuario):
    __mapper_args__ = {"polymorphic_identity": "RESIDENTE"}


class Administrador(Usuario):
    __mapper_args__ = {"polymorphic_identity": "ADMINISTRADOR"}


class PersonalOperativo(Usuario):
    __mapper_args__ = {"polymorphic_identity": "OPERATIVO"}


# ==========================================
# VIVIENDAS, UBICACIONES Y CATEGORÍAS
# ==========================================

class Vivienda(db.Model):
    __tablename__ = "vivienda"

    id = db.Column(db.Integer, primary_key=True)
    identificacion = db.Column(db.String(60), nullable=False, unique=True)
    sector = db.Column(db.String(100), nullable=False)

    residentes = db.relationship("Usuario", back_populates="vivienda")


class Ubicacion(db.Model):
    __tablename__ = "ubicacion"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True)
    tipo = db.Column(db.String(60), nullable=False, default="COMUN")


class Categoria(db.Model):
    __tablename__ = "categoria"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)


# ==========================================
# VALIDACIONES DE NEGOCIO
# ==========================================

def require_role(usuario, rol):
    if not usuario or not usuario.activo or usuario.rol != rol:
        raise PermissionError(
            f"Solo {rol} puede realizar esta operación"
        )


def require_state(incidencia, estado):
    if incidencia.estado != estado:
        raise ValueError(
            f"La incidencia debe estar {estado}"
        )


# ==========================================
# INCIDENCIA
# ==========================================

class Incidencia(db.Model):
    __tablename__ = "incidencia"

    REGISTRADA = "REGISTRADA"
    REVISION = "EN REVISIÓN"
    VALIDADA = "VALIDADA"
    ASIGNADA = "ASIGNADA"
    PROCESO = "EN PROCESO"
    RESUELTA = "RESUELTA"
    CERRADA = "CERRADA"
    RECHAZADA = "RECHAZADA"

    id = db.Column(db.Integer, primary_key=True)

    reportante_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id"), nullable=False
    )
    ubicacion_id = db.Column(
        db.Integer, db.ForeignKey("ubicacion.id"), nullable=False
    )
    categoria_id = db.Column(
        db.Integer, db.ForeignKey("categoria.id"), nullable=False
    )
    responsable_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id"), nullable=True
    )

    descripcion = db.Column(db.Text, nullable=False)
    fecha_hora = db.Column(db.DateTime, default=now, nullable=False)
    estado = db.Column(
        db.String(30), default=REGISTRADA, nullable=False
    )
    prioridad = db.Column(db.String(12))
    privada = db.Column(db.Boolean, default=False, nullable=False)
    motivo_rechazo = db.Column(db.Text)

    reportante = db.relationship(
        "Usuario", foreign_keys=[reportante_id]
    )
    responsable = db.relationship(
        "Usuario", foreign_keys=[responsable_id]
    )
    ubicacion = db.relationship("Ubicacion")
    categoria = db.relationship("Categoria")

    eventos = db.relationship(
        "Evento",
        back_populates="incidencia",
        cascade="all, delete-orphan",
        order_by="Evento.id"
    )
    comunicaciones = db.relationship(
        "Comunicacion",
        back_populates="incidencia",
        cascade="all, delete-orphan",
        order_by="Comunicacion.id"
    )
    notas = db.relationship(
        "NotaInterna",
        back_populates="incidencia",
        cascade="all, delete-orphan",
        order_by="NotaInterna.id"
    )
    fotos = db.relationship(
        "Fotografia",
        back_populates="incidencia",
        cascade="all, delete-orphan"
    )

    def registrar_evento(self, accion, usuario, detalle=""):
        db.session.add(
            Evento(
                incidencia=self,
                accion=accion,
                usuario_id=usuario.id,
                detalle=detalle
            )
        )

    def iniciar_revision(self, administrador):
        require_role(administrador, "ADMINISTRADOR")
        require_state(self, self.REGISTRADA)

        self.estado = self.REVISION
        self.registrar_evento("INICIO REVISIÓN", administrador)

    def establecer_prioridad(self, administrador, prioridad):
        require_role(administrador, "ADMINISTRADOR")

        if self.estado not in (self.REVISION, self.VALIDADA):
            raise ValueError(
                "La incidencia debe estar EN REVISIÓN o VALIDADA"
            )

        if prioridad not in ("BAJA", "MEDIA", "ALTA", "URGENTE"):
            raise ValueError("Prioridad no válida")

        self.prioridad = prioridad
        self.registrar_evento("PRIORIDAD", administrador, prioridad)

    def validar_incidencia(self, administrador):
        require_role(administrador, "ADMINISTRADOR")
        require_state(self, self.REVISION)

        self.estado = self.VALIDADA
        self.registrar_evento("VALIDACIÓN", administrador)

    def rechazar_incidencia(self, administrador, motivo):
        require_role(administrador, "ADMINISTRADOR")
        require_state(self, self.REVISION)

        if not motivo or not motivo.strip():
            raise ValueError("Motivo obligatorio")

        self.motivo_rechazo = motivo.strip()
        self.estado = self.RECHAZADA
        self.registrar_evento(
            "RECHAZO", administrador, self.motivo_rechazo
        )

    def asignar_responsable(self, administrador, operativo):
        require_role(administrador, "ADMINISTRADOR")
        require_role(operativo, "OPERATIVO")
        require_state(self, self.VALIDADA)

        if self.prioridad is None:
            raise ValueError(
                "Primero debe establecerse la prioridad"
            )

        self.responsable = operativo
        self.estado = self.ASIGNADA
        self.registrar_evento(
            "ASIGNACIÓN",
            administrador,
            operativo.obtener_nombre_completo()
        )

    def _verificar_responsable(self, operativo):
        require_role(operativo, "OPERATIVO")

        if self.responsable_id != operativo.id:
            raise PermissionError(
                "No es el responsable asignado"
            )

    def iniciar_trabajo(self, operativo):
        self._verificar_responsable(operativo)
        require_state(self, self.ASIGNADA)

        self.estado = self.PROCESO
        self.registrar_evento("INICIO TRABAJO", operativo)

    def marcar_resuelta(self, operativo):
        self._verificar_responsable(operativo)
        require_state(self, self.PROCESO)

        self.estado = self.RESUELTA
        self.registrar_evento("RESOLUCIÓN", operativo)

    def reabrir_incidencia(self, administrador):
        require_role(administrador, "ADMINISTRADOR")
        require_state(self, self.RESUELTA)

        self.estado = self.PROCESO
        self.registrar_evento("REAPERTURA", administrador)

    def cerrar_incidencia(self, administrador):
        require_role(administrador, "ADMINISTRADOR")
        require_state(self, self.RESUELTA)

        self.estado = self.CERRADA
        self.registrar_evento("CIERRE", administrador)


# ==========================================
# HISTORIAL
# ==========================================

class Evento(db.Model):
    __tablename__ = "evento"

    id = db.Column(db.Integer, primary_key=True)
    incidencia_id = db.Column(
        db.Integer, db.ForeignKey("incidencia.id"), nullable=False
    )
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id"), nullable=False
    )
    accion = db.Column(db.String(80), nullable=False)
    detalle = db.Column(db.Text, default="")
    fecha_hora = db.Column(db.DateTime, default=now, nullable=False)

    incidencia = db.relationship(
        "Incidencia", back_populates="eventos"
    )
    usuario = db.relationship("Usuario")


# ==========================================
# COMUNICACIONES
# ==========================================

class Comunicacion(db.Model):
    __tablename__ = "comunicacion"

    id = db.Column(db.Integer, primary_key=True)
    incidencia_id = db.Column(
        db.Integer, db.ForeignKey("incidencia.id"), nullable=False
    )
    autor_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id"), nullable=False
    )
    mensaje = db.Column(db.Text, nullable=False)
    fecha_hora = db.Column(db.DateTime, default=now, nullable=False)

    incidencia = db.relationship(
        "Incidencia", back_populates="comunicaciones"
    )
    autor = db.relationship("Usuario")


# ==========================================
# NOTAS INTERNAS
# ==========================================

class NotaInterna(db.Model):
    __tablename__ = "nota_interna"

    id = db.Column(db.Integer, primary_key=True)
    incidencia_id = db.Column(
        db.Integer, db.ForeignKey("incidencia.id"), nullable=False
    )
    autor_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id"), nullable=False
    )
    texto = db.Column(db.Text, nullable=False)
    fecha_hora = db.Column(db.DateTime, default=now, nullable=False)

    incidencia = db.relationship(
        "Incidencia", back_populates="notas"
    )


# ==========================================
# FOTOGRAFÍAS
# ==========================================

class Fotografia(db.Model):
    __tablename__ = "fotografia"

    id = db.Column(db.Integer, primary_key=True)
    incidencia_id = db.Column(
        db.Integer, db.ForeignKey("incidencia.id"), nullable=False
    )
    ruta_archivo = db.Column(db.String(255), nullable=False)
    fecha_carga = db.Column(db.DateTime, default=now, nullable=False)

    incidencia = db.relationship(
        "Incidencia", back_populates="fotos"
    )


# ==========================================
# NOTIFICACIONES
# ==========================================

class Notificacion(db.Model):
    __tablename__ = "notificacion"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id"), nullable=False
    )
    incidencia_id = db.Column(
        db.Integer, db.ForeignKey("incidencia.id")
    )
    mensaje = db.Column(db.Text, nullable=False)
    leida = db.Column(db.Boolean, default=False, nullable=False)
    fecha_hora = db.Column(db.DateTime, default=now, nullable=False)


# ==========================================
# INCIDENCIAS DUPLICADAS
# ==========================================

class IncidenciaVinculada(db.Model):
    __tablename__ = "incidencia_vinculada"

    principal_id = db.Column(
        db.Integer,
        db.ForeignKey("incidencia.id"),
        primary_key=True
    )
    vinculada_id = db.Column(
        db.Integer,
        db.ForeignKey("incidencia.id"),
        primary_key=True
    )
    fecha_vinculacion = db.Column(
        db.DateTime, default=now, nullable=False
    )
