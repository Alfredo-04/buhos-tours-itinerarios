from app import db
from datetime import datetime
# pyrefly: ignore [missing-import]
from werkzeug.security import generate_password_hash, check_password_hash
# pyrefly: ignore [missing-import]
from flask_login import UserMixin

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(80), nullable=False)
    apellidos = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True, index=True)
    contrasenia = db.Column(db.String(255), nullable=False)
    id_rol = db.Column(db.Integer, db.ForeignKey('rol.id_rol'), nullable=False)
    fecha_registro = db.Column(db.Date, nullable=False, default=datetime.utcnow)

    # Relación N:1 con ROL
    rol = db.relationship('Rol', backref='usuarios')

    # Relación 1:N con GENERACION (EJECUTA)
    generaciones = db.relationship('Generacion', backref='usuario', lazy=True)

    def get_id(self):
        """Requerido por Flask-Login para identificar al usuario por su clave primaria"""
        return str(self.id_usuario)

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
        return f"<Usuario {self.email} ({rol_nombre})>"
