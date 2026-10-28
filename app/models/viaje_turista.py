from app import db

class ViajeTurista(db.Model):
    __tablename__ = 'viaje_turista'
    __table_args__ = (
        db.UniqueConstraint('id_itinerario', 'id_turista', name='uq_viaje_turista_itinerario_turista'),
    )

    id_viaje_turista = db.Column(db.Integer, primary_key=True)
    id_itinerario = db.Column(db.Integer, db.ForeignKey('itinerario.id_itinerario'), nullable=False)
    id_turista = db.Column(db.Integer, db.ForeignKey('turista.id_turista'), nullable=False)

    itinerario = db.relationship('Itinerario', backref=db.backref('viajes_turistas', cascade='all, delete-orphan'), lazy=True)
    turista = db.relationship('Turista', backref='viajes', lazy=True)

    def __repr__(self):
        return f"<ViajeTurista #{self.id_viaje_turista} Itin:{self.id_itinerario} Turista:{self.id_turista}>"
