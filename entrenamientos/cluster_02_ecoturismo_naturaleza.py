# -*- coding: utf-8 -*-
"""
Clúster 2: Ecoturismo, Miradores y Naturaleza (Escenarios 21 al 30)
Enfoque: Rutas hacia la periferia, valles, áreas protegidas y miradores; clima activo y traslados amplios.
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from entrenamientos.base_entrenador import entrenar_escenario_individual

app = create_app()

ESCENARIOS_CLUSTER_2 = [
    {
        "nombre": "Escenario #21 - Valles y Formaciones Rocosas (1d, 2p, Taxi, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2],
        "subcategorias_activas_ids": [4, 6],     # Miradores, Áreas Protegidas
        "transporte_ids": [1],                   # Taxi
        "forzar_transporte": True,
        "presupuesto_max": 600.0,
        "num_dias": 1,
        "num_personas": 2,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "08:00",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 2,
        "max_paradas": 4,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 1.0, "Áreas Protegidas": 1.0, "Miradores": 0.8}
    },
    {
        "nombre": "Escenario #22 - Ecoturismo Familiar 2 Días (2d, 4p, Libre, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2],
        "subcategorias_activas_ids": [4, 5, 6],  # Miradores, Parques, Áreas
        "transporte_ids": [1, 2],                # Taxi, Van
        "forzar_transporte": False,
        "presupuesto_max": 1800.0,
        "num_dias": 2,
        "num_personas": 4,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "08:30",
        "hora_fin_dia": "17:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 7,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 1.0, "Parques y Bosquecillos": 0.9, "Áreas Protegidas": 0.9}
    },
    {
        "nombre": "Escenario #23 - Cadena de Miradores Paceños (1d, 3p, Taxi, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2],
        "subcategorias_activas_ids": [4],        # Solo Miradores
        "transporte_ids": [1],
        "forzar_transporte": True,
        "presupuesto_max": 500.0,
        "num_dias": 1,
        "num_personas": 3,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "07:00",
        "hora_fin_dia": "15:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 6,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 1.0, "Miradores": 1.0}
    },
    {
        "nombre": "Escenario #24 - Parques Ecológicos y Bosques (2d, 2p, Libre, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2],
        "subcategorias_activas_ids": [5],        # Solo Parques y Bosquecillos
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 700.0,
        "num_dias": 2,
        "num_personas": 2,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "16:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 5,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 1.0, "Parques y Bosquecillos": 1.0}
    },
    {
        "nombre": "Escenario #25 - Aventura Paisajística 3 Días (3d, 3p, Van, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2],
        "subcategorias_activas_ids": [4, 6],     # Áreas Protegidas, Miradores
        "transporte_ids": [2],                   # Van
        "forzar_transporte": True,
        "presupuesto_max": 2200.0,
        "num_dias": 3,
        "num_personas": 3,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "08:00",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 5,
        "max_paradas": 8,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 1.0, "Áreas Protegidas": 1.0, "Miradores": 0.9}
    },
    {
        "nombre": "Escenario #26 - Fotografía de Paisajes 2 Días (2d, 2p, Libre, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2, 3],
        "subcategorias_activas_ids": [4, 7],     # Miradores, Plazas
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 1200.0,
        "num_dias": 2,
        "num_personas": 2,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "06:30",
        "hora_fin_dia": "18:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 7,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 0.9, "Urbano": 0.6, "Miradores": 1.0, "Plazas": 0.7}
    },
    {
        "nombre": "Escenario #27 - Naturaleza Relajada Tercera Edad (2d, 2p, Taxi, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2],
        "subcategorias_activas_ids": [5, 6],     # Parques, Áreas
        "transporte_ids": [1],
        "forzar_transporte": True,
        "presupuesto_max": 1100.0,
        "num_dias": 2,
        "num_personas": 2,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "10:00",
        "hora_fin_dia": "16:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 2,
        "max_paradas": 4,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 1.0, "Parques y Bosquecillos": 1.0, "Áreas Protegidas": 0.6}
    },
    {
        "nombre": "Escenario #28 - Circuito Valles del Sur en Van (1d, 5p, Van, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2],
        "subcategorias_activas_ids": [6],        # Áreas Protegidas
        "transporte_ids": [2],                   # Van
        "forzar_transporte": True,
        "presupuesto_max": 1000.0,
        "num_dias": 1,
        "num_personas": 5,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "08:00",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 2,
        "max_paradas": 4,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 1.0, "Áreas Protegidas": 1.0}
    },
    {
        "nombre": "Escenario #29 - Senderos Grupo Amigos 3 Días (3d, 6p, Libre, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2],
        "subcategorias_activas_ids": [4, 5, 6],  # Miradores, Parques, Áreas
        "transporte_ids": [2],                   # Van
        "forzar_transporte": False,
        "presupuesto_max": 2500.0,
        "num_dias": 3,
        "num_personas": 6,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "08:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 6,
        "max_paradas": 10,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 1.0, "Miradores": 0.9, "Áreas Protegidas": 0.9, "Parques y Bosquecillos": 0.8}
    },
    {
        "nombre": "Escenario #30 - Miradores Mañana Despejada (1d, 2p, Libre, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2],
        "subcategorias_activas_ids": [4],        # Solo Miradores
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 450.0,
        "num_dias": 1,
        "num_personas": 2,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "06:00",
        "hora_fin_dia": "13:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 2,
        "max_paradas": 3,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 1.0, "Miradores": 1.0}
    }
]

def main():
    with app.app_context():
        print("=" * 80)
        print("  INICIANDO ENTRENAMIENTO - CLÚSTER 2: ECOTURISMO Y NATURALEZA")
        print("=" * 80)
        for esc in ESCENARIOS_CLUSTER_2:
            entrenar_escenario_individual(esc)
        print("\n[ÉXITO] Clúster 2 finalizado completamente.")

if __name__ == "__main__":
    main()
