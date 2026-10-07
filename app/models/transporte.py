from datetime import datetime
from app import db

class Transporte(db.Model):
    __tablename__ = 'transporte'

    id_transporte = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'Privado' o 'Público'
    capacidad = db.Column(db.Integer, nullable=True)
    horario_inicio = db.Column(db.Time, nullable=True)
    horario_fin = db.Column(db.Time, nullable=True)
    costo = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    tipo_costo = db.Column(db.String(20), nullable=False)  # 'por_dia' o 'por_persona'
    velocidad_promedio_kmh = db.Column(db.Numeric(5, 2), nullable=False, default=30.0)

    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True, default=None)

    @property
    def costo_por_tramo(self):
        """Propiedad de compatibilidad regresiva para costo"""
        return self.costo

    @costo_por_tramo.setter
    def costo_por_tramo(self, val):
        self.costo = val

    @property
    def is_deleted(self):
        """Indica si el transporte se encuentra eliminado lógicamente"""
        return self.deleted_at is not None

    def __repr__(self):
        status = " (Eliminado)" if self.is_deleted else ""
        return f"<Transporte #{self.id_transporte} {self.nombre} ({self.tipo}){status}>"
