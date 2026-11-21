
from modelos_originales.usuario import Usuario


class Administrador(Usuario):

    def __init__(self, id_usuario, nombre, apellido,
                 email, password_hash):

        super().__init__(
            id_usuario,
            nombre,
            apellido,
            email,
            password_hash
        )

    def obtener_tipo_usuario(self):
        return "Administrador"
