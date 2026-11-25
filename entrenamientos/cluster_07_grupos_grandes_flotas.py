# -*- coding: utf-8 -*-
"""
Clúster 7: Grupos Grandes y Múltiples Vehículos (Escenarios 71 al 80)
Enfoque: 8 a 35 personas, minibuses, vans o flotas de taxis con switch múltiple activo.
Ajuste técnico: Presupuestos ajustados a umbrales viables para costear flotas y entradas.
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from entrenamientos.base_entrenador import entrenar_escenario_individual

app = create_app()

ESCENARIOS_CLUSTER_7 = [
    {
        "nombre": "Escenario #71 - Promoción Escolar 2 Días (2d, 25p, 2 Minibuses, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 2],
        "subcategorias_activas_ids": [1, 5],     # Museos, Parques
        "transporte_ids": [3],                   # Minibús (capacidad 20 -> requiere 2)
        "forzar_transporte": True,
        "presupuesto_max": 9500.0,               # Ajustado de 7000 a 9500 para cubrir 2 minibuses x 2 días + 25 entradas
        "num_dias": 2,
        "num_personas": 25,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "08:30",
        "hora_fin_dia": "17:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 5,
        "max_paradas": 8,
        "permitir_multiples_vehiculos": True,    # Switch activo
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.8, "Naturaleza": 0.8, "Parques y Bosquecillos": 0.9}
    },
    {
        "nombre": "Escenario #72 - Delegación Turística en Taxis (3d, 12p, 3 Taxis)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [1, 3, 7],  # Museos, Sitios, Plazas
        "transporte_ids": [1],                   # Taxi (capacidad 4 -> requiere 3 taxis)
        "forzar_transporte": True,
        "presupuesto_max": 7500.0,
        "num_dias": 3,
        "num_personas": 12,
        "fecha_inicio": "2026-11-20",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 6,
        "max_paradas": 10,
        "permitir_multiples_vehiculos": True,    # Switch activo
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.9, "Urbano": 0.8, "Sitios Patrimoniales y Calles Históricas": 0.9}
    },
    {
        "nombre": "Escenario #73 - Grupo Parroquial 2 Días (2d, 18p, 1 Minibús)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1],
        "subcategorias_activas_ids": [2],        # Iglesias
        "transporte_ids": [3],                   # Minibús (capacidad 20 >= 18)
        "forzar_transporte": True,
        "presupuesto_max": 5500.0,
        "num_dias": 2,
        "num_personas": 18,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "08:30",
        "hora_fin_dia": "17:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 7,
        "permitir_multiples_vehiculos": False,   # 18 <= Minibús cap 20
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Iglesias y Templos": 1.0}
    },
    {
        "nombre": "Escenario #74 - Delegación Extranjera Vans (4d, 16p, 2 Vans, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 2, 3],
        "subcategorias_activas_ids": [1, 2, 3, 4, 5, 6, 7],
        "transporte_ids": [2],                   # Van (capacidad 10 -> requiere 2 vans)
        "forzar_transporte": True,
        "presupuesto_max": 14000.0,
        "num_dias": 4,
        "num_personas": 16,
        "fecha_inicio": "2026-11-21",
        "hora_inicio_dia": "08:30",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 8,
        "max_paradas": 14,
        "permitir_multiples_vehiculos": True,    # Switch activo
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.8, "Naturaleza": 0.8, "Urbano": 0.8}
    },
    {
        "nombre": "Escenario #75 - Grupo Corporativo 1 Día (1d, 15p, 1 Minibús, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2, 3],
        "subcategorias_activas_ids": [4, 7],     # Miradores, Plazas
        "transporte_ids": [3],                   # Minibús (15 <= 20)
        "forzar_transporte": True,
        "presupuesto_max": 5000.0,
        "num_dias": 1,
        "num_personas": 15,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 5,
        "permitir_multiples_vehiculos": False,
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 0.8, "Urbano": 0.8, "Miradores": 1.0}
    },
    {
        "nombre": "Escenario #76 - Grupo Cultural Grande 3 Días (3d, 20p, 1 Minibús)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1],
        "subcategorias_activas_ids": [1, 3],     # Museos, Sitios
        "transporte_ids": [3],                   # Minibús (20 <= 20)
        "forzar_transporte": True,
        "presupuesto_max": 9500.0,
        "num_dias": 3,
        "num_personas": 20,
        "fecha_inicio": "2026-11-22",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "17:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 6,
        "max_paradas": 11,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 1.0, "Museos": 1.0, "Sitios Patrimoniales y Calles Históricas": 0.9}
    },
    {
        "nombre": "Escenario #77 - Ecoturismo Delegación 2 Días (2d, 14p, 2 Vans, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2],
        "subcategorias_activas_ids": [4, 6],     # Miradores, Áreas
        "transporte_ids": [2],                   # Van (capacidad 10 -> requiere 2 vans)
        "forzar_transporte": True,
        "presupuesto_max": 7500.0,
        "num_dias": 2,
        "num_personas": 14,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "08:00",
        "hora_fin_dia": "17:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 7,
        "permitir_multiples_vehiculos": True,    # Switch activo
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 1.0, "Áreas Protegidas": 1.0}
    },
    {
        "nombre": "Escenario #78 - Conferencia Internacional (2d, 10p, 1 Van)",
        "atractivos_ids": [],
        "categorias_activas_ids": [1, 3],
        "subcategorias_activas_ids": [3, 7],     # Sitios, Plazas
        "transporte_ids": [2],                   # Van (capacidad 10 >= 10)
        "forzar_transporte": True,
        "presupuesto_max": 5000.0,
        "num_dias": 2,
        "num_personas": 10,
        "fecha_inicio": "2026-11-23",
        "hora_inicio_dia": "14:00",
        "hora_fin_dia": "19:30",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 3,
        "max_paradas": 6,
        "permitir_multiples_vehiculos": False,
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Cultural": 0.8, "Urbano": 0.9, "Sitios Patrimoniales y Calles Históricas": 0.9}
    },
    {
        "nombre": "Escenario #79 - Contingente Juvenil en Vans (3d, 18p, 2 Vans, Clima)",
        "atractivos_ids": [],
        "categorias_activas_ids": [2, 3],
        "subcategorias_activas_ids": [4, 7],     # Miradores, Plazas
        "transporte_ids": [2],                   # Van (capacidad 10 -> requiere 2 vans)
        "forzar_transporte": True,
        "presupuesto_max": 10500.0,
        "num_dias": 3,
        "num_personas": 18,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "08:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 6,
        "max_paradas": 10,
        "permitir_multiples_vehiculos": True,    # Switch activo
        "usar_clima": True,
        "forzar_atractivos": False,
        "intereses": {"Naturaleza": 0.9, "Urbano": 0.7, "Miradores": 0.9}
    },
    {
        "nombre": "Escenario #80 - Gran Grupo Gastronómico (2d, 30p, 2 Minibuses)",
        "atractivos_ids": [],
        "categorias_activas_ids": [3, 4],
        "subcategorias_activas_ids": [7, 8, 9],  # Plazas, Mercados, Gastronomía
        "transporte_ids": [3],                   # Minibús (capacidad 20 -> requiere 2 minibuses)
        "forzar_transporte": True,
        "presupuesto_max": 12500.0,              # Ajustado para 30 personas x 2 días
        "num_dias": 2,
        "num_personas": 30,
        "fecha_inicio": "2026-11-24",
        "hora_inicio_dia": "10:00",
        "hora_fin_dia": "18:00",
        "auto_fechas": False,
        "auto_rango_paradas": False,
        "min_paradas": 4,
        "max_paradas": 8,
        "permitir_multiples_vehiculos": True,    # Switch activo
        "usar_clima": False,
        "forzar_atractivos": False,
        "intereses": {"Gastronomía": 1.0, "Urbano": 0.8, "Gastronomía Tradicional": 1.0}
    }
]

def main():
    with app.app_context():
        print("=" * 80)
        print("  INICIANDO ENTRENAMIENTO - CLÚSTER 7: GRUPOS GRANDES Y MÚLTIPLES VEHÍCULOS")
        print("=" * 80)
        for esc in ESCENARIOS_CLUSTER_7:
            entrenar_escenario_individual(esc)
        print("\n[ÉXITO] Clúster 7 finalizado completamente.")

if __name__ == "__main__":
    main()
