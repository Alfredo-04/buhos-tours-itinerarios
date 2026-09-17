from app import db
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class Proveedor(db.Model):
    __tablename__ = 'proveedor'
    id_proveedor = db.Column(db.Integer, primary_key=True)
    razon_social = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))
    contacto_nombre = db.Column(db.String(100))
    contacto_telefono = db.Column(db.String(20))
    contacto_email = db.Column(db.String(100))
    tarifa_especial = db.Column(db.Numeric(10, 2))
    observaciones = db.Column(db.Text)

    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True, default=None)

    # Relación 1:N con ATRACTIVO (OFRECE)
    atractivos = db.relationship('Atractivo', backref='proveedor', lazy=True)

    @property
    def is_deleted(self):
        """Indica si el proveedor se encuentra eliminado lógicamente"""
        return self.deleted_at is not None

    def __repr__(self):
        status = " (Eliminado)" if self.is_deleted else ""
        return f"<Proveedor #{self.id_proveedor} {self.razon_social}{status}>"
