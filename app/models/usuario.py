from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(80), nullable=False)
    apellidos = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True, index=True)
    contrasenia = db.Column(db.String(255), nullable=False)
    id_rol = db.Column(db.Integer, db.ForeignKey('rol.id_rol'), nullable=False)
    fecha_registro = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    
    # Eliminación lógica (soft delete)
    deleted_at = db.Column(db.DateTime, nullable=True, default=None)

    # Autenticación de Dos Factores (2FA TOTP)
    two_factor_secret = db.Column(db.String(32), nullable=True)
    two_factor_enabled = db.Column(db.Boolean, nullable=False, default=False)
    two_factor_confirmed_at = db.Column(db.DateTime, nullable=True)

    # Primer login (para agentes creados por admin)
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)
    temp_password_expires_at = db.Column(db.DateTime, nullable=True)

    # Recuperación de contraseña (Self-service)
    reset_token = db.Column(db.String(255), nullable=True, unique=True, index=True)
    reset_token_expires_at = db.Column(db.DateTime, nullable=True)
    reset_token_used = db.Column(db.Boolean, nullable=False, default=False)

    # Relaciones
    rol = db.relationship('Rol', backref='usuarios')
    # Relación 1:1 opcional con TURISTA (vía backref en Turista)
    # Relación 1:N con GENERACION (vía backref en Generacion)

    def get_id(self):
        """Requerido por Flask-Login para identificar al usuario por su clave primaria"""
        return str(self.id_usuario)

    @property
    def is_active(self):
        """Si el usuario fue eliminado lógicamente, Flask-Login no permite iniciar sesión"""
        return self.deleted_at is None

    @property
    def is_deleted(self):
        """Verifica si el usuario se encuentra con soft delete"""
        return self.deleted_at is not None

    @property
    def is_temp_password_expired(self):
        """Verifica si la contraseña temporal ha expirado (más de 24 horas)"""
        if self.temp_password_expires_at:
            return datetime.utcnow() > self.temp_password_expires_at
        return False

    def set_password(self, password):
        """Genera el hash seguro de la contraseña"""
        self.contrasenia = generate_password_hash(password)

    def check_password(self, password):
        """Verifica la contraseña contra el hash almacenado"""
        return check_password_hash(self.contrasenia, password)

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    def __repr__(self):
        rol_nombre = self.rol.nombre if self.rol else self.id_rol
        status = " (Eliminado)" if self.is_deleted else ""
        return f"<Usuario {self.email} ({rol_nombre}){status}>"
