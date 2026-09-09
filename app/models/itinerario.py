from app import db
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class Itinerario(db.Model):
    __tablename__ = 'itinerario'
    id_itinerario = db.Column(db.Integer, primary_key=True)
    id_generacion = db.Column(db.Integer, db.ForeignKey('generacion.id_generacion'), nullable=False)
    numero_solucion = db.Column(db.Integer, nullable=False)  # índice dentro de la generación
    estado = db.Column(db.String(20), nullable=False, default='Borrador')
    tiempo_total_estimado = db.Column(db.Numeric(10, 2))  # derivado
    codigo_confirmacion = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    voucher_generado = db.Column(db.Boolean, nullable=False, default=False)

    # Relaciones
    detalles = db.relationship('ItinerarioDetalle', backref='itinerario', lazy=True, cascade='all, delete-orphan')
    viajes_turistas = db.relationship('ViajeTurista', backref='itinerario', lazy=True, cascade='all, delete-orphan')
