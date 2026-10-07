from datetime import datetime
from app import db

class PatronTrafico(db.Model):
    __tablename__ = 'patron_trafico'

    id_patron = db.Column(db.Integer, primary_key=True)
    id_zona = db.Column(db.Integer, db.ForeignKey('zona_trafico.id_zona'), nullable=False)
    dia_semana = db.Column(db.String(20), nullable=False)  # lunes, martes, ..., domingo
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    factor_congestion = db.Column(db.Numeric(4, 2), nullable=False, default=1.0)
    color_nivel = db.Column(db.String(20), nullable=False)  # verde, amarillo, naranja, rojo
    tipo = db.Column(db.String(20), nullable=False)  # trafico, feria, cierre

    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True, default=None)

    # Relación con ZONA_TRAFICO
    zona = db.relationship('ZonaTrafico', backref='patrones', lazy=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def __repr__(self):
        status = " (Eliminado)" if self.is_deleted else ""
        return f"<PatronTrafico #{self.id_patron} ({self.dia_semana} {self.hora_inicio}-{self.hora_fin}){status}>"
