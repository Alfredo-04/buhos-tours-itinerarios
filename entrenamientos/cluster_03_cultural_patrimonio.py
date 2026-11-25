# -*- coding: utf-8 -*-
"""
Clúster 3: Cultural Profundo, Museos y Patrimonio (Escenarios 31 al 40)
Enfoque: Visitas prolongadas en interiores; alta sensibilidad a horarios comerciales y patrimoniales.
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from entrenamientos.base_entrenador import entrenar_escenario_individual

app = create_app()

ESCENARIOS_CLUSTER_3 = [
    {
        "nombre": "Escenario #31 - Maratón de Museos 3 Días (3d, 2p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1],
        "subcategorias_activas_ids": [1],        # Solo Museos
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 900.0,
        "num_dias": 3,
        "num_personas": 2,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "17:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 6,
        "max_paradas": 11,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Museos": 1.0}
    },
    {
        "nombre": "Escenario #32 - Investigador Histórico 4 Días (4d, 1p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1],
        "subcategorias_activas_ids": [1, 2, 3],  # Museos, Iglesias, Sitios
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 1200.0,
        "num_dias": 4,
        "num_personas": 1,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 7,
        "max_paradas": 13,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Museos": 1.0, "Iglesias y Templos": 0.9, "Sitios Patrimoniales y Calles Históricas": 1.0}
    },
    {
        "nombre": "Escenario #33 - Arte Sacro y Conventos (2d, 2p, Caminata)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1],
        "subcategorias_activas_ids": [2],        # Solo Iglesias y Conventos
        "transporte_ids": [4],
        "forzar_transporte": True,
        "presupuesto_max": 550.0,
        "num_dias": 2,
        "num_personas": 2,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "09:30",
        "hora_fin_dia": "16:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 6,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Iglesias y Templos": 1.0}
    },
    {
        "nombre": "Escenario #34 - Familia Museos Dinámicos (3d, 4p, Taxi)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [1, 7],     # Museos, Plazas
        "transporte_ids": [1],
        "forzar_transporte": True,
        "presupuesto_max": 1600.0,
        "num_dias": 3,
        "num_personas": 4,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "10:00",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 5,
        "max_paradas": 8,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.8, "Urbano": 0.7, "Museos": 0.9, "Plazas": 0.8}
    },
    {
        "nombre": "Escenario #35 - Etnografía y Costumbres 2 Días (2d, 3p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [1, 8],     # Museos, Mercados Tradicionales
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 800.0,
        "num_dias": 2,
        "num_personas": 3,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 7,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.9, "Urbano": 0.7, "Museos": 1.0, "Mercados Tradicionales": 0.8}
    },
    {
        "nombre": "Escenario #36 - Gran Circuito Cultural 5 Días (5d, 2p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1],
        "subcategorias_activas_ids": [1, 2, 3],  # Museos, Iglesias, Sitios
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 2000.0,
        "num_dias": 5,
        "num_personas": 2,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 8,
        "max_paradas": 15,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Museos": 0.9, "Iglesias y Templos": 0.8, "Sitios Patrimoniales y Calles Históricas": 0.9}
    },
    {
        "nombre": "Escenario #37 - Breve Cultural Ejecutivo (1d, 1p, Taxi)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1],
        "subcategorias_activas_ids": [1, 3],     # Museos, Sitios
        "transporte_ids": [1],
        "forzar_transporte": True,
        "presupuesto_max": 300.0,
        "num_dias": 1,
        "num_personas": 1,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "14:00",
        "hora_fin_dia": "19:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 2,
        "max_paradas": 4,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Museos": 0.8, "Sitios Patrimoniales y Calles Históricas": 0.8}
    },
    {
        "nombre": "Escenario #38 - Delegación Académica en Van (4d, 8p, Van)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1],
        "subcategorias_activas_ids": [1, 3],     # Museos, Sitios
        "transporte_ids": [2],                   # Van
        "forzar_transporte": True,
        "presupuesto_max": 3500.0,
        "num_dias": 4,
        "num_personas": 8,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "08:30",
        "hora_fin_dia": "17:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 7,
        "max_paradas": 14,
        "permitir_multiples_vehiculos": False,   # 8 <= Van cap 10
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Museos": 1.0, "Sitios Patrimoniales y Calles Históricas": 1.0}
    },
    {
        "nombre": "Escenario #39 - Calle Jaén Monotemático (1d, 2p, Caminata)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1],
        "subcategorias_activas_ids": [1, 3],     # Museos, Sitios
        "transporte_ids": [4],
        "forzar_transporte": True,
        "presupuesto_max": 220.0,
        "num_dias": 1,
        "num_personas": 2,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "15:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 5,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Museos": 1.0, "Sitios Patrimoniales y Calles Históricas": 0.9}
    },
    {
        "nombre": "Escenario #40 - Arqueología y Arte Republicano (3d, 2p, Libre)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1],
        "subcategorias_activas_ids": [1, 3],     # Museos, Sitios
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 1100.0,
        "num_dias": 3,
        "num_personas": 2,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 6,
        "max_paradas": 9,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Museos": 1.0, "Sitios Patrimoniales y Calles Históricas": 0.9}
    }
]

def main():
    with app.app_context():
        print("=" * 80)
        print("  INICIANDO ENTRENAMIENTO - CLÚSTER 3: CULTURAL PROFUNDO Y PATRIMONIO")
        print("=" * 80)
        for esc in ESCENARIOS_CLUSTER_3:
            entrenar_escenario_individual(esc)
        print("\n[ÉXITO] Clúster 3 finalizado completamente.")

if __name__ == "__main__":
    main()
