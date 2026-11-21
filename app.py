
import os
from functools import wraps
from secrets import token_hex, compare_digest

import click
from dotenv import load_dotenv
from flask import (
    Flask, abort, flash, redirect, render_template,
    request, session, url_for
)

from models import (
    db, Usuario, Residente, Administrador, PersonalOperativo,
    Vivienda, Ubicacion, Categoria, Incidencia, Evento,
    Comunicacion, NotaInterna, Notificacion, IncidenciaVinculada
)


load_dotenv()


# ==========================================
# CONFIGURACIÓN
# ==========================================

def create_app(test_config=None):
    app = Flask(__name__)

    app.config.update(
        SECRET_KEY=os.getenv(
            "SECRET_KEY", "solo-desarrollo-cambiar"
        ),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL", "sqlite:///boar.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=8 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax"
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    # ======================================
    # AUTENTICACIÓN
    # ======================================

    def usuario_actual():
        usuario_id = session.get("usuario_id")

        if not usuario_id:
            return None

        usuario = db.session.get(Usuario, usuario_id)

        if usuario is None or not usuario.activo:
            session.clear()
            return None

        return usuario

    @app.context_processor
    def variables_globales():
        return {
            "usuario_actual": usuario_actual(),
            "csrf_token": lambda: session.get("csrf_token", "")
        }

    def login_required(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if usuario_actual() is None:
                return redirect(url_for("login"))
            return func(*args, **kwargs)
        return wrapper

    def role_required(*roles):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                usuario = usuario_actual()

                if usuario is None:
                    return redirect(url_for("login"))

                if usuario.rol not in roles:
                    abort(403)

                return func(*args, **kwargs)
            return wrapper
        return decorator

    # ======================================
    # PROTECCIÓN CSRF
    # ======================================

    @app.before_request
    def proteger_formularios():
        if "csrf_token" not in session:
            session["csrf_token"] = token_hex(32)

        if request.method == "POST":
            recibido = request.form.get("csrf_token", "")
            esperado = session.get("csrf_token", "")

            if not recibido or not compare_digest(
                esperado, recibido
            ):
                abort(400, "Token CSRF inválido")

    # ======================================
    # AUTORIZACIÓN POR RECURSO
    # ======================================

    def puede_ver_incidencia(usuario, incidencia):
        if usuario is None:
            return False

        if usuario.rol == "ADMINISTRADOR":
            return True

        if usuario.rol == "RESIDENTE":
            return incidencia.reportante_id == usuario.id

        if usuario.rol == "OPERATIVO":
            return incidencia.responsable_id == usuario.id

        return False

    def obtener_incidencia_autorizada(incidencia_id):
        incidencia = db.get_or_404(
            Incidencia, incidencia_id
        )

        if not puede_ver_incidencia(
            usuario_actual(), incidencia
        ):
            abort(403)

        return incidencia

    # ======================================
    # NOTIFICACIONES AUXILIARES
    # ======================================

    def notificar(usuario_id, incidencia_id, mensaje):
        db.session.add(
            Notificacion(
                usuario_id=usuario_id,
                incidencia_id=incidencia_id,
                mensaje=mensaje
            )
        )

    def notificar_administradores(incidencia_id, mensaje):
        administradores = Usuario.query.filter_by(
            rol="ADMINISTRADOR", activo=True
        ).all()

        for administrador in administradores:
            notificar(
                administrador.id, incidencia_id, mensaje
            )

    # ======================================
    # INICIO
    # ======================================

    @app.route("/")
    def index():
        if usuario_actual() is None:
            return redirect(url_for("login"))
        return redirect(url_for("dashboard"))

    # ======================================
    # LOGIN
    # ======================================

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if usuario_actual() is not None:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            email = request.form.get(
                "email", ""
            ).strip().lower()

            password = request.form.get("password", "")

            usuario = Usuario.query.filter_by(
                email=email, activo=True
            ).first()

            if (
                usuario is None
                or not usuario.check_password(password)
            ):
                flash(
                    "Correo o contraseña incorrectos.",
                    "danger"
                )
                return render_template("login.html")

            session.clear()
            session["usuario_id"] = usuario.id
            session["csrf_token"] = token_hex(32)

            flash(
                "Inicio de sesión correcto.",
                "success"
            )

            return redirect(url_for("dashboard"))

        return render_template("login.html")

    # ======================================
    # LOGOUT
    # ======================================

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        session.clear()
        flash("Sesión cerrada.", "success")
        return redirect(url_for("login"))

    # ======================================
    # DASHBOARD
    # ======================================

    @app.route("/dashboard")
    @login_required
    def dashboard():
        usuario = usuario_actual()
        consulta = Incidencia.query

        if usuario.rol == "RESIDENTE":
            consulta = consulta.filter_by(
                reportante_id=usuario.id
            )

        elif usuario.rol == "OPERATIVO":
            consulta = consulta.filter_by(
                responsable_id=usuario.id
            )

        incidencias = consulta.order_by(
            Incidencia.fecha_hora.desc(),
            Incidencia.id.desc()
        ).all()

        return render_template(
            "dashboard.html",
            incidencias=incidencias
        )

    # ======================================
    # NUEVA INCIDENCIA
    # ======================================

    @app.route(
        "/incidencias/nueva",
        methods=["GET", "POST"]
    )
    @role_required("RESIDENTE")
    def nueva_incidencia():
        usuario = usuario_actual()

        if usuario.vivienda_id is None:
            abort(403)

        ubicaciones = Ubicacion.query.order_by(
            Ubicacion.nombre
        ).all()

        categorias = Categoria.query.order_by(
            Categoria.nombre
        ).all()

        if request.method == "POST":
            descripcion = request.form.get(
                "descripcion", ""
            ).strip()

            ubicacion_id = request.form.get(
                "ubicacion_id", type=int
            )
            categoria_id = request.form.get(
                "categoria_id", type=int
            )

            ubicacion = (
                db.session.get(Ubicacion, ubicacion_id)
                if ubicacion_id else None
            )
            categoria = (
                db.session.get(Categoria, categoria_id)
                if categoria_id else None
            )

            if (
                len(descripcion) < 10
                or len(descripcion) > 2000
                or ubicacion is None
                or categoria is None
            ):
                flash(
                    "Completá correctamente los campos.",
                    "danger"
                )
            else:
                incidencia = Incidencia(
                    reportante_id=usuario.id,
                    ubicacion_id=ubicacion.id,
                    categoria_id=categoria.id,
                    descripcion=descripcion,
                    privada=(
                        request.form.get("privada") == "on"
                    )
                )

                db.session.add(incidencia)
                db.session.flush()

                incidencia.registrar_evento(
                    "REGISTRO",
                    usuario,
                    "Incidencia registrada por residente."
                )

                notificar_administradores(
                    incidencia.id,
                    f"Nueva incidencia #{incidencia.id}"
                )

                db.session.commit()

                flash(
                    "Incidencia registrada correctamente.",
                    "success"
                )

                return redirect(
                    url_for(
                        "ver_incidencia",
                        incidencia_id=incidencia.id
                    )
                )

        return render_template(
            "nueva_incidencia.html",
            ubicaciones=ubicaciones,
            categorias=categorias
        )

    # ======================================
    # DETALLE DE INCIDENCIA
    # ======================================

    @app.route("/incidencias/<int:incidencia_id>")
    @login_required
    def ver_incidencia(incidencia_id):
        incidencia = obtener_incidencia_autorizada(
            incidencia_id
        )

        usuario = usuario_actual()

        eventos = []
        notas = []
        operativos = []

        if usuario.rol in (
            "ADMINISTRADOR", "OPERATIVO"
        ):
            eventos = incidencia.eventos
            notas = incidencia.notas

        if usuario.rol == "ADMINISTRADOR":
            operativos = Usuario.query.filter_by(
                rol="OPERATIVO", activo=True
            ).all()

        return render_template(
            "incidencia_detalle.html",
            incidencia=incidencia,
            eventos=eventos,
            notas=notas,
            comunicaciones=incidencia.comunicaciones,
            operativos=operativos
        )

    # ======================================
    # ACCIONES SOBRE INCIDENCIAS
    # ======================================

    @app.route(
        "/incidencias/<int:incidencia_id>/accion",
        methods=["POST"]
    )
    @login_required
    def accion_incidencia(incidencia_id):
        incidencia = obtener_incidencia_autorizada(
            incidencia_id
        )
        usuario = usuario_actual()
        accion = request.form.get("accion", "")

        try:
            if accion == "iniciar_revision":
                incidencia.iniciar_revision(usuario)

            elif accion == "establecer_prioridad":
                incidencia.establecer_prioridad(
                    usuario,
                    request.form.get("prioridad", "")
                )

            elif accion == "validar":
                incidencia.validar_incidencia(usuario)

                notificar(
                    incidencia.reportante_id,
                    incidencia.id,
                    "Tu incidencia fue validada."
                )

            elif accion == "rechazar":
                incidencia.rechazar_incidencia(
                    usuario,
                    request.form.get("motivo", "")
                )

                notificar(
                    incidencia.reportante_id,
                    incidencia.id,
                    "Tu incidencia fue rechazada."
                )

            elif accion == "asignar":
                operativo_id = request.form.get(
                    "operativo_id", type=int
                )

                operativo = (
                    db.session.get(Usuario, operativo_id)
                    if operativo_id else None
                )

                if operativo is None:
                    raise ValueError(
                        "Trabajador no encontrado."
                    )

                incidencia.asignar_responsable(
                    usuario, operativo
                )

                notificar(
                    operativo.id,
                    incidencia.id,
                    "Tenés una nueva incidencia asignada."
                )

            elif accion == "iniciar_trabajo":
                incidencia.iniciar_trabajo(usuario)

            elif accion == "resolver":
                incidencia.marcar_resuelta(usuario)

                notificar(
                    incidencia.reportante_id,
                    incidencia.id,
                    "Tu incidencia fue marcada como resuelta."
                )

            elif accion == "reabrir":
                incidencia.reabrir_incidencia(usuario)

            elif accion == "cerrar":
                incidencia.cerrar_incidencia(usuario)

                notificar(
                    incidencia.reportante_id,
                    incidencia.id,
                    "Tu incidencia fue cerrada."
                )

            else:
                raise ValueError("Acción desconocida.")

            db.session.commit()

            flash(
                "Operación realizada correctamente.",
                "success"
            )

        except (ValueError, PermissionError, TypeError) as error:
            db.session.rollback()
            flash(str(error), "danger")

        return redirect(
            url_for(
                "ver_incidencia",
                incidencia_id=incidencia.id
            )
        )

    # ======================================
    # COMUNICACIONES
    # ======================================

    @app.route(
        "/incidencias/<int:incidencia_id>/comentar",
        methods=["POST"]
    )
    @login_required
    def comentar_incidencia(incidencia_id):
        incidencia = obtener_incidencia_autorizada(
            incidencia_id
        )
        usuario = usuario_actual()

        mensaje = request.form.get(
            "mensaje", ""
        ).strip()

        if not mensaje or len(mensaje) > 2000:
            flash(
                "El mensaje debe tener entre 1 y 2000 caracteres.",
                "danger"
            )

        elif incidencia.estado in (
            Incidencia.CERRADA,
            Incidencia.RECHAZADA
        ):
            flash(
                "No se puede comentar una incidencia finalizada.",
                "danger"
            )

        else:
            db.session.add(
                Comunicacion(
                    incidencia_id=incidencia.id,
                    autor_id=usuario.id,
                    mensaje=mensaje
                )
            )

            if usuario.rol == "RESIDENTE":
                notificar_administradores(
                    incidencia.id,
                    "Nueva comunicación del residente."
                )

            elif usuario.rol == "ADMINISTRADOR":
                notificar(
                    incidencia.reportante_id,
                    incidencia.id,
                    "Administración agregó un mensaje."
                )

            db.session.commit()
            flash("Mensaje enviado.", "success")

        return redirect(
            url_for(
                "ver_incidencia",
                incidencia_id=incidencia.id
            )
        )

    # ======================================
    # NOTAS INTERNAS
    # ======================================

    @app.route(
        "/incidencias/<int:incidencia_id>/nota",
        methods=["POST"]
    )
    @role_required("ADMINISTRADOR", "OPERATIVO")
    def agregar_nota(incidencia_id):
        incidencia = obtener_incidencia_autorizada(
            incidencia_id
        )

        texto = request.form.get(
            "texto", ""
        ).strip()

        if not texto:
            flash(
                "La nota no puede estar vacía.",
                "danger"
            )
        else:
            db.session.add(
                NotaInterna(
                    incidencia_id=incidencia.id,
                    autor_id=usuario_actual().id,
                    texto=texto
                )
            )

            db.session.commit()
            flash(
                "Nota interna registrada.",
                "success"
            )

        return redirect(
            url_for(
                "ver_incidencia",
                incidencia_id=incidencia.id
            )
        )

    # ======================================
    # VINCULAR INCIDENCIAS DUPLICADAS
    # ======================================

    @app.route(
        "/incidencias/<int:incidencia_id>/vincular",
        methods=["POST"]
    )
    @role_required("ADMINISTRADOR")
    def vincular_incidencia(incidencia_id):
        actual = db.get_or_404(
            Incidencia, incidencia_id
        )

        otra_id = request.form.get(
            "otra_id", type=int
        )

        otra = (
            db.session.get(Incidencia, otra_id)
            if otra_id else None
        )

        if otra is None or otra.id == actual.id:
            flash(
                "Seleccioná otra incidencia válida.",
                "danger"
            )
            return redirect(
                url_for(
                    "ver_incidencia",
                    incidencia_id=actual.id
                )
            )

        principal = min(actual.id, otra.id)
        secundaria = max(actual.id, otra.id)

        existente = db.session.get(
            IncidenciaVinculada,
            (principal, secundaria)
        )

        if existente is None:
            db.session.add(
                IncidenciaVinculada(
                    principal_id=principal,
                    vinculada_id=secundaria
                )
            )
            db.session.commit()

        flash(
            f"Vinculada a la incidencia principal #{principal}.",
            "success"
        )

        return redirect(
            url_for(
                "ver_incidencia",
                incidencia_id=actual.id
            )
        )

    # ======================================
    # NOTIFICACIONES
    # ======================================

    @app.route("/notificaciones")
    @login_required
    def notificaciones():
        usuario = usuario_actual()

        lista = Notificacion.query.filter_by(
            usuario_id=usuario.id
        ).order_by(
            Notificacion.fecha_hora.desc()
        ).all()

        return render_template(
            "notificaciones.html",
            notificaciones=lista
        )

    @app.route(
        "/notificaciones/<int:notificacion_id>/leer",
        methods=["POST"]
    )
    @login_required
    def marcar_notificacion_leida(notificacion_id):
        notificacion = db.get_or_404(
            Notificacion, notificacion_id
        )

        if notificacion.usuario_id != usuario_actual().id:
            abort(403)

        notificacion.leida = True
        db.session.commit()

        return redirect(url_for("notificaciones"))

    # ======================================
    # COMANDOS DE BASE DE DATOS
    # ======================================

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        click.echo("Tablas de BOAR creadas correctamente.")

    @app.cli.command("seed")
    def seed():
        db.create_all()

        if not Vivienda.query.first():
            db.session.add(
                Vivienda(
                    identificacion="Casa 53",
                    sector="Sector A"
                )
            )

        for nombre in (
            "Jardines", "Piscina", "Garaje", "Portal"
        ):
            if not Ubicacion.query.filter_by(
                nombre=nombre
            ).first():
                db.session.add(
                    Ubicacion(nombre=nombre, tipo="COMUN")
                )

        for nombre in (
            "Fontanería", "Electricidad",
            "Limpieza", "Seguridad", "Otros"
        ):
            if not Categoria.query.filter_by(
                nombre=nombre
            ).first():
                db.session.add(Categoria(nombre=nombre))

        db.session.flush()

        usuarios_demo = (
            (Administrador, "admin@boar.local", "Laura"),
            (PersonalOperativo, "operativo@boar.local", "Carlos"),
            (Residente, "residente@boar.local", "Ana")
        )

        for clase, email, nombre in usuarios_demo:
            if Usuario.query.filter_by(email=email).first():
                continue

            usuario = clase(
                nombre=nombre,
                apellido="Demo",
                email=email,
                activo=True
            )

            if isinstance(usuario, Residente):
                usuario.vivienda_id = Vivienda.query.first().id

            usuario.set_password("Demo1234!")
            db.session.add(usuario)

        db.session.commit()

        click.echo(
            "Datos de demostración creados. "
            "Contraseña: Demo1234!"
        )

    # ======================================
    # ERRORES
    # ======================================

    @app.errorhandler(400)
    def error_400(error):
        return f"Error 400: {error.description}", 400

    @app.errorhandler(403)
    def error_403(error):
        return "Error 403: Acceso denegado.", 403

    @app.errorhandler(404)
    def error_404(error):
        return "Error 404: Página no encontrada.", 404

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=False)
