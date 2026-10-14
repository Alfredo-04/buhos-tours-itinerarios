from datetime import datetime
from app import db

class DistanciaAtractivo(db.Model):
    __tablename__ = 'distancia_atractivo'

    id_distancia = db.Column(db.Integer, primary_key=True)
    id_atractivo_origen = db.Column(db.Integer, db.ForeignKey('atractivo.id_atractivo'), nullable=False)
    id_atractivo_destino = db.Column(db.Integer, db.ForeignKey('atractivo.id_atractivo'), nullable=False)
    distancia_km = db.Column(db.Numeric(8, 3), nullable=False)
    duracion_min = db.Column(db.Numeric(6, 2), nullable=False)
    polyline_coords = db.Column(db.Text, nullable=True)  # JSON con array [[lat, lon], ...]
    fuente = db.Column(db.String(20), nullable=False, default='osrm')  # 'osrm' o 'manual'
    fecha_calculo = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Restricción única de par (origen, destino)
    __table_args__ = (
        db.UniqueConstraint('id_atractivo_origen', 'id_atractivo_destino', name='uq_distancia_origen_destino'),
    )

    # Relaciones con ATRACTIVO
    atractivo_origen = db.relationship('Atractivo', foreign_keys=[id_atractivo_origen], backref='distancias_salida', lazy=True)
    atractivo_destino = db.relationship('Atractivo', foreign_keys=[id_atractivo_destino], backref='distancias_llegada', lazy=True)

    def __repr__(self):
        return f"<DistanciaAtractivo {self.id_atractivo_origen}->{self.id_atractivo_destino} ({self.distancia_km}km, {self.duracion_min}min, {self.fuente})>"
