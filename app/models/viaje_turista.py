from app import db
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class ViajeTurista(db.Model):
    __tablename__ = 'viaje_turista'
    id_itinerario = db.Column(db.Integer, db.ForeignKey('itinerario.id_itinerario'), primary_key=True)
    id_turista = db.Column(db.Integer, db.ForeignKey('turista.id_turista'), primary_key=True)

    # No se necesitan más atributos, es una tabla intermedia pura
