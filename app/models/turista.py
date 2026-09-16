from app import db
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class Turista(db.Model):
    __tablename__ = 'turista'
    id_turista = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=True, unique=True)
    nombres = db.Column(db.String(80), nullable=False)
    apellidos = db.Column(db.String(80), nullable=False)
    nacionalidad = db.Column(db.String(50), nullable=True)
    procedencia = db.Column(db.String(50), nullable=True)
    nro_documento = db.Column(db.String(20), nullable=True, unique=True)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    pasaporte_vencimiento = db.Column(db.Date, nullable=True)
    email = db.Column(db.String(100))
    telefono = db.Column(db.String(20))

    # Relación 1:1 opcional con USUARIO
    usuario = db.relationship('Usuario', backref=db.backref('turista', uselist=False))

    # Relación N:M con ITINERARIO a través de VIAJE_TURISTA
    viajes = db.relationship('ViajeTurista', backref='turista', lazy=True)
