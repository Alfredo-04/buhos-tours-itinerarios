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
    costo_por_tramo = db.Column(db.Numeric(10, 2))
    tipo_costo = db.Column(db.String(20), nullable=False)  # 'por_persona' o 'por_vehiculo'
    tiempo_recorrido_base = db.Column(db.Integer)  # en minutos

    # Relación 1:N con ITINERARIO_DETALLE (USADO EN)
    detalles = db.relationship('ItinerarioDetalle', backref='transporte', lazy=True)
