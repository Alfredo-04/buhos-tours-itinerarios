from datetime import datetime
from app import db

class Generacion(db.Model):
    __tablename__ = 'generacion'

    id_generacion = db.Column(db.Integer, primary_key=True)
    fecha_generacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    fecha_inicio_viaje = db.Column(db.Date, nullable=False)
    fecha_fin_viaje = db.Column(db.Date, nullable=False)
    presupuesto = db.Column(db.Numeric(10, 2), nullable=False)
    cantidad_soluciones = db.Column(db.Integer, nullable=False)
    observaciones = db.Column(db.Text, nullable=True)

    # Relación con USUARIO
    usuario = db.relationship('Usuario', backref='generaciones', lazy=True)

    def __repr__(self):
        return f"<Generacion #{self.id_generacion} (Usuario {self.id_usuario})>"
