from datetime import datetime
from app import db

class ArchivoPareto(db.Model):
    __tablename__ = 'archivo_pareto'

    id_archivo = db.Column(db.Integer, primary_key=True)
    # CAMBIO: Este hash ahora será el "bucket" normalizado (rangos)
    hash_problema_bucket = db.Column(db.String(64), nullable=False, unique=True, index=True)
    
    ref_point_json = db.Column(db.Text, nullable=False)
    valores_json = db.Column(db.Text, nullable=False)
    num_puntos = db.Column(db.Integer, nullable=False, default=0)
    
    # NUEVO: Para saber cuántas veces se ha alimentado este bucket
    total_ejecuciones = db.Column(db.Integer, nullable=False, default=1)
    
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ArchivoPareto Bucket:{self.hash_problema_bucket[:8]}... puntos={self.num_puntos} ejecuciones={self.total_ejecuciones}>"