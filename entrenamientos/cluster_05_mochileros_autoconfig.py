# -*- coding: utf-8 -*-
"""
Clúster 5: Mochileros y Auto-Configuración (Escenarios 51 al 60)
Enfoque: 1-2 personas, presupuestos bajos, caminata y switches automáticos habilitados (auto_fechas, auto_rango).
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from entrenamientos.base_entrenador import entrenar_escenario_individual

app = create_app()

ESCENARIOS_CLUSTER_5 = [
    {
        "nombre": "Escenario #51 - Mochilero Auto-Rango Centro (2d, 1p, Caminata, AutoRango)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [1, 2, 3, 7, 8],
        "transporte_ids": [4],
        "forzar_transporte": True,
        "presupuesto_max": 250.0,
        "num_dias": 2,
        "num_personas": 1,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": True,              # Switch activo
        "min_paradas": 2,
        "max_paradas": 15,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.6, "Urbano": 0.7, "Sitios Patrimoniales y Calles Históricas": 0.8, "Plazas": 0.7}
    },
    {
        "nombre": "Escenario #52 - Mochilero Escapada 4 Días Auto (4d, 1p, FullAuto, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 2, 3, 4],
        "subcategorias_activas_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "transporte_ids": [4],
        "forzar_transporte": True,
        "presupuesto_max": 600.0,
        "num_dias": 4,
        "num_personas": 1,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "08:30",
        "hora_fin_dia": "18:00",
        "auto_fechas": True,                     # Switch activo
        "auto_rango_paradas": True,              # Switch activo
        "min_paradas": 2,
        "max_paradas": 15,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.5, "Naturaleza": 0.6, "Urbano": 0.5, "Gastronomía": 0.5}
    },
    {
        "nombre": "Escenario #53 - Pareja Mochilera Presupuesto Mínimo (2d, 2p, Caminata)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [3, 7, 8],
        "transporte_ids": [4],
        "forzar_transporte": True,
        "presupuesto_max": 350.0,
        "num_dias": 2,
        "num_personas": 2,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "17:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 7,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.7, "Urbano": 0.7, "Plazas": 0.8, "Mercados Tradicionales": 0.8}
    },
    {
        "nombre": "Escenario #54 - Mochilero Naturaleza y Miradores (3d, 1p, Libre, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2],
        "subcategorias_activas_ids": [4, 5],
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 450.0,
        "num_dias": 3,
        "num_personas": 1,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "08:00",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 8,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 1.0, "Miradores": 1.0, "Parques y Bosquecillos": 0.8}
    },
    {
        "nombre": "Escenario #55 - Explorador Solitario 5 Días Auto (5d, 1p, AutoRango, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 2, 3, 4],
        "subcategorias_activas_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 800.0,
        "num_dias": 5,
        "num_personas": 1,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "08:30",
        "hora_fin_dia": "18:30",
        "auto_fechas": False,
        "auto_rango_paradas": True,              # Switch activo
        "min_paradas": 2,
        "max_paradas": 15,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.6, "Naturaleza": 0.6, "Urbano": 0.6, "Gastronomía": 0.6}
    },
    {
        "nombre": "Escenario #56 - Mochilero Gastronomía Callejera (2d, 1p, Caminata)",
        "atractivos_ids": [],
        "categorias_activas_ids": [3, 4],
        "subcategorias_activas_ids": [8, 9],
        "transporte_ids": [4],
        "forzar_transporte": True,
        "presupuesto_max": 300.0,
        "num_dias": 2,
        "num_personas": 1,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "10:00",
        "hora_fin_dia": "19:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 6,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Gastronomía": 0.9, "Urbano": 0.7, "Mercados Tradicionales": 1.0, "Gastronomía Tradicional": 0.9}
    },
    {
        "nombre": "Escenario #57 - Descubrimiento Urbano 3 Días Auto (3d, 1p, FullAuto)",
        "atractivos_ids": [],
        "categorias_activas_ids": [3],
        "subcategorias_activas_ids": [7, 8],
        "transporte_ids": [4],
        "forzar_transporte": True,
        "presupuesto_max": 400.0,
        "num_dias": 3,
        "num_personas": 1,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": True,                     # Switch activo
        "auto_rango_paradas": True,              # Switch activo
        "min_paradas": 2,
        "max_paradas": 15,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Urbano": 1.0, "Plazas": 0.9, "Mercados Tradicionales": 0.9}
    },
    {
        "nombre": "Escenario #58 - Pareja Low-Cost 3 Días (3d, 2p, Caminata, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 2, 3],
        "subcategorias_activas_ids": [3, 4, 7],
        "transporte_ids": [4],
        "forzar_transporte": True,
        "presupuesto_max": 550.0,
        "num_dias": 3,
        "num_personas": 2,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 5,
        "max_paradas": 9,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.5, "Naturaleza": 0.6, "Urbano": 0.6}
    },
    {
        "nombre": "Escenario #59 - Mochilero Patrimonio Rápido (1d, 1p, Caminata)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1],
        "subcategorias_activas_ids": [3],
        "transporte_ids": [4],
        "forzar_transporte": True,
        "presupuesto_max": 120.0,
        "num_dias": 1,
        "num_personas": 1,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "16:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 2,
        "max_paradas": 4,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Sitios Patrimoniales y Calles Históricas": 1.0}
    },
    {
        "nombre": "Escenario #60 - Mochilero Integral 4 Días (4d, 1p, Libre, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 2, 3, 4],
        "subcategorias_activas_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 700.0,
        "num_dias": 4,
        "num_personas": 1,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "08:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 6,
        "max_paradas": 12,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.6, "Naturaleza": 0.6, "Urbano": 0.6, "Gastronomía": 0.6}
    }
]

def main():
    with app.app_context():
        print("=" * 80)
        print("  INICIANDO ENTRENAMIENTO - CLÚSTER 5: MOCHILEROS Y AUTO-CONFIGURACIÓN")
        print("=" * 80)
        for esc in ESCENARIOS_CLUSTER_5:
            entrenar_escenario_individual(esc)
        print("\n[ÉXITO] Clúster 5 finalizado completamente.")

if __name__ == "__main__":
    main()
