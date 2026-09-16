import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from app.models.usuario import Usuario
    return Usuario.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    
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
    from app.controllers.usuario_controller import usuario_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(usuario_bp)

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