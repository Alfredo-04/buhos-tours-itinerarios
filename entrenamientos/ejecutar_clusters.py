# -*- coding: utf-8 -*-
"""
Lanzador Flexible de Entrenamiento por Clústeres (Búhos Tours).
Permite ejecutar uno o varios clústeres en secuencia continua.

Uso:
  python entrenamientos/ejecutar_clusters.py 1 2          # Ejecuta Clúster 1 y 2
  python entrenamientos/ejecutar_clusters.py 1 2 3        # Ejecuta Clúster 1, 2 y 3
  python entrenamientos/ejecutar_clusters.py              # Si no se pasan argumentos, corre 1 y 2 por defecto
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from entrenamientos.base_entrenador import entrenar_escenario_individual

# Importar las listas de escenarios de cada cluster
from entrenamientos.cluster_01_urbanos_centro import ESCENARIOS_CLUSTER_1
from entrenamientos.cluster_02_ecoturismo_naturaleza import ESCENARIOS_CLUSTER_2
from entrenamientos.cluster_03_cultural_patrimonio import ESCENARIOS_CLUSTER_3
from entrenamientos.cluster_04_gastronomia_mercados import ESCENARIOS_CLUSTER_4
from entrenamientos.cluster_05_mochileros_autoconfig import ESCENARIOS_CLUSTER_5
from entrenamientos.cluster_06_familias_ritmo_relajado import ESCENARIOS_CLUSTER_6
from entrenamientos.cluster_07_grupos_grandes_flotas import ESCENARIOS_CLUSTER_7
from entrenamientos.cluster_08_estancias_largas import ESCENARIOS_CLUSTER_8
from entrenamientos.cluster_09_atractivos_forzados_restricciones import ESCENARIOS_CLUSTER_9

MAPA_CLUSTERS = {
    1: ("CLÚSTER 1: Express Urbanos y Centro Histórico (Escenarios 11 al 20)", ESCENARIOS_CLUSTER_1),
    2: ("CLÚSTER 2: Ecoturismo y Naturaleza (Escenarios 21 al 30)", ESCENARIOS_CLUSTER_2),
    3: ("CLÚSTER 3: Cultural Profundo y Patrimonio (Escenarios 31 al 40)", ESCENARIOS_CLUSTER_3),
    4: ("CLÚSTER 4: Gastronomía Tradicional y Mercados (Escenarios 41 al 50)", ESCENARIOS_CLUSTER_4),
    5: ("CLÚSTER 5: Mochileros y Auto-Configuración (Escenarios 51 al 60)", ESCENARIOS_CLUSTER_5),
    6: ("CLÚSTER 6: Familias y Ritmo Relajado (Escenarios 61 al 70)", ESCENARIOS_CLUSTER_6),
    7: ("CLÚSTER 7: Grupos Grandes y Múltiples Vehículos (Escenarios 71 al 80)", ESCENARIOS_CLUSTER_7),
    8: ("CLÚSTER 8: Estancias Largas e Inmersivas (Escenarios 81 al 90)", ESCENARIOS_CLUSTER_8),
    9: ("CLÚSTER 9: Atractivos Forzados y Restricciones (Escenarios 91 al 100)", ESCENARIOS_CLUSTER_9),
}

app = create_app()

def main():
    # Obtener los números de clusters pasados por consola
    args = sys.argv[1:]
    if not args:
        clusters_a_ejecutar = [1, 2] # Por defecto los 2 primeros
    else:
        clusters_a_ejecutar = []
        for a in args:
            try:
                num = int(a)
                if num in MAPA_CLUSTERS:
                    clusters_a_ejecutar.append(num)
                else:
                    print(f"[WARN] Clúster {num} no existe (rango válido: 1 al 9). Ignorado.")
            except ValueError:
                pass

    if not clusters_a_ejecutar:
        print("[ERROR] No se especificó ningún clúster válido. Finalizando.")
        return

    print("=" * 80)
    print(f"  LANZADOR DE ENTRENAMIENTO - CLÚSTERES A EJECUTAR: {clusters_a_ejecutar}")
    print("=" * 80)

    with app.app_context():
        for num_c in clusters_a_ejecutar:
            nombre, lista_esc = MAPA_CLUSTERS[num_c]
            print("\n" + "#" * 80)
            print(f"  INICIANDO {nombre}")
            print("#" * 80)

            for esc in lista_esc:
                entrenar_escenario_individual(esc)

            print(f"\n[OK] Finalizado exitosamente: {nombre}")

    print("\n" + "=" * 80)
    print("  TODOS LOS CLÚSTERES SELECCIONADOS HAN SIDO COMPLETADOS CON ÉXITO")
    print("=" * 80)

if __name__ == "__main__":
    main()
