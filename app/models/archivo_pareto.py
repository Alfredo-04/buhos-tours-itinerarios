from datetime import datetime
from app import db


class ArchivoPareto(db.Model):
    __tablename__ = 'archivo_pareto'

    id_archivo = db.Column(db.Integer, primary_key=True)
    hash_problema = db.Column(db.String(64), nullable=False, unique=True, index=True)
    ref_point_json = db.Column(db.Text, nullable=False)
    valores_json = db.Column(db.Text, nullable=False)
    num_puntos = db.Column(db.Integer, nullable=False, default=0)
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ArchivoPareto {self.hash_problema[:8]}... puntos={self.num_puntos}>"
