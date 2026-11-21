

from modelos_originales.residente import Residente
from modelos_originales.vivienda import Vivienda
from modelos_originales.incidencia import Incidencia
from modelos_originales.administrador import Administrador
from modelos_originales.personal_operativo import PersonalOperativo


# ==================================
# CREACIÓN DE VIVIENDA
# ==================================

vivienda1 = Vivienda(
    1,
    "25",
    "Sector B"
)


# ==================================
# CREACIÓN DE RESIDENTES
# ==================================

residente1 = Residente(
    1,
    "Ana",
    "García",
    "ana@boar.com",
    "hash_de_ejemplo",
    vivienda1
)

residente2 = Residente(
    2,
    "Pedro",
    "López",
    "pedro@boar.com",
    "hash_de_ejemplo",
    vivienda1
)


# ==================================
# CREACIÓN DE ADMINISTRADOR
# ==================================

administrador1 = Administrador(
    3,
    "Laura",
    "Martínez",
    "laura@boar.com",
    "hash_de_ejemplo"
)


# ==================================
# CREACIÓN DE PERSONAL OPERATIVO
# ==================================

operativo1 = PersonalOperativo(
    4,
    "Carlos",
    "Ruiz",
    "carlos@boar.com",
    "hash_de_ejemplo"
)


# ==================================
# CREACIÓN DE INCIDENCIA
# ==================================

incidencia1 = Incidencia(
    1,
    "Farola averiada",
    "La farola junto a la piscina no funciona.",
    "Mantenimiento",
    "Sector B - Piscina",
    residente1
)


# ==================================
# PRUEBAS GENERALES DEL SISTEMA
# ==================================

print("===== SISTEMA BOAR =====")

print("\n--- VIVIENDA ---")
print("Número:", vivienda1.numero)
print("Sector:", vivienda1.sector)

print("\n--- RESIDENTES ---")
vivienda1.mostrar_residentes()

print("\n--- HERENCIA ---")
print("Nombre:", residente1.obtener_nombre_completo())
print("Tipo:", residente1.obtener_tipo_usuario())

print("\n--- INCIDENCIA ---")
print(incidencia1.mostrar_informacion())

print("\nFecha de creación:")
print(incidencia1.fecha_creacion)


# ==================================
# PRUEBA DE POLIMORFISMO
# ==================================

usuarios = [
    residente1,
    administrador1,
    operativo1
]

print("\n===== TIPOS DE USUARIO =====")

for usuario in usuarios:
    print(
        usuario.obtener_nombre_completo(),
        "-",
        usuario.obtener_tipo_usuario()
    )


# ==================================
# CICLO DE VIDA DE LA INCIDENCIA
# ==================================

print("\n===== CICLO DE INCIDENCIA =====")

print("Estado inicial:", incidencia1.estado)

# Administración inicia la revisión.
incidencia1.iniciar_revision(administrador1)

print("Después de revisión:", incidencia1.estado)

# Administración valida la incidencia.
incidencia1.validar_incidencia(administrador1)

print("Después de validación:", incidencia1.estado)

# Administración establece la prioridad.
incidencia1.establecer_prioridad(
    administrador1,
    "ALTA"
)

print("Prioridad:", incidencia1.prioridad)

# Administración asigna un responsable.
incidencia1.asignar_responsable(
    administrador1,
    operativo1
)

print("Después de asignación:", incidencia1.estado)

# El trabajador comienza la intervención.
incidencia1.iniciar_trabajo(operativo1)

print("Trabajo iniciado:", incidencia1.estado)

# El trabajador informa que terminó.
incidencia1.marcar_resuelta(operativo1)

print("Trabajo terminado:", incidencia1.estado)


# ==================================
# REAPERTURA ADMINISTRATIVA
# ==================================

print("\n===== REAPERTURA =====")

incidencia1.reabrir_incidencia(
    administrador1,
    "La farola sigue sin funcionar correctamente."
)

print("Estado:", incidencia1.estado)
print("Motivo:", incidencia1.motivo_reapertura)


# ==================================
# SEGUNDA INTERVENCIÓN
# ==================================

print("\n===== SEGUNDA INTERVENCIÓN =====")

incidencia1.marcar_resuelta(operativo1)

print("Estado:", incidencia1.estado)


# ==================================
# CIERRE DEFINITIVO
# ==================================

print("\n===== CIERRE DEFINITIVO =====")

incidencia1.cerrar_incidencia(
    administrador1,
    True
)

print("Estado final:", incidencia1.estado)


# ==================================
# PRUEBA DE CIERRE NO AUTORIZADO
# ==================================

print("\n===== CIERRE NO AUTORIZADO =====")

try:
    incidencia1.cerrar_incidencia(
        residente1,
        True
    )

except PermissionError as error:
    print("Acceso denegado:", error)


# ==================================
# CREACIÓN DE SEGUNDA INCIDENCIA
# ==================================

print("\n===== PRUEBA DE RECHAZO =====")

incidencia2 = Incidencia(
    2,
    "Problema con televisión",
    "Mi televisión dejó de funcionar.",
    "Otros",
    "Vivienda 25",
    residente1
)

print("Estado inicial:", incidencia2.estado)

# Administración comienza la revisión.
incidencia2.iniciar_revision(administrador1)

print("En revisión:", incidencia2.estado)

# Administración rechaza la incidencia.
incidencia2.rechazar_incidencia(
    administrador1,
    "Es una avería privada ajena al mantenimiento comunitario."
)

print("Estado final:", incidencia2.estado)
print("Motivo:", incidencia2.motivo_rechazo)


# ==================================
# HISTORIAL DE LA PRIMERA INCIDENCIA
# ==================================

print("\n===== CONSULTA DE HISTORIAL =====")

incidencia1.mostrar_historial()


# ==================================
# HISTORIAL DE LA SEGUNDA INCIDENCIA
# ==================================

incidencia2.mostrar_historial()


# ==================================
# RESUMEN FINAL
# ==================================

print("\n===== RESUMEN FINAL DE BOAR =====")

print(
    incidencia1.obtener_codigo(),
    "-",
    incidencia1.estado
)

print(
    incidencia2.obtener_codigo(),
    "-",
    incidencia2.estado
)

print("\nPruebas finalizadas correctamente.")
