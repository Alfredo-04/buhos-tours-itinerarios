from datetime import datetime
from app import db

class RecetaEntrenamiento(db.Model):
    __tablename__ = 'receta_entrenamiento'

    id_receta = db.Column(db.Integer, primary_key=True)
    
    # Llave foránea al escenario en ArchivoPareto
    id_archivo = db.Column(
        db.Integer, 
        db.ForeignKey('archivo_pareto.id_archivo', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    
    # Parámetros probados en el Grid Search
    poblacion = db.Column(db.Integer, nullable=False)
    generaciones = db.Column(db.Integer, nullable=False)
    mutacion = db.Column(db.Numeric(4, 2), nullable=False)
    
    # Métricas promediadas (después de N corridas)
    gd_promedio = db.Column(db.Numeric(8, 6), nullable=True)
    spread_promedio = db.Column(db.Numeric(8, 6), nullable=True)
    hv_promedio = db.Column(db.Numeric(8, 6), nullable=True)
    tiempo_promedio_seg = db.Column(db.Numeric(6, 2), nullable=True)
    
    # Flag para marcar la configuración ganadora
    es_ganadora = db.Column(db.Boolean, nullable=False, default=False)

    historial_hv_json = db.Column(db.Text, nullable=True)
    historial_gd_json = db.Column(db.Text, nullable=True)
    historial_spread_json = db.Column(db.Text, nullable=True)
    
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relación con ArchivoPareto
    archivo_pareto_rel = db.relationship('ArchivoPareto', backref='recetas_entrenamiento', lazy=True)

    def __repr__(self):
        return f"<RecetaEntrenamiento #{self.id_receta} (P={self.poblacion}, M={self.mutacion}) GD={self.gd_promedio}>"
