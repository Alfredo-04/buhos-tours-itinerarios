import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

@login_manager.user_loader
def load_user(user_id):
    from app.models.usuario import Usuario
    return db.session.get(Usuario, int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    # Configurar LoginManager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'

    # Importar modelos para registro con SQLAlchemy y migraciones
    from app.models import (
        proveedor, categoria, transporte, rol, usuario, 
        turista, atractivo, generacion, itinerario, 
        itinerario_detalle, viaje_turista
    )

    # Registrar blueprints
    from app.controllers.auth_controller import auth_bp
    from app.controllers.admin_controller import admin_bp
    from app.controllers.agente_controller import agente_bp
    from app.controllers.turista_controller import turista_bp
    from app.controllers.usuario_controller import usuario_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(agente_bp)
    app.register_blueprint(turista_bp)
    app.register_blueprint(usuario_bp)

    # Middleware de seguridad global
    @app.before_request
    def enforce_security_policies():
        from flask_login import current_user
        from flask import request, redirect, url_for, flash

        if current_user.is_authenticated:
            # 1. Forzar cambio de contraseña si está pendiente
            if getattr(current_user, 'must_change_password', False):
                exempt_endpoints = {'auth.cambiar_password_obligatorio', 'auth.logout', 'static'}
                if request.endpoint and request.endpoint not in exempt_endpoints:
                    flash('Debes cambiar tu contraseña temporal antes de continuar navegando.', 'warning')
                    return redirect(url_for('auth.cambiar_password_obligatorio'))

            # 2. Forzar configuración de 2FA para Agentes y Administradores
            if current_user.rol and current_user.rol.nombre in ['admin', 'agente'] and not current_user.two_factor_enabled:
                exempt_endpoints = {
                    'auth.configurar_2fa',
                    'auth.logout',
                    'auth.cambiar_password_obligatorio',
                    'static'
                }
                if request.endpoint and request.endpoint not in exempt_endpoints:
                    flash('Como agente o administrador, debes configurar la autenticación de dos factores (2FA) para continuar.', 'warning')
                    return redirect(url_for('auth.configurar_2fa'))

    # Comando CLI para ejecutar Seeder de Roles
    @app.cli.command("seed-roles")
    def seed_roles_command():
        """Ejecuta el seeder para poblar roles básicos."""
        from app.seeds.rol_seeder import seed_roles
        seed_roles()
        click.echo("Seeder de roles ejecutado con éxito.")

    # Comando CLI para ejecutar Seeders de Usuarios
    @app.cli.command("seed-users")
    def seed_users_command():
        """Ejecuta el seeder para poblar usuarios iniciales."""
        from app.seeds.user_seeder import seed_usuarios
        seed_usuarios()
        click.echo("Seeder de usuarios ejecutado con éxito.")

    return app