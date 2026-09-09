from app import db
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class ItinerarioDetalle(db.Model):
    __tablename__ = 'itinerario_detalle'
    id_detalle = db.Column(db.Integer, primary_key=True)
    id_itinerario = db.Column(db.Integer, db.ForeignKey('itinerario.id_itinerario'), nullable=False)
    id_atractivo = db.Column(db.Integer, db.ForeignKey('atractivo.id_atractivo'), nullable=False)
    id_transporte = db.Column(db.Integer, db.ForeignKey('transporte.id_transporte'), nullable=False)
    dia = db.Column(db.Integer, nullable=False)
    orden = db.Column(db.Integer, nullable=False)
    hora_llegada_estimada = db.Column(db.Time)
    hora_salida_estimada = db.Column(db.Time)
    tiempo_traslado_desde_anterior = db.Column(db.Integer)  # derivado, en minutos
