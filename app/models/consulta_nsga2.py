from datetime import datetime
from app import db

class ConsultaNSGA2(db.Model):
    __tablename__ = 'consulta_nsga2'

    id_consulta = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    id_generacion = db.Column(db.Integer, db.ForeignKey('generacion.id_generacion'), nullable=True)
    num_atractivos = db.Column(db.Integer, nullable=False)
    num_transportes = db.Column(db.Integer, nullable=False)
    presupuesto = db.Column(db.Numeric(10, 2), nullable=False)
    tiempo_disponible_horas = db.Column(db.Numeric(5, 2), nullable=False)
    intereses = db.Column(db.Text, nullable=True)  # JSON con categorías y pesos
    tamano_poblacion = db.Column(db.Integer, nullable=False)
    generaciones = db.Column(db.Integer, nullable=False)
    prob_cruce = db.Column(db.Numeric(4, 2), nullable=False)
    prob_mutacion = db.Column(db.Numeric(4, 2), nullable=False)
    num_soluciones = db.Column(db.Integer, nullable=False)
    mejor_afinidad = db.Column(db.Numeric(5, 4), nullable=True)
    mejor_tiempo = db.Column(db.Numeric(10, 2), nullable=True)
    soluciones_viables = db.Column(db.Integer, nullable=False)
    todas_exceden = db.Column(db.Boolean, nullable=False, default=False)
    tiempo_ejecucion_seg = db.Column(db.Numeric(6, 2), nullable=True)
    convergencia = db.Column(db.Numeric(5, 4), nullable=True)
    diversidad_final = db.Column(db.Numeric(5, 4), nullable=True)

    # --- NUEVOS CAMPOS ---
    fecha_inicio_viaje = db.Column(db.Date, nullable=True)
    fecha_fin_viaje = db.Column(db.Date, nullable=True)
    hora_inicio_dia = db.Column(db.Time, nullable=True)
    hora_fin_dia = db.Column(db.Time, nullable=True)
    auto_rango_paradas = db.Column(db.Boolean, nullable=False, default=True)
    min_paradas = db.Column(db.Integer, nullable=True)
    max_paradas = db.Column(db.Integer, nullable=True)
    usar_clima = db.Column(db.Boolean, nullable=False, default=True)
    
    # Guardar los IDs usados en esta consulta para el entrenamiento empírico
    atractivos_ids_json = db.Column(db.Text, nullable=True) 
    transporte_ids_json = db.Column(db.Text, nullable=True)
    hubo_soluciones_viables = db.Column(db.Boolean, nullable=False, default=True)
    hash_parametros = db.Column(db.String(64), nullable=True)
    resultados_json = db.Column(db.Text, nullable=True)  # Guarda el JSON de soluciones para caché

    # Relación con GENERACION
    generacion = db.relationship('Generacion', backref='consultas_nsga2', lazy=True)

    def __repr__(self):
        return f"<ConsultaNSGA2 #{self.id_consulta} ({self.fecha}) Soluciones:{self.num_soluciones}>"
