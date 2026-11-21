


from datetime import datetime

from modelos_originales.administrador import Administrador
from modelos_originales.personal_operativo import PersonalOperativo


class Incidencia:

    # ==========================================
    # ESTADOS DE LA INCIDENCIA
    # ==========================================

    ESTADO_REGISTRADA = "REGISTRADA"
    ESTADO_REVISION = "EN REVISIÓN"
    ESTADO_VALIDADA = "VALIDADA"
    ESTADO_ASIGNADA = "ASIGNADA"
    ESTADO_PROCESO = "EN PROCESO"
    ESTADO_RESUELTA = "RESUELTA"
    ESTADO_CERRADA = "CERRADA"
    ESTADO_RECHAZADA = "RECHAZADA"

    # ==========================================
    # CONSTRUCTOR
    # ==========================================

    def __init__(
        self,
        id_incidencia,
        titulo,
        descripcion,
        categoria,
        ubicacion,
        residente
    ):

        self.id_incidencia = id_incidencia
        self.titulo = titulo
        self.descripcion = descripcion
        self.categoria = categoria
        self.ubicacion = ubicacion
        self.residente = residente

        self.fecha_creacion = datetime.now()

        self.estado = self.ESTADO_REGISTRADA
        self.prioridad = None
        self.responsable = None

        self.motivo_rechazo = None
        self.motivo_reapertura = None

        self.historial = []

        self.registrar_evento(
            "REGISTRO",
            residente,
            "Incidencia registrada por el residente."
        )

    # ==========================================
    # MÉTODOS DE CONSULTA
    # ==========================================

    def obtener_codigo(self):
        return f"INC-{self.id_incidencia:04d}"

    def mostrar_informacion(self):
        return (
            f"Código: {self.obtener_codigo()}\n"
            f"Título: {self.titulo}\n"
            f"Descripción: {self.descripcion}\n"
            f"Categoría: {self.categoria}\n"
            f"Ubicación: {self.ubicacion}\n"
            f"Estado: {self.estado}\n"
            f"Reportada por: "
            f"{self.residente.obtener_nombre_completo()}"
        )

    # ==========================================
    # HISTORIAL DE EVENTOS
    # ==========================================

    def registrar_evento(self, accion, usuario, detalle=""):

        evento = {
            "fecha": datetime.now(),
            "accion": accion,
            "id_usuario": usuario.id_usuario,
            "usuario": usuario.obtener_nombre_completo(),
            "estado": self.estado,
            "detalle": detalle
        }

        self.historial.append(evento)

    def mostrar_historial(self):

        print(
            f"\n===== HISTORIAL DE "
            f"{self.obtener_codigo()} ====="
        )

        for evento in self.historial:

            print("----------------------------")
            print("Fecha:", evento["fecha"])
            print("Acción:", evento["accion"])
            print("Usuario:", evento["usuario"])
            print("Estado:", evento["estado"])
            print("Detalle:", evento["detalle"])

    # ==========================================
    # INICIO DE REVISIÓN
    # ==========================================

    def iniciar_revision(self, administrador):

        if not isinstance(administrador, Administrador):
            raise PermissionError(
                "Solo administración puede revisar incidencias."
            )

        if self.estado != self.ESTADO_REGISTRADA:
            raise ValueError(
                "La incidencia debe estar REGISTRADA."
            )

        self.estado = self.ESTADO_REVISION

        self.registrar_evento(
            "INICIO DE REVISIÓN",
            administrador,
            "Administración inició la revisión."
        )

    # ==========================================
    # VALIDACIÓN ADMINISTRATIVA
    # ==========================================

    def validar_incidencia(self, administrador):

        if not isinstance(administrador, Administrador):
            raise PermissionError(
                "Solo administración puede validar incidencias."
            )

        if self.estado != self.ESTADO_REVISION:
            raise ValueError(
                "La incidencia debe estar EN REVISIÓN."
            )

        self.estado = self.ESTADO_VALIDADA

        self.registrar_evento(
            "VALIDACIÓN",
            administrador,
            "Incidencia aprobada por administración."
        )

    # ==========================================
    # RECHAZO ADMINISTRATIVO
    # ==========================================

    def rechazar_incidencia(self, administrador, motivo):

        if not isinstance(administrador, Administrador):
            raise PermissionError(
                "Solo administración puede rechazar incidencias."
            )

        if self.estado != self.ESTADO_REVISION:
            raise ValueError(
                "Solo se pueden rechazar incidencias EN REVISIÓN."
            )

        if not isinstance(motivo, str) or not motivo.strip():
            raise ValueError(
                "Debe indicar el motivo del rechazo."
            )

        self.motivo_rechazo = motivo.strip()
        self.estado = self.ESTADO_RECHAZADA

        self.registrar_evento(
            "RECHAZO",
            administrador,
            self.motivo_rechazo
        )

    # ==========================================
    # ESTABLECER PRIORIDAD
    # ==========================================

    def establecer_prioridad(self, administrador, prioridad):

        if not isinstance(administrador, Administrador):
            raise PermissionError(
                "Solo administración puede establecer prioridades."
            )

        if self.estado != self.ESTADO_VALIDADA:
            raise ValueError(
                "La incidencia debe estar VALIDADA."
            )

        prioridades_validas = (
            "BAJA",
            "MEDIA",
            "ALTA",
            "URGENTE"
        )

        if prioridad not in prioridades_validas:
            raise ValueError(
                "Prioridad no válida."
            )

        self.prioridad = prioridad

        self.registrar_evento(
            "PRIORIDAD",
            administrador,
            f"Prioridad establecida: {prioridad}"
        )

    # ==========================================
    # ASIGNACIÓN DE RESPONSABLE
    # ==========================================

    def asignar_responsable(self, administrador, operativo):

        if not isinstance(administrador, Administrador):
            raise PermissionError(
                "Solo administración puede asignar responsables."
            )

        if not isinstance(operativo, PersonalOperativo):
            raise TypeError(
                "El responsable debe ser personal operativo."
            )

        if self.estado != self.ESTADO_VALIDADA:
            raise ValueError(
                "La incidencia debe estar VALIDADA antes de asignarse."
            )

        if self.prioridad is None:
            raise ValueError(
                "Primero debe establecerse la prioridad."
            )

        self.responsable = operativo
        self.estado = self.ESTADO_ASIGNADA

        self.registrar_evento(
            "ASIGNACIÓN",
            administrador,
            f"Responsable asignado: "
            f"{operativo.obtener_nombre_completo()}"
        )

    # ==========================================
    # INICIO DEL TRABAJO
    # ==========================================

    def iniciar_trabajo(self, operativo):

        if not isinstance(operativo, PersonalOperativo):
            raise PermissionError(
                "Solo personal operativo puede iniciar trabajos."
            )

        if self.responsable is not operativo:
            raise PermissionError(
                "La incidencia no está asignada a este trabajador."
            )

        if self.estado != self.ESTADO_ASIGNADA:
            raise ValueError(
                "La incidencia debe estar ASIGNADA."
            )

        self.estado = self.ESTADO_PROCESO

        self.registrar_evento(
            "INICIO DE TRABAJO",
            operativo,
            "El personal operativo inició el trabajo."
        )

    # ==========================================
    # RESOLUCIÓN
    # ==========================================

    def marcar_resuelta(self, operativo):

        if not isinstance(operativo, PersonalOperativo):
            raise PermissionError(
                "Solo personal operativo puede marcarla resuelta."
            )

        if self.responsable is not operativo:
            raise PermissionError(
                "La incidencia no está asignada a este trabajador."
            )

        if self.estado != self.ESTADO_PROCESO:
            raise ValueError(
                "La incidencia debe estar EN PROCESO."
            )

        self.estado = self.ESTADO_RESUELTA

        self.registrar_evento(
            "RESOLUCIÓN",
            operativo,
            "El trabajador informó que terminó la intervención."
        )

    # ==========================================
    # REAPERTURA ADMINISTRATIVA
    # ==========================================

    def reabrir_incidencia(self, administrador, motivo):

        if not isinstance(administrador, Administrador):
            raise PermissionError(
                "Solo administración puede reabrir incidencias."
            )

        if self.estado != self.ESTADO_RESUELTA:
            raise ValueError(
                "Solo se puede reabrir una incidencia RESUELTA."
            )

        if not isinstance(motivo, str) or not motivo.strip():
            raise ValueError(
                "Debe indicar el motivo de la reapertura."
            )

        if self.responsable is None:
            raise ValueError(
                "La incidencia no tiene responsable asignado."
            )

        self.motivo_reapertura = motivo.strip()
        self.estado = self.ESTADO_PROCESO

        self.registrar_evento(
            "REAPERTURA",
            administrador,
            self.motivo_reapertura
        )

    # ==========================================
    # CIERRE ADMINISTRATIVO
    # ==========================================

    def cerrar_incidencia(self, administrador, verificada):

        if not isinstance(administrador, Administrador):
            raise PermissionError(
                "Solo administración puede cerrar incidencias."
            )

        if self.estado != self.ESTADO_RESUELTA:
            raise ValueError(
                "Solo se puede cerrar una incidencia RESUELTA."
            )

        if verificada is not True:
            raise ValueError(
                "Administración debe verificar la resolución."
            )

        self.estado = self.ESTADO_CERRADA

        self.registrar_evento(
            "CIERRE",
            administrador,
            "Resolución verificada y cierre administrativo."
        )
