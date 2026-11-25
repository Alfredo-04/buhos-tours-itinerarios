# -*- coding: utf-8 -*-
"""
Clúster 1: Express Urbanos y Centro Histórico (Escenarios 11 al 20)
Enfoque: Rutas cortas (1-2 días), 1-4 personas, alta densidad en casco central, caminata y taxi.
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from entrenamientos.base_entrenador import entrenar_escenario_individual

app = create_app()

ESCENARIOS_CLUSTER_1 = [
    {
        "nombre": "Escenario #11 - Casco Viejo Peatonal Express (1d, 1p, Caminata)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [2, 3, 7],  # Iglesias, Sitios Históricos, Plazas
        "transporte_ids": [4],                   # Caminata
        "forzar_transporte": True,
        "presupuesto_max": 150.0,
        "num_dias": 1,
        "num_personas": 1,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "16:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 5,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.9, "Urbano": 0.8, "Iglesias y Templos": 0.9, "Sitios Patrimoniales y Calles Históricas": 1.0, "Plazas": 0.7}
    },
    {
        "nombre": "Escenario #12 - Museos y Plazas Centro Pareja (2d, 2p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [1, 7],     # Museos, Plazas
        "transporte_ids": [1, 4],                # Taxi, Caminata
        "forzar_transporte": False,
        "presupuesto_max": 600.0,
        "num_dias": 2,
        "num_personas": 2,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "09:30",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 8,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Urbano": 0.6, "Museos": 1.0, "Plazas": 0.8}
    },
    {
        "nombre": "Escenario #13 - Medio Día Patrimonial Acelerado (1d, 2p, Taxi)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1],
        "subcategorias_activas_ids": [1, 3],     # Museos, Sitios Históricos
        "transporte_ids": [1],                   # Taxi
        "forzar_transporte": True,
        "presupuesto_max": 250.0,
        "num_dias": 1,
        "num_personas": 2,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "08:00",
        "hora_fin_dia": "13:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 2,
        "max_paradas": 4,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Museos": 0.9, "Sitios Patrimoniales y Calles Históricas": 0.9}
    },
    {
        "nombre": "Escenario #14 - Arquitectura y Calles Típicas (2d, 3p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [3, 7, 8],  # Sitios, Plazas, Mercados
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 900.0,
        "num_dias": 2,
        "num_personas": 3,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 5,
        "max_paradas": 9,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Urbano": 1.0, "Sitios Patrimoniales y Calles Históricas": 0.8, "Plazas": 0.9, "Mercados Tradicionales": 0.7}
    },
    {
        "nombre": "Escenario #15 - Domingo Familiar Centro (1d, 4p, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [3, 4],
        "subcategorias_activas_ids": [7, 8, 9],  # Plazas, Mercados, Gastronomía
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 400.0,
        "num_dias": 1,
        "num_personas": 4,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "08:30",
        "hora_fin_dia": "16:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 6,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Urbano": 0.8, "Gastronomía": 0.9, "Mercados Tradicionales": 1.0, "Gastronomía Tradicional": 0.9}
    },
    {
        "nombre": "Escenario #16 - Circuito Religioso Colonial (2d, 2p, Caminata)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1],
        "subcategorias_activas_ids": [2, 3],     # Iglesias, Sitios
        "transporte_ids": [4],
        "forzar_transporte": True,
        "presupuesto_max": 500.0,
        "num_dias": 2,
        "num_personas": 2,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 7,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Iglesias y Templos": 1.0, "Sitios Patrimoniales y Calles Históricas": 0.7}
    },
    {
        "nombre": "Escenario #17 - Urbano Universitario 2 Días (2d, 4p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [1, 7, 8],  # Museos, Plazas, Mercados
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 700.0,
        "num_dias": 2,
        "num_personas": 4,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "10:00",
        "hora_fin_dia": "19:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 6,
        "max_paradas": 10,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.6, "Urbano": 0.9, "Museos": 0.7, "Mercados Tradicionales": 0.8}
    },
    {
        "nombre": "Escenario #18 - Plazas y Miradores Centrales (1d, 2p, Taxi, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2, 3],
        "subcategorias_activas_ids": [4, 7],     # Miradores, Plazas
        "transporte_ids": [1],
        "forzar_transporte": True,
        "presupuesto_max": 300.0,
        "num_dias": 1,
        "num_personas": 2,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 5,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 0.7, "Urbano": 0.8, "Miradores": 1.0, "Plazas": 0.8}
    },
    {
        "nombre": "Escenario #19 - Paseo Histórico Tarde y Noche (1d, 3p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [3, 7],     # Sitios, Plazas
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 450.0,
        "num_dias": 1,
        "num_personas": 3,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "13:00",
        "hora_fin_dia": "19:59",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 5,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.9, "Urbano": 0.7, "Sitios Patrimoniales y Calles Históricas": 1.0}
    },
    {
        "nombre": "Escenario #20 - Centro Monotemático Cultural (2d, 1p, Caminata)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1],
        "subcategorias_activas_ids": [1, 2, 3],  # Museos, Iglesias, Sitios
        "transporte_ids": [4],
        "forzar_transporte": True,
        "presupuesto_max": 400.0,
        "num_dias": 2,
        "num_personas": 1,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "17:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 5,
        "max_paradas": 8,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Museos": 0.9, "Iglesias y Templos": 0.8, "Sitios Patrimoniales y Calles Históricas": 0.9}
    }
]

def main():
    with app.app_context():
        print("=" * 80)
        print("  INICIANDO ENTRENAMIENTO - CLÚSTER 1: EXPRESS URBANOS Y CENTRO HISTÓRICO")
        print("=" * 80)
        for esc in ESCENARIOS_CLUSTER_1:
            entrenar_escenario_individual(esc)
        print("\n[ÉXITO] Clúster 1 finalizado completamente.")

if __name__ == "__main__":
    main()
