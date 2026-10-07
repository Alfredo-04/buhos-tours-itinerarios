from datetime import datetime
from app import db

class Proveedor(db.Model):
    __tablename__ = 'proveedor'

    id_proveedor = db.Column(db.Integer, primary_key=True)
    razon_social = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=True)
    contacto_nombre = db.Column(db.String(100), nullable=True)
    contacto_telefono = db.Column(db.String(20), nullable=True)
    contacto_email = db.Column(db.String(100), nullable=True)
    tarifa_especial = db.Column(db.Numeric(10, 2), nullable=True)
    observaciones = db.Column(db.Text, nullable=True)

    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True, default=None)

    @property
    def is_deleted(self):
        """Indica si el proveedor se encuentra eliminado lógicamente"""
        return self.deleted_at is not None

    def __repr__(self):
        status = " (Eliminado)" if self.is_deleted else ""
        return f"<Proveedor #{self.id_proveedor} {self.razon_social}{status}>"
