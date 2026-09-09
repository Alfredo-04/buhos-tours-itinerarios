from app import db
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class Turista(db.Model):
    __tablename__ = 'turista'
    id_turista = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(80), nullable=False)
    apellidos = db.Column(db.String(80), nullable=False)
    nacionalidad = db.Column(db.String(50), nullable=False)
    procedencia = db.Column(db.String(50), nullable=False)
    nro_documento = db.Column(db.String(20), nullable=False, unique=True)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    pasaporte_vencimiento = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(100))
    telefono = db.Column(db.String(20))

    # Relación N:M con ITINERARIO a través de VIAJE_TURISTA
    viajes = db.relationship('ViajeTurista', backref='turista', lazy=True)
