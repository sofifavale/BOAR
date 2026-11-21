
from modelos_originales.usuario import Usuario


class Residente(Usuario):

    def __init__(self, id_usuario, nombre, apellido,
                 email, password_hash, vivienda):

        super().__init__(
            id_usuario,
            nombre,
            apellido,
            email,
            password_hash
        )

        self.vivienda = vivienda

        if vivienda is not None:
            vivienda.agregar_residente(self)

    def obtener_tipo_usuario(self):
        return "Residente"

    def mostrar_informacion(self):

        numero_vivienda = (
            self.vivienda.numero
            if self.vivienda is not None
            else "Sin vivienda asignada"
        )

        return (
            f"Nombre: {self.obtener_nombre_completo()}\n"
            f"Tipo: {self.obtener_tipo_usuario()}\n"
            f"Vivienda: {numero_vivienda}"
        )
