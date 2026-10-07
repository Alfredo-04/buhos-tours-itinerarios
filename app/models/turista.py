from app import db

class Turista(db.Model):
    __tablename__ = 'turista'

    id_turista = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=True, unique=True)
    nombres = db.Column(db.String(80), nullable=False)
    apellidos = db.Column(db.String(80), nullable=False)
    nacionalidad = db.Column(db.String(50), nullable=True)
    procedencia = db.Column(db.String(50), nullable=True)
    nro_documento = db.Column(db.String(20), nullable=True, unique=True)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    pasaporte_vencimiento = db.Column(db.Date, nullable=True)
    email = db.Column(db.String(100), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)

    # Relación 1:1 opcional con USUARIO
    usuario = db.relationship('Usuario', backref=db.backref('turista', uselist=False))

    def __repr__(self):
        return f"<Turista #{self.id_turista} {self.nombres} {self.apellidos}>"
