from datetime import datetime
from app import db

class ArchivoPareto(db.Model):
    __tablename__ = 'archivo_pareto'

    id_archivo = db.Column(db.Integer, primary_key=True)
    
    # ADIÓS AL HASH. Ahora guardamos el Vector de 6 dimensiones en formato JSON
    vector_instancia_json = db.Column(db.Text, nullable=False) 
    
    ref_point_json = db.Column(db.Text, nullable=False)
    valores_json = db.Column(db.Text, nullable=False)
    num_puntos = db.Column(db.Integer, nullable=False, default=0)
    total_ejecuciones = db.Column(db.Integer, nullable=False, default=1)
    
    # --- LAS RECETAS (META-OPTIMIZACIÓN) ---
    poblacion_optima = db.Column(db.Integer, nullable=True)
    generaciones_optimas = db.Column(db.Integer, nullable=True)
    prob_mutacion_optima = db.Column(db.Numeric(4, 2), nullable=True)
    historial_hv_json = db.Column(db.Text, nullable=True)
    
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ArchivoPareto #{self.id_archivo} puntos={self.num_puntos} receta(P={self.poblacion_optima}, G={self.generaciones_optimas})>"