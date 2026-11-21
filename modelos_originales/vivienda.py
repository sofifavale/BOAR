
class Vivienda:

    def __init__(self, id_vivienda, numero, sector):

        self.id_vivienda = id_vivienda
        self.numero = numero
        self.sector = sector
        self.residentes = []

    def agregar_residente(self, residente):

        if residente not in self.residentes:
            self.residentes.append(residente)

    def mostrar_residentes(self):

        for residente in self.residentes:
            print(residente.obtener_nombre_completo())
