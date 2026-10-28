from app import db

class ItinerarioDetalle(db.Model):
    __tablename__ = 'itinerario_detalle'

    id_detalle = db.Column(db.Integer, primary_key=True)
    id_itinerario = db.Column(db.Integer, db.ForeignKey('itinerario.id_itinerario'), nullable=False)
    id_atractivo = db.Column(db.Integer, db.ForeignKey('atractivo.id_atractivo'), nullable=False)
    id_transporte = db.Column(db.Integer, db.ForeignKey('transporte.id_transporte'), nullable=True)
    dia = db.Column(db.Integer, nullable=False)
    orden = db.Column(db.Integer, nullable=False)
    hora_llegada_estimada = db.Column(db.Time, nullable=True)
    hora_salida_estimada = db.Column(db.Time, nullable=True)
    tiempo_traslado_desde_anterior = db.Column(db.Integer, nullable=True)  # derivado, en minutos

    # --- NUEVOS CAMPOS ---
    costo_entrada_bob = db.Column(db.Numeric(10, 2), nullable=True)
    clima_temperatura = db.Column(db.Numeric(5, 2), nullable=True)
    clima_lluvia_mm = db.Column(db.Numeric(5, 2), nullable=True)
    clima_descripcion = db.Column(db.String(100), nullable=True)

    # Relaciones con modelos de fases anteriores
    itinerario = db.relationship('Itinerario', backref=db.backref('detalles', cascade='all, delete-orphan'), lazy=True)
    atractivo = db.relationship('Atractivo', backref='detalles', lazy=True)
    transporte = db.relationship('Transporte', backref='detalles', lazy=True)

    def __repr__(self):
        return f"<ItinerarioDetalle #{self.id_detalle} (Itin {self.id_itinerario}, Dia {self.dia}, Orden {self.orden})>"
