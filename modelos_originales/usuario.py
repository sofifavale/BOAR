
class Usuario:

    def __init__(self, id_usuario, nombre, apellido,
                 email, password_hash):

        self.id_usuario = id_usuario
        self.nombre = nombre
        self.apellido = apellido
        self.email = email
        self.password_hash = password_hash
        self.activo = True

    def obtener_nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def obtener_id(self):
        return self.id_usuario

    def obtener_tipo_usuario(self):
        return "Usuario"
