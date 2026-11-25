# -*- coding: utf-8 -*-
"""
Clúster 6: Familias y Ritmo Relajado (Escenarios 61 al 70)
Enfoque: 3 a 5 personas, ventanas horarias cómodas (10:00 - 16:30), van o taxi exclusivo.
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from entrenamientos.base_entrenador import entrenar_escenario_individual

app = create_app()

ESCENARIOS_CLUSTER_6 = [
    {
        "nombre": "Escenario #61 - Familia con Niños 2 Días Centro (2d, 4p, Taxi)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [1, 7],     # Museos, Plazas
        "transporte_ids": [1],                   # Taxi
        "forzar_transporte": True,
        "presupuesto_max": 1400.0,
        "num_dias": 2,
        "num_personas": 4,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "10:00",
        "hora_fin_dia": "16:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 6,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.7, "Urbano": 0.8, "Museos": 0.8, "Plazas": 0.8}
    },
    {
        "nombre": "Escenario #62 - Familia Parques y Naturaleza (3d, 5p, Van, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2],
        "subcategorias_activas_ids": [4, 5],     # Miradores, Parques
        "transporte_ids": [2],                   # Van
        "forzar_transporte": True,
        "presupuesto_max": 2400.0,
        "num_dias": 3,
        "num_personas": 5,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "09:30",
        "hora_fin_dia": "16:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 7,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 1.0, "Parques y Bosquecillos": 1.0, "Miradores": 0.8}
    },
    {
        "nombre": "Escenario #63 - Ritmo Cómodo Adultos Mayores (3d, 3p, Taxi)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [1, 3, 7],  # Museos, Sitios, Plazas
        "transporte_ids": [1],                   # Taxi
        "forzar_transporte": True,
        "presupuesto_max": 1900.0,
        "num_dias": 3,
        "num_personas": 3,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "10:00",
        "hora_fin_dia": "16:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 6,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.9, "Urbano": 0.6, "Museos": 0.9, "Plazas": 0.7}
    },
    {
        "nombre": "Escenario #64 - Fin de Semana Familiar Completo (2d, 5p, Van, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 2],
        "subcategorias_activas_ids": [1, 5],     # Museos, Parques
        "transporte_ids": [2],                   # Van
        "forzar_transporte": True,
        "presupuesto_max": 2000.0,
        "num_dias": 2,
        "num_personas": 5,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 5,
        "max_paradas": 8,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.6, "Naturaleza": 0.8, "Parques y Bosquecillos": 0.9}
    },
    {
        "nombre": "Escenario #65 - Familia Valles del Sur en Van (1d, 5p, Van, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2],
        "subcategorias_activas_ids": [6],        # Áreas Protegidas
        "transporte_ids": [2],                   # Van
        "forzar_transporte": True,
        "presupuesto_max": 1200.0,
        "num_dias": 1,
        "num_personas": 5,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "16:00",
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
        "nombre": "Escenario #66 - Paseo Familiar y Almuerzo Típico (1d, 4p, Taxi)",
        "atractivos_ids": [],
        "categorias_activas_ids": [3, 4],
        "subcategorias_activas_ids": [7, 9],     # Plazas, Gastronomía
        "transporte_ids": [1],                   # Taxi
        "forzar_transporte": True,
        "presupuesto_max": 800.0,
        "num_dias": 1,
        "num_personas": 4,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "10:00",
        "hora_fin_dia": "16:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 2,
        "max_paradas": 4,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Gastronomía": 0.9, "Urbano": 0.8, "Plazas": 0.8, "Gastronomía Tradicional": 0.9}
    },
    {
        "nombre": "Escenario #67 - Familia 4 Días Vacaciones (4d, 4p, Libre, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 2, 3],
        "subcategorias_activas_ids": [1, 2, 3, 4, 5, 6, 7],
        "transporte_ids": [1, 2],                # Taxi, Van
        "forzar_transporte": False,
        "presupuesto_max": 3200.0,
        "num_dias": 4,
        "num_personas": 4,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "09:30",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 6,
        "max_paradas": 10,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.7, "Naturaleza": 0.8, "Urbano": 0.7}
    },
    {
        "nombre": "Escenario #68 - Circuito Panorámico Familiar (2d, 4p, Taxi, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2, 3],
        "subcategorias_activas_ids": [4, 7],     # Miradores, Plazas
        "transporte_ids": [1],                   # Taxi
        "forzar_transporte": True,
        "presupuesto_max": 1500.0,
        "num_dias": 2,
        "num_personas": 4,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "09:30",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 7,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 0.8, "Urbano": 0.8, "Miradores": 0.9, "Plazas": 0.7}
    },
    {
        "nombre": "Escenario #69 - Familia Museos y Tradición (3d, 4p, Van)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 4],
        "subcategorias_activas_ids": [1, 9],     # Museos, Gastronomía
        "transporte_ids": [2],                   # Van
        "forzar_transporte": True,
        "presupuesto_max": 2200.0,
        "num_dias": 3,
        "num_personas": 4,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "10:00",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 5,
        "max_paradas": 8,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.8, "Gastronomía": 0.9, "Museos": 0.8, "Gastronomía Tradicional": 0.9}
    },
    {
        "nombre": "Escenario #70 - Escapada Relajada 1 Día (1d, 3p, Taxi)",
        "atractivos_ids": [],
        "categorias_activas_ids": [3],
        "subcategorias_activas_ids": [7],        # Solo Plazas
        "transporte_ids": [1],                   # Taxi
        "forzar_transporte": True,
        "presupuesto_max": 700.0,
        "num_dias": 1,
        "num_personas": 3,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "10:30",
        "hora_fin_dia": "16:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 2,
        "max_paradas": 3,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Urbano": 1.0, "Plazas": 1.0}
    }
]

def main():
    with app.app_context():
        print("=" * 80)
        print("  INICIANDO ENTRENAMIENTO - CLÚSTER 6: FAMILIAS Y RITMO RELAJADO")
        print("=" * 80)
        for esc in ESCENARIOS_CLUSTER_6:
            entrenar_escenario_individual(esc)
        print("\n[ÉXITO] Clúster 6 finalizado completamente.")

if __name__ == "__main__":
    main()
