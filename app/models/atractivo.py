from app import db
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class Atractivo(db.Model):
    __tablename__ = 'atractivo'
    id_atractivo = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.String(500))
    latitud = db.Column(db.Numeric(10, 7))
    longitud = db.Column(db.Numeric(10, 7))
    direccion = db.Column(db.String(200))
    horario_apertura = db.Column(db.Time)
    horario_cierre = db.Column(db.Time)
    costo_entrada = db.Column(db.Numeric(10, 2), default=0.0)
    tiempo_visita_estimado = db.Column(db.Integer)  # en minutos
    dias_cerrado = db.Column(db.Text)  # multivalorado, ej. "Lunes,Martes"
    imagen_url = db.Column(db.String(255), nullable=True)

    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True, default=None)

    # Claves foráneas
    id_categoria = db.Column(db.Integer, db.ForeignKey('categoria.id_categoria'), nullable=False)
    id_proveedor = db.Column(db.Integer, db.ForeignKey('proveedor.id_proveedor'), nullable=False)

    # Relación 1:N con ITINERARIO_DETALLE (APARECE EN)
    detalles = db.relationship('ItinerarioDetalle', backref='atractivo', lazy=True)

    @property
    def is_deleted(self):
        """Indica si el atractivo se encuentra eliminado lógicamente"""
        return self.deleted_at is not None

    def __repr__(self):
        status = " (Eliminado)" if self.is_deleted else ""
        return f"<Atractivo #{self.id_atractivo} {self.nombre}{status}>"
