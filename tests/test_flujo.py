
import unittest

from app import create_app
from modelos_originales import (
    db, Residente, Administrador, PersonalOperativo,
    Vivienda, Categoria, Ubicacion, Incidencia
)


class TestFlujoBOAR(unittest.TestCase):

    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "clave-exclusiva-pruebas"
        })

        self.contexto = self.app.app_context()
        self.contexto.push()

        db.create_all()

        vivienda = Vivienda(
            identificacion="Casa 53",
            sector="A"
        )

        categoria = Categoria(nombre="Electricidad")

        ubicacion = Ubicacion(
            nombre="Jardines",
            tipo="COMUN"
        )

        self.admin = Administrador(
            nombre="Laura",
            apellido="Demo",
            email="admin@test.com"
        )
        self.admin.set_password("test123")

        self.operario = PersonalOperativo(
            nombre="Carlos",
            apellido="Demo",
            email="operario@test.com"
        )
        self.operario.set_password("test123")

        self.residente = Residente(
            nombre="Ana",
            apellido="Demo",
            email="residente@test.com",
            vivienda=vivienda
        )
        self.residente.set_password("test123")

        db.session.add_all([
            vivienda,
            categoria,
            ubicacion,
            self.admin,
            self.operario,
            self.residente
        ])
        db.session.flush()

        self.incidencia = Incidencia(
            reportante=self.residente,
            ubicacion=ubicacion,
            categoria=categoria,
            descripcion="Luminaria rota en jardines"
        )

        db.session.add(self.incidencia)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.contexto.pop()

    def test_flujo_completo(self):
        i = self.incidencia

        i.iniciar_revision(self.admin)
        i.establecer_prioridad(self.admin, "ALTA")
        i.validar_incidencia(self.admin)
        i.asignar_responsable(self.admin, self.operario)

        db.session.flush()

        i.iniciar_trabajo(self.operario)
        i.marcar_resuelta(self.operario)
        i.cerrar_incidencia(self.admin)

        self.assertEqual(i.estado, "CERRADA")

    def test_no_asignar_sin_prioridad(self):
        i = self.incidencia

        i.iniciar_revision(self.admin)
        i.validar_incidencia(self.admin)

        with self.assertRaises(ValueError):
            i.asignar_responsable(
                self.admin, self.operario
            )

    def test_residente_no_puede_validar(self):
        self.incidencia.iniciar_revision(self.admin)

        with self.assertRaises(PermissionError):
            self.incidencia.validar_incidencia(
                self.residente
            )

    def test_operario_no_puede_revisar(self):
        with self.assertRaises(PermissionError):
            self.incidencia.iniciar_revision(
                self.operario
            )

    def test_estado_inicial(self):
        self.assertEqual(
            self.incidencia.estado,
            "REGISTRADA"
        )


if __name__ == "__main__":
    unittest.main()
