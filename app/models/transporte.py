from app import db
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class Transporte(db.Model):
    __tablename__ = 'transporte'
    id_transporte = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'Privado' o 'Público'
    capacidad = db.Column(db.Integer)
    horario_inicio = db.Column(db.Time)
    horario_fin = db.Column(db.Time)
    costo_por_tramo = db.Column(db.Numeric(10, 2), default=0.0)
    tipo_costo = db.Column(db.String(20), nullable=False)  # 'por_persona' o 'por_vehiculo'
    velocidad_promedio_kmh = db.Column(db.Numeric(5, 2), nullable=False, default=30.0)  # en km/h (ej. 5.0, 20.0, 30.0, 40.0)

    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True, default=None)

    # Relación 1:N con ITINERARIO_DETALLE (USADO EN)
    detalles = db.relationship('ItinerarioDetalle', backref='transporte', lazy=True)

    @property
    def is_deleted(self):
        """Indica si el transporte se encuentra eliminado lógicamente"""
        return self.deleted_at is not None

    def __repr__(self):
        status = " (Eliminado)" if self.is_deleted else ""
        return f"<Transporte #{self.id_transporte} {self.nombre} ({self.tipo}){status}>"
