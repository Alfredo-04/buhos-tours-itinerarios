from datetime import datetime
from app import db

class Atractivo(db.Model):
    __tablename__ = 'atractivo'

    id_atractivo = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.String(500), nullable=True)
    latitud = db.Column(db.Numeric(10, 7), nullable=True)
    longitud = db.Column(db.Numeric(10, 7), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    horario_apertura = db.Column(db.Time, nullable=True)
    horario_cierre = db.Column(db.Time, nullable=True)
    costo_entrada = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    tiempo_visita_estimado = db.Column(db.Integer, nullable=True)  # en minutos
    dias_cerrado = db.Column(db.Text, nullable=True)  # multivalorado, ej. "Lunes,Martes"
    imagen_url = db.Column(db.String(255), nullable=True)
    fecha_inicio = db.Column(db.Date, nullable=True)
    fecha_fin = db.Column(db.Date, nullable=True)
    afecta_rutas = db.Column(db.Boolean, nullable=False, default=False)
    sensible_al_clima = db.Column(db.Boolean, nullable=False, default=False)
    tipo_clima_ideal = db.Column(db.String(100), nullable=True)

    # Claves foráneas
    id_subcategoria = db.Column(db.Integer, db.ForeignKey('subcategoria.id_subcategoria'), nullable=False)
    id_proveedor = db.Column(db.Integer, db.ForeignKey('proveedor.id_proveedor'), nullable=False)

    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True, default=None)

    # Relaciones
    subcategoria = db.relationship('Subcategoria', backref='atractivos', lazy=True)
    proveedor = db.relationship('Proveedor', backref='atractivos', lazy=True)

    @property
    def categoria(self):
        """Propiedad de acceso directo a la categoría padre a través de subcategoría"""
        return self.subcategoria.categoria if self.subcategoria else None

    @property
    def id_categoria(self):
        """Propiedad de compatibilidad con id_categoria"""
        return self.subcategoria.id_categoria if self.subcategoria else None

    @property
    def is_deleted(self):
        """Indica si el atractivo se encuentra eliminado lógicamente"""
        return self.deleted_at is not None

    def __repr__(self):
        status = " (Eliminado)" if self.is_deleted else ""
        return f"<Atractivo #{self.id_atractivo} {self.nombre}{status}>"
