# -*- coding: utf-8 -*-
"""
Clúster 9: Casos con Atractivos Específicos y Restricciones Fuertes (Escenarios 91 al 100)
Enfoque: Forzado de IDs exactos, presupuestos frontera, horarios recortados y estrés de operadores.

Ajustes y Correcciones Técnicas:
1. IDs representativos válidos de la base de datos para forzar_atractivos=True.
2. Compatibilidad con el nuevo comportamiento de diversidad que preserva combinaciones múltiples en selección forzada.
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from entrenamientos.base_entrenador import entrenar_escenario_individual

app = create_app()

ESCENARIOS_CLUSTER_9 = [
    {
        "nombre": "Escenario #91 - Forzar 3 Íconos del Centro (1d, 2p, Forzar 3 IDs)",
        "atractivos_ids": [1, 4, 6],             # Murillo, San Francisco, Jaén
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [1, 2, 3, 7],
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 350.0,
        "num_dias": 1,
        "num_personas": 2,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "08:30",
        "hora_fin_dia": "16:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 3,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": True,               # Switch activo
        "intereses": {"Cultural": 0.8, "Urbano": 0.8, "Museos": 0.8, "Sitios Patrimoniales y Calles Históricas": 0.9}
    },
    {
        "nombre": "Escenario #92 - Forzar 5 Atractivos Variados (2d, 2p, Forzar 5 IDs, Clima)",
        "atractivos_ids": [1, 4, 9, 20, 22],     # Centro + Mirador + Valle
        "categorias_activas_ids": [1, 2, 3],
        "subcategorias_activas_ids": [1, 2, 3, 4, 6, 7],
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 800.0,
        "num_dias": 2,
        "num_personas": 2,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "08:30",
        "hora_fin_dia": "17:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 5,
        "max_paradas": 5,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": True,               # Switch activo
        "intereses": {"Cultural": 0.7, "Naturaleza": 0.7, "Urbano": 0.7}
    },
    {
        "nombre": "Escenario #93 - Forzar 8 Atractivos en 3 Días (3d, 3p, Forzar 8 IDs, Clima)",
        "atractivos_ids": [1, 4, 6, 9, 20, 22, 23, 28], # 8 representativos
        "categorias_activas_ids": [1, 2, 3],
        "subcategorias_activas_ids": [1, 2, 3, 4, 5, 6, 7],
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 1600.0,
        "num_dias": 3,
        "num_personas": 3,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "08:30",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 8,
        "max_paradas": 8,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": True,               # Switch activo
        "intereses": {"Cultural": 0.8, "Naturaleza": 0.8, "Urbano": 0.7}
    },
    {
        "nombre": "Escenario #94 - Presupuesto Frontera Muy Bajo (2d, 2p, Caminata, Bs 220)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [3, 7],
        "transporte_ids": [4],                   # Caminata
        "forzar_transporte": True,
        "presupuesto_max": 220.0,                # Presupuesto límite
        "num_dias": 2,
        "num_personas": 2,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 5,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.8, "Urbano": 0.8, "Plazas": 0.9, "Sitios Patrimoniales y Calles Históricas": 0.8}
    },
    {
        "nombre": "Escenario #95 - Presupuesto Holgado Premium (2d, 2p, Van, Bs 5000, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 2, 3, 4],
        "subcategorias_activas_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "transporte_ids": [2],                   # Van
        "forzar_transporte": True,
        "presupuesto_max": 5000.0,               # Presupuesto holgado
        "num_dias": 2,
        "num_personas": 2,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "08:00",
        "hora_fin_dia": "19:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 6,
        "max_paradas": 10,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.9, "Naturaleza": 0.9, "Urbano": 0.9, "Gastronomía": 0.9}
    },
    {
        "nombre": "Escenario #96 - Ventana Estrecha Mañana 3h (1d, 1p, Taxi, 09:00-12:00)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1],
        "subcategorias_activas_ids": [1],        # Museos
        "transporte_ids": [1],                   # Taxi
        "forzar_transporte": True,
        "presupuesto_max": 180.0,
        "num_dias": 1,
        "num_personas": 1,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "12:00",                 # Solo 3 horas
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 2,
        "max_paradas": 3,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Museos": 1.0}
    },
    {
        "nombre": "Escenario #97 - Ventana Estrecha Tarde 3h (1d, 2p, Taxi, 15:00-18:00)",
        "atractivos_ids": [],
        "categorias_activas_ids": [3],
        "subcategorias_activas_ids": [7],        # Plazas
        "transporte_ids": [1],                   # Taxi
        "forzar_transporte": True,
        "presupuesto_max": 280.0,
        "num_dias": 1,
        "num_personas": 2,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "15:00",
        "hora_fin_dia": "18:00",                 # Solo 3 horas
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 2,
        "max_paradas": 3,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Urbano": 1.0, "Plazas": 1.0}
    },
    {
        "nombre": "Escenario #98 - Forzar 6 Sitios de Naturaleza (2d, 4p, Van, Forzar 6 IDs, Clima)",
        "atractivos_ids": [9, 20, 22, 23, 28, 29], # 6 de naturaleza
        "categorias_activas_ids": [2],
        "subcategorias_activas_ids": [4, 5, 6],
        "transporte_ids": [2],                   # Van
        "forzar_transporte": True,
        "presupuesto_max": 1800.0,
        "num_dias": 2,
        "num_personas": 4,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "08:00",
        "hora_fin_dia": "17:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 6,
        "max_paradas": 6,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": True,               # Switch activo
        "intereses": {"Naturaleza": 1.0, "Miradores": 1.0, "Áreas Protegidas": 1.0, "Parques y Bosquecillos": 0.8}
    },
    {
        "nombre": "Escenario #99 - Full Switches Activos 3 Días (3d, 2p, FullAuto, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 2, 3, 4],
        "subcategorias_activas_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "transporte_ids": [1, 4],
        "forzar_transporte": False,
        "presupuesto_max": 1200.0,
        "num_dias": 3,
        "num_personas": 2,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": True,                     # Switch activo
        "auto_rango_paradas": True,              # Switch activo
        "min_paradas": 2,
        "max_paradas": 15,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.7, "Naturaleza": 0.7, "Urbano": 0.7, "Gastronomía": 0.7}
    },
    {
        "nombre": "Escenario #100 - Forzar 12 Atractivos en 4 Días (4d, 4p, Van, Forzar 12 IDs, Clima)",
        "atractivos_ids": [1, 4, 6, 9, 20, 22, 23, 28, 29, 31, 2, 3], # 12 representativos
        "categorias_activas_ids": [1, 2, 3, 4],
        "subcategorias_activas_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "transporte_ids": [2],                   # Van
        "forzar_transporte": True,
        "presupuesto_max": 3800.0,
        "num_dias": 4,
        "num_personas": 4,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "08:00",
        "hora_fin_dia": "18:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 12,
        "max_paradas": 12,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": True,               # Switch activo
        "intereses": {"Cultural": 0.8, "Naturaleza": 0.8, "Urbano": 0.8, "Gastronomía": 0.7}
    }
]

def main():
    with app.app_context():
        print("=" * 80)
        print("  INICIANDO ENTRENAMIENTO - CLÚSTER 9: ATRACTIVOS FORZADOS Y RESTRICCIONES")
        print("=" * 80)
        for esc in ESCENARIOS_CLUSTER_9:
            entrenar_escenario_individual(esc)
        print("\n[ÉXITO] Clúster 9 finalizado completamente.")

if __name__ == "__main__":
    main()
