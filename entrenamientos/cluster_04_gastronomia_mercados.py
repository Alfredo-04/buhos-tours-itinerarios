# -*- coding: utf-8 -*-
"""
Clúster 4: Gastronomía Tradicional y Mercados (Escenarios 41 al 50)
Enfoque: Comida típica, mercados tradicionales, plazas y vida popular paceña.
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from entrenamientos.base_entrenador import entrenar_escenario_individual

app = create_app()

ESCENARIOS_CLUSTER_4 = [
    {
        "nombre": "Escenario #41 - Sabores Tradicionales Express (1d, 2p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [4],
        "subcategorias_activas_ids": [9],        # Gastronomía Tradicional
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 300.0,
        "num_dias": 1,
        "num_personas": 2,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "08:30",
        "hora_fin_dia": "16:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 5,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Gastronomía": 1.0, "Gastronomía Tradicional": 1.0}
    },
    {
        "nombre": "Escenario #42 - Tour de Mercados y Comida 2 Días (2d, 2p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [3, 4],
        "subcategorias_activas_ids": [8, 9],     # Mercados, Gastronomía
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 700.0,
        "num_dias": 2,
        "num_personas": 2,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 8,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Gastronomía": 1.0, "Urbano": 0.8, "Mercados Tradicionales": 0.9, "Gastronomía Tradicional": 0.9}
    },
    {
        "nombre": "Escenario #43 - Degustación Andina Pareja (2d, 2p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [4],
        "subcategorias_activas_ids": [9],        # Gastronomía
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 900.0,
        "num_dias": 2,
        "num_personas": 2,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "10:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 6,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Gastronomía": 1.0, "Gastronomía Tradicional": 1.0}
    },
    {
        "nombre": "Escenario #44 - Sabores y Plazas con Amigos (2d, 4p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [3, 4],
        "subcategorias_activas_ids": [7, 9],     # Plazas, Gastronomía
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 1200.0,
        "num_dias": 2,
        "num_personas": 4,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "09:30",
        "hora_fin_dia": "19:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 5,
        "max_paradas": 9,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Gastronomía": 0.9, "Urbano": 0.8, "Plazas": 0.8, "Gastronomía Tradicional": 0.9}
    },
    {
        "nombre": "Escenario #45 - Circuito Gastronómico 3 Días (3d, 3p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 4],
        "subcategorias_activas_ids": [3, 9],     # Sitios, Gastronomía
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 1800.0,
        "num_dias": 3,
        "num_personas": 3,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "17:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 6,
        "max_paradas": 10,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Gastronomía": 1.0, "Cultural": 0.6, "Gastronomía Tradicional": 1.0}
    },
    {
        "nombre": "Escenario #46 - Medio Día de Comida Típica (1d, 2p, Taxi)",
        "atractivos_ids": [],
        "categorias_activas_ids": [4],
        "subcategorias_activas_ids": [9],        # Gastronomía
        "transporte_ids": [1],                   # Taxi
        "forzar_transporte": True,
        "presupuesto_max": 250.0,
        "num_dias": 1,
        "num_personas": 2,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "11:00",
        "hora_fin_dia": "16:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 2,
        "max_paradas": 4,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Gastronomía": 1.0, "Gastronomía Tradicional": 1.0}
    },
    {
        "nombre": "Escenario #47 - Mercado Tradicional y Artesanía (1d, 3p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [3, 4],
        "subcategorias_activas_ids": [8, 9],     # Mercados, Gastronomía
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 500.0,
        "num_dias": 1,
        "num_personas": 3,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 6,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Gastronomía": 0.8, "Urbano": 0.9, "Mercados Tradicionales": 1.0}
    },
    {
        "nombre": "Escenario #48 - Gastronomía y Vistas Panorámicas (2d, 2p, Libre, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2, 4],
        "subcategorias_activas_ids": [4, 9],     # Miradores, Gastronomía
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 800.0,
        "num_dias": 2,
        "num_personas": 2,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "10:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 7,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Gastronomía": 0.9, "Naturaleza": 0.7, "Miradores": 0.8, "Gastronomía Tradicional": 0.9}
    },
    {
        "nombre": "Escenario #49 - Riqueza Culinaria en Van (3d, 6p, Van)",
        "atractivos_ids": [],
        "categorias_activas_ids": [4],
        "subcategorias_activas_ids": [9],        # Gastronomía
        "transporte_ids": [2],                   # Van
        "forzar_transporte": True,
        "presupuesto_max": 2800.0,
        "num_dias": 3,
        "num_personas": 6,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 6,
        "max_paradas": 10,
        "permitir_multiples_vehiculos": False,   # 6 <= Van cap 10
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Gastronomía": 1.0, "Gastronomía Tradicional": 1.0}
    },
    {
        "nombre": "Escenario #50 - Tradición Popular de Tarde (1d, 1p, Caminata)",
        "atractivos_ids": [],
        "categorias_activas_ids": [3, 4],
        "subcategorias_activas_ids": [8, 9],     # Mercados, Gastronomía
        "transporte_ids": [4],                   # Caminata
        "forzar_transporte": True,
        "presupuesto_max": 180.0,
        "num_dias": 1,
        "num_personas": 1,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "13:00",
        "hora_fin_dia": "18:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 2,
        "max_paradas": 4,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Gastronomía": 0.9, "Urbano": 0.8, "Mercados Tradicionales": 0.9}
    }
]

def main():
    with app.app_context():
        print("=" * 80)
        print("  INICIANDO ENTRENAMIENTO - CLÚSTER 4: GASTRONOMÍA TRADICIONAL Y MERCADOS")
        print("=" * 80)
        for esc in ESCENARIOS_CLUSTER_4:
            entrenar_escenario_individual(esc)
        print("\n[ÉXITO] Clúster 4 finalizado completamente.")

if __name__ == "__main__":
    main()
