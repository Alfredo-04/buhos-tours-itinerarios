import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app import db

class Itinerario(db.Model):
    __tablename__ = 'itinerario'

    id_itinerario = db.Column(db.Integer, primary_key=True)
    id_generacion = db.Column(db.Integer, db.ForeignKey('generacion.id_generacion'), nullable=False)
    numero_solucion = db.Column(db.Integer, nullable=False)  # índice dentro de la generación
    estado = db.Column(db.String(20), nullable=False, default='Borrador')
    tiempo_total_estimado = db.Column(db.Numeric(10, 2), nullable=True)  # derivado
    codigo_confirmacion = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    voucher_generado = db.Column(db.Boolean, nullable=False, default=False)

    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True, default=None)

    # --- NUEVOS CAMPOS ---
    afinidad = db.Column(db.Numeric(5, 4), nullable=True)  # % de afinidad (0.0000 a 1.0000)
    costo_total_bob = db.Column(db.Numeric(10, 2), nullable=True)
    costo_entradas_bob = db.Column(db.Numeric(10, 2), nullable=True)
    costo_transporte_bob = db.Column(db.Numeric(10, 2), nullable=True)
    distancia_total_km = db.Column(db.Numeric(8, 2), nullable=True)
    fecha_inicio = db.Column(db.Date, nullable=True)
    fecha_fin = db.Column(db.Date, nullable=True)
    dias_totales = db.Column(db.Integer, nullable=True, default=1)
    num_personas = db.Column(db.Integer, nullable=False, default=1, server_default='1')
    es_viable = db.Column(db.Boolean, nullable=False, default=True)
    snapshot_json = db.Column(db.Text, nullable=True)

    # Relación con GENERACION
    generacion = db.relationship('Generacion', backref='itinerarios', lazy=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def __repr__(self):
        status = " (Eliminado)" if self.is_deleted else ""
        return f"<Itinerario #{self.id_itinerario} (Gen {self.id_generacion}, Sol #{self.numero_solucion}, {self.estado}){status}>"
