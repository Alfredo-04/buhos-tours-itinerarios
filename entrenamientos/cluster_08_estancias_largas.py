# -*- coding: utf-8 -*-
"""
Clúster 8: Estancias Largas e Inmersivas (Escenarios 81 al 90)
Enfoque: 6 a 12 días, alta cantidad de paradas (10 a 25), catálogos completos.
Ajuste técnico: Clima controlado en días > 5 para evitar sesgos por límites del pronóstico.
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from entrenamientos.base_entrenador import entrenar_escenario_individual

app = create_app()

ESCENARIOS_CLUSTER_8 = [
    {
        "nombre": "Escenario #81 - La Paz Integral 7 Días Pareja (7d, 2p, Libre, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 2, 3, 4],
        "subcategorias_activas_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 5500.0,
        "num_dias": 7,
        "num_personas": 2,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "08:30",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 12,
        "max_paradas": 20,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.8, "Naturaleza": 0.8, "Urbano": 0.7, "Gastronomía": 0.7}
    },
    {
        "nombre": "Escenario #82 - Inmersión Cultural 8 Días (8d, 2p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [1, 2, 3, 7],
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 5000.0,
        "num_dias": 8,
        "num_personas": 2,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "17:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 14,
        "max_paradas": 22,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Urbano": 0.8, "Museos": 1.0, "Sitios Patrimoniales y Calles Históricas": 0.9}
    },
    {
        "nombre": "Escenario #83 - Expedición Naturaleza 6 Días (6d, 4p, Van, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2],
        "subcategorias_activas_ids": [4, 5, 6],
        "transporte_ids": [2],                   # Van
        "forzar_transporte": True,
        "presupuesto_max": 6500.0,
        "num_dias": 6,
        "num_personas": 4,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "08:00",
        "hora_fin_dia": "17:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 10,
        "max_paradas": 18,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 1.0, "Áreas Protegidas": 1.0, "Miradores": 0.9, "Parques y Bosquecillos": 0.8}
    },
    {
        "nombre": "Escenario #84 - Vacaciones Completas 10 Días (10d, 3p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 2, 3, 4],
        "subcategorias_activas_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "transporte_ids": [1, 2],
        "forzar_transporte": False,
        "presupuesto_max": 9000.0,
        "num_dias": 10,
        "num_personas": 3,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "08:30",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 15,
        "max_paradas": 25,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,                     # Desactivado clima para estabilidad en 10 días
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.7, "Naturaleza": 0.7, "Urbano": 0.7, "Gastronomía": 0.7}
    },
    {
        "nombre": "Escenario #85 - Gran Tour Gastronomía y Cultura (7d, 2p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 4],
        "subcategorias_activas_ids": [1, 3, 8, 9],
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 6000.0,
        "num_dias": 7,
        "num_personas": 2,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "09:30",
        "hora_fin_dia": "18:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 12,
        "max_paradas": 18,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.8, "Gastronomía": 1.0, "Gastronomía Tradicional": 1.0, "Museos": 0.8}
    },
    {
        "nombre": "Escenario #86 - Familia Vacaciones 8 Días (8d, 4p, Van)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 2, 3],
        "subcategorias_activas_ids": [1, 3, 4, 5, 7],
        "transporte_ids": [2],                   # Van
        "forzar_transporte": True,
        "presupuesto_max": 8500.0,
        "num_dias": 8,
        "num_personas": 4,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "09:30",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 12,
        "max_paradas": 20,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,                     # Desactivado clima para estabilidad en 8 días
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.7, "Naturaleza": 0.8, "Urbano": 0.7, "Parques y Bosquecillos": 0.9}
    },
    {
        "nombre": "Escenario #87 - Gran Circuito Paceño 12 Días (12d, 2p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 2, 3, 4],
        "subcategorias_activas_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 10000.0,
        "num_dias": 12,
        "num_personas": 2,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "08:30",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 18,
        "max_paradas": 28,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,                     # Desactivado clima en 12 días
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.8, "Naturaleza": 0.8, "Urbano": 0.8, "Gastronomía": 0.8}
    },
    {
        "nombre": "Escenario #88 - Ruta Andina 6 Días Amigos (6d, 5p, Van, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 2],
        "subcategorias_activas_ids": [3, 4, 6],  # Sitios, Miradores, Áreas
        "transporte_ids": [2],                   # Van
        "forzar_transporte": True,
        "presupuesto_max": 7500.0,
        "num_dias": 6,
        "num_personas": 5,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "08:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 10,
        "max_paradas": 16,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.8, "Naturaleza": 0.9, "Miradores": 1.0, "Áreas Protegidas": 0.9}
    },
    {
        "nombre": "Escenario #89 - Sabores y Paisajes 7 Días (7d, 3p, Libre, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2, 4],
        "subcategorias_activas_ids": [4, 6, 9],  # Miradores, Áreas, Gastronomía
        "transporte_ids": [1, 2],
        "forzar_transporte": False,
        "presupuesto_max": 6800.0,
        "num_dias": 7,
        "num_personas": 3,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 11,
        "max_paradas": 17,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 0.9, "Gastronomía": 0.9, "Áreas Protegidas": 0.9, "Gastronomía Tradicional": 0.9}
    },
    {
        "nombre": "Escenario #90 - Exploración Urbana 7 Días (7d, 2p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [3],
        "subcategorias_activas_ids": [7, 8],     # Plazas, Mercados
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 4500.0,
        "num_dias": 7,
        "num_personas": 2,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "18:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 12,
        "max_paradas": 19,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Urbano": 1.0, "Plazas": 0.9, "Mercados Tradicionales": 0.9}
    }
]

def main():
    with app.app_context():
        print("=" * 80)
        print("  INICIANDO ENTRENAMIENTO - CLÚSTER 8: ESTANCIAS LARGAS E INMERSIVAS")
        print("=" * 80)
        for esc in ESCENARIOS_CLUSTER_8:
            entrenar_escenario_individual(esc)
        print("\n[ÉXITO] Clúster 8 finalizado completamente.")

if __name__ == "__main__":
    main()
