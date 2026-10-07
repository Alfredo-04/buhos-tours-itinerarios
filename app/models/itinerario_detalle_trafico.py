from app import db

class ItinerarioDetalleTrafico(db.Model):
    __tablename__ = 'itinerario_detalle_trafico'

    id_detalle = db.Column(db.Integer, db.ForeignKey('itinerario_detalle.id_detalle'), primary_key=True)
    id_patron = db.Column(db.Integer, db.ForeignKey('patron_trafico.id_patron'), primary_key=True)

    itinerario_detalle = db.relationship('ItinerarioDetalle', backref=db.backref('traficos', cascade='all, delete-orphan'), lazy=True)
    patron_trafico = db.relationship('PatronTrafico', backref='detalles_trafico', lazy=True)

    def __repr__(self):
        return f"<ItinerarioDetalleTrafico Detalle:{self.id_detalle} Patron:{self.id_patron}>"
