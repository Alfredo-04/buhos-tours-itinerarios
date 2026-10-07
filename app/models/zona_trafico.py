from datetime import datetime
from app import db

class ZonaTrafico(db.Model):
    __tablename__ = 'zona_trafico'

    id_zona = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo_geometria = db.Column(db.String(20), nullable=False)  # poligono, polilinea, punto
    geometria_wkt = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # trafico, feria, cierre, bloqueo

    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True, default=None)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def __repr__(self):
        status = " (Eliminado)" if self.is_deleted else ""
        return f"<ZonaTrafico #{self.id_zona} {self.nombre} ({self.tipo}){status}>"
