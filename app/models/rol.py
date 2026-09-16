from app import db

class Rol(db.Model):
    __tablename__ = 'rol'

    id_rol = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(20), unique=True, nullable=False)

    def __repr__(self):
        return f"<Rol {self.nombre}>"
