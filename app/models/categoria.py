from datetime import datetime
from app import db

class Categoria(db.Model):
    __tablename__ = 'categoria'

    id_categoria = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.String(200), nullable=True)

    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True, default=None)

    @property
    def is_deleted(self):
        """Indica si la categoría se encuentra eliminada lógicamente"""
        return self.deleted_at is not None

    def __repr__(self):
        status = " (Eliminado)" if self.is_deleted else ""
        return f"<Categoria #{self.id_categoria} {self.nombre}{status}>"
