from datetime import datetime
from app import db

class ConsultaNSGA2(db.Model):
    __tablename__ = 'consulta_nsga2'

    id_consulta = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.now)
    id_generacion = db.Column(db.Integer, db.ForeignKey('generacion.id_generacion'), nullable=True)
    
    # Parámetros del problema
    num_atractivos = db.Column(db.Integer, nullable=False)
    num_transportes = db.Column(db.Integer, nullable=False)
    presupuesto = db.Column(db.Numeric(10, 2), nullable=False)
    tiempo_disponible_horas = db.Column(db.Numeric(5, 2), nullable=False)
    intereses = db.Column(db.Text, nullable=True)
    
    # Parámetros del Algoritmo (Los que realmente se usaron en esta corrida)
    tamano_poblacion = db.Column(db.Integer, nullable=False)
    generaciones = db.Column(db.Integer, nullable=False)
    prob_cruce = db.Column(db.Numeric(4, 2), nullable=False)
    prob_mutacion = db.Column(db.Numeric(4, 2), nullable=False)
    
    # Resultados generales
    num_soluciones = db.Column(db.Integer, nullable=False)
    mejor_afinidad = db.Column(db.Numeric(5, 4), nullable=True)
    mejor_tiempo = db.Column(db.Numeric(10, 2), nullable=True)
    soluciones_viables = db.Column(db.Integer, nullable=False)
    todas_exceden = db.Column(db.Boolean, nullable=False, default=False)
    tiempo_ejecucion_seg = db.Column(db.Numeric(6, 2), nullable=True)
    
    # Métricas antiguas (compatibilidad)
    convergencia = db.Column(db.Numeric(5, 4), nullable=True)
    diversidad_final = db.Column(db.Numeric(5, 4), nullable=True)

    # --- MÉTRICAS FORMALES ---
    hipervolumen = db.Column(db.Numeric(8, 6), nullable=True)
    generational_distance = db.Column(db.Numeric(8, 6), nullable=True) 
    spread_spacing = db.Column(db.Numeric(8, 6), nullable=True)

    # Restricciones y fechas
    fecha_inicio_viaje = db.Column(db.Date, nullable=True)
    fecha_fin_viaje = db.Column(db.Date, nullable=True)
    hora_inicio_dia = db.Column(db.Time, nullable=True)
    hora_fin_dia = db.Column(db.Time, nullable=True)
    auto_rango_paradas = db.Column(db.Boolean, nullable=False, default=True)
    min_paradas = db.Column(db.Integer, nullable=True)
    max_paradas = db.Column(db.Integer, nullable=True)
    usar_clima = db.Column(db.Boolean, nullable=False, default=True)
    
    atractivos_ids_json = db.Column(db.Text, nullable=True) 
    transporte_ids_json = db.Column(db.Text, nullable=True)
    hubo_soluciones_viables = db.Column(db.Boolean, nullable=False, default=True)
    
    # Guardamos el vector de esta consulta en específico para auditoría
    vector_instancia_json = db.Column(db.Text, nullable=True)
    
    # --- RELACIÓN CON EL VECINO MÁS CERCANO (KNN) ---
    # En lugar de un hash, apuntamos al ID del archivo pareto que se usó como referencia
    id_archivo_pareto = db.Column(
        db.Integer, 
        db.ForeignKey('archivo_pareto.id_archivo', name='fk_consulta_archivo_pareto'), 
        nullable=True, 
        index=True
    )
    
    resultados_json = db.Column(db.Text, nullable=True)

    # Relaciones
    generacion = db.relationship('Generacion', backref='consultas_nsga2', lazy=True)
    archivo_pareto_rel = db.relationship('ArchivoPareto', foreign_keys=[id_archivo_pareto], lazy=True)

    def __repr__(self):
        return f"<ConsultaNSGA2 #{self.id_consulta} Soluciones:{self.num_soluciones} HV:{self.hipervolumen}>"