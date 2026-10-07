from datetime import datetime
from app import db

class Subcategoria(db.Model):
    __tablename__ = 'subcategoria'

    id_subcategoria = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.String(200), nullable=True)
    id_categoria = db.Column(db.Integer, db.ForeignKey('categoria.id_categoria'), nullable=False)

    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True, default=None)

    # Relación con CATEGORIA
    categoria = db.relationship('Categoria', backref='subcategorias', lazy=True)

    @property
    def is_deleted(self):
        """Indica si la subcategoría se encuentra eliminada lógicamente"""
        return self.deleted_at is not None

    def __repr__(self):
        status = " (Eliminado)" if self.is_deleted else ""
        return f"<Subcategoria #{self.id_subcategoria} {self.nombre}{status}>"
