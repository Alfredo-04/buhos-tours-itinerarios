from app import db
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class Generacion(db.Model):
    __tablename__ = 'generacion'
    id_generacion = db.Column(db.Integer, primary_key=True)
    fecha_generacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    fecha_inicio_viaje = db.Column(db.Date, nullable=False)
    fecha_fin_viaje = db.Column(db.Date, nullable=False)
    presupuesto = db.Column(db.Numeric(10, 2), nullable=False)
    cantidad_soluciones = db.Column(db.Integer, nullable=False)
    observaciones = db.Column(db.Text)

    # Relación 1:N con ITINERARIO (CONTIENE)
    itinerarios = db.relationship('Itinerario', backref='generacion', lazy=True)
