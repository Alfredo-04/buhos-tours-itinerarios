from app import db

class ViajeTurista(db.Model):
    __tablename__ = 'viaje_turista'

    id_itinerario = db.Column(db.Integer, db.ForeignKey('itinerario.id_itinerario'), primary_key=True)
    id_turista = db.Column(db.Integer, db.ForeignKey('turista.id_turista'), primary_key=True)

    itinerario = db.relationship('Itinerario', backref=db.backref('viajes_turistas', cascade='all, delete-orphan'), lazy=True)
    turista = db.relationship('Turista', backref='viajes', lazy=True)

    def __repr__(self):
        return f"<ViajeTurista Itin:{self.id_itinerario} Turista:{self.id_turista}>"
