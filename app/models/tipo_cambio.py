from datetime import datetime
from app import db

class TipoCambio(db.Model):
    __tablename__ = 'tipo_cambio'

    id_tipo_cambio = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    valor_compra = db.Column(db.Numeric(10, 4), nullable=False)
    valor_venta = db.Column(db.Numeric(10, 4), nullable=False)
    fuente = db.Column(db.String(20), nullable=False, default='api')  # 'api' o 'manual'
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=True)

    # Relación opcional con USUARIO
    usuario = db.relationship('Usuario', backref='tipos_cambio', lazy=True)

    def __repr__(self):
        return f"<TipoCambio #{self.id_tipo_cambio} {self.fecha} Venta:{self.valor_venta} ({self.fuente})>"
