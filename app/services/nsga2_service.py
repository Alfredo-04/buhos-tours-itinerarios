import time
from math import radians, sin, cos, sqrt, atan2
from typing import Any
import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.sampling.rnd import PermutationRandomSampling
from pymoo.operators.crossover.ox import OrderCrossover
from pymoo.operators.mutation.inversion import InversionMutation
from pymoo.optimize import minimize


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia ortodrómica en kilómetros entre dos coordenadas geográficas
    utilizando la fórmula de Haversine.

    :param lat1: Latitud del punto 1 en grados decimales
    :param lon1: Longitud del punto 1 en grados decimales
    :param lat2: Latitud del punto 2 en grados decimales
    :param lon2: Longitud del punto 2 en grados decimales
    :return: Distancia en kilómetros
    """
    R = 6371.0  # Radio medio de la Tierra en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2.0) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2.0) ** 2
    c = 2.0 * atan2(sqrt(a), sqrt(1.0 - a))
    return R * c


class ItinerarioProblem(Problem):
    """
    Problema de optimización multiobjetivo para generación de itinerarios turísticos.
    
    Variables de decisión:
        Permutación de índices de atractivos seleccionados.
        
    Objetivos:
        1. Maximizar afinidad turística (se minimiza -afinidad).
        2. Minimizar tiempo total de recorrido (visitas + traslados).
        
    Restricciones:
        1. Tiempo total <= tiempo_disponible_horas * 60.
        2. Costo total <= presupuesto_max.
    """

    def __init__(
        self,
        atractivos: list[dict[str, Any]],
        transporte_optimo: dict[str, Any],
        presupuesto_max: float,
        tiempo_disponible_horas: float,
        intereses: dict[str, float],
    ):
        n_atractivos = len(atractivos)
        super().__init__(
            n_var=n_atractivos,
            n_obj=2,
            n_ieq_constr=2,
            xl=0,
            xu=n_atractivos - 1,
            vtype=int,
        )
        self.atractivos = atractivos
        self.transporte = transporte_optimo
        self.presupuesto_max = float(presupuesto_max)
        self.tiempo_max_min = float(tiempo_disponible_horas) * 60.0
        self.intereses = intereses
        self.n_atractivos = n_atractivos

        # Precalcular afinidad individual y costo de entrada de cada atractivo:
        # Se evalúa afinidad buscando por nombre de subcategoría o heredando el peso de la categoría padre
        self.afinidad_individual = np.array([
            float(self.intereses.get(a.get("subcategoria", ""), self.intereses.get(a.get("categoria", ""), 0.0)))
            for a in self.atractivos
        ], dtype=float)

        self.costos_entradas = np.array([
            float(a.get("costo_entrada", 0.0) or 0.0)
            for a in self.atractivos
        ], dtype=float)

        self.tiempos_visitas = np.array([
            float(a.get("tiempo_visita", 60) or 60)
            for a in self.atractivos
        ], dtype=float)

        # Precalcular matriz de distancias y tiempos de traslado entre todos los pares
        self.distancias_matriz = np.zeros((n_atractivos, n_atractivos), dtype=float)
        velocidad = max(1.0, float(self.transporte.get("velocidad_promedio_kmh", 30.0) or 30.0))
        
        for i in range(n_atractivos):
            lat_i = float(self.atractivos[i]["lat"])
            lon_i = float(self.atractivos[i]["lon"])
            for j in range(n_atractivos):
                if i != j:
                    lat_j = float(self.atractivos[j]["lat"])
                    lon_j = float(self.atractivos[j]["lon"])
                    self.distancias_matriz[i, j] = haversine_km(lat_i, lon_i, lat_j, lon_j)

        # Matriz de tiempos de traslado en minutos
        self.tiempos_traslado_matriz = (self.distancias_matriz / velocidad) * 60.0
        self.costo_por_tramo = float(self.transporte.get("costo_por_tramo", 0.0) or 0.0)

    def _evaluate(self, x: np.ndarray, out: dict[str, Any], *args: Any, **kwargs: Any) -> None:
        """
        Evalúa una población de individuos (permutaciones de atractivos).
        """
        n_individuos = x.shape[0]
        f1 = np.zeros(n_individuos, dtype=float)  # -afinidad
        f2 = np.zeros(n_individuos, dtype=float)  # tiempo total (min)
        g1 = np.zeros(n_individuos, dtype=float)  # tiempo_total - tiempo_max <= 0
        g2 = np.zeros(n_individuos, dtype=float)  # costo_total - presupuesto_max <= 0

        suma_costos_entradas = float(np.sum(self.costos_entradas))
        suma_tiempos_visitas = float(np.sum(self.tiempos_visitas))
        n_tramos = max(0, self.n_atractivos - 1)
        costo_total_traslados = n_tramos * self.costo_por_tramo
        costo_total = suma_costos_entradas + costo_total_traslados

        for k in range(n_individuos):
            ind = x[k]
            # 1. Afinidad promedio
            afinidad_total = float(np.mean(self.afinidad_individual[ind]))
            f1[k] = -afinidad_total

            # 2. Tiempo de traslados a lo largo de la ruta ordenada
            if n_tramos > 0:
                tiempo_traslado_total = float(np.sum(
                    self.tiempos_traslado_matriz[ind[:-1], ind[1:]]
                ))
            else:
                tiempo_traslado_total = 0.0

            tiempo_total = suma_tiempos_visitas + tiempo_traslado_total
            f2[k] = tiempo_total

            # 3. Restricciones
            g1[k] = tiempo_total - self.tiempo_max_min
            g2[k] = costo_total - self.presupuesto_max

        out["F"] = np.column_stack([f1, f2])
        out["G"] = np.column_stack([g1, g2])


def ejecutar_nsga2(
    atractivos: list[dict[str, Any]],
    transportes: list[dict[str, Any]],
    presupuesto_max: float,
    tiempo_disponible_horas: float,
    intereses: dict[str, float],
    tamano_poblacion: int = 50,
    generaciones: int = 40,
    prob_cruce: float = 0.9,
    prob_mutacion: float = 0.1,
) -> dict[str, Any]:
    """
    Ejecuta el algoritmo genético multiobjetivo NSGA-II con pymoo para la
    optimización de rutas e itinerarios turísticos.

    :param atractivos: Lista de atractivos con id, nombre, lat, lon, tiempo_visita, categoria, costo_entrada
    :param transportes: Lista de transportes con id, nombre, velocidad_promedio_kmh, tipo, tipo_costo, costo_por_tramo
    :param presupuesto_max: Presupuesto límite en BOB
    :param tiempo_disponible_horas: Tiempo total disponible en horas
    :param intereses: Diccionario de pesos de afinidad por categoría {nombre_categoria: peso (0.0 a 1.0)}
    :param tamano_poblacion: Tamaño de la población de cromosomas (default: 50)
    :param generaciones: Número de generaciones evolutivas (default: 40)
    :param prob_cruce: Probabilidad de cruce OrderCrossover (default: 0.9)
    :param prob_mutacion: Probabilidad de mutación InversionMutation (default: 0.1)
    :return: Diccionario con soluciones, frente de Pareto, historiales de convergencia y diversidad
    """
    inicio = time.perf_counter()

    if not atractivos or len(atractivos) < 2:
        raise ValueError("Se requieren al menos 2 atractivos para generar un itinerario.")
    if not transportes or len(transportes) < 1:
        raise ValueError("Se requiere al menos un medio de transporte disponible.")

    # Selección automática del transporte más rápido disponible
    transporte_optimo = max(transportes, key=lambda t: float(t.get("velocidad_promedio_kmh", 0.0) or 0.0))
    velocidad_kmh = max(1.0, float(transporte_optimo.get("velocidad_promedio_kmh", 30.0) or 30.0))
    costo_tramo_transporte = float(transporte_optimo.get("costo_por_tramo", 0.0) or 0.0)

    # Instanciación del problema
    problem = ItinerarioProblem(
        atractivos=atractivos,
        transporte_optimo=transporte_optimo,
        presupuesto_max=presupuesto_max,
        tiempo_disponible_horas=tiempo_disponible_horas,
        intereses=intereses,
    )

    # Configuración de operadores genéticos para permutaciones
    algorithm = NSGA2(
        pop_size=tamano_poblacion,
        sampling=PermutationRandomSampling(),
        crossover=OrderCrossover(prob=prob_cruce),
        mutation=InversionMutation(prob=prob_mutacion),
        eliminate_duplicates=True,
    )

    # Ejecución de la optimización con registro de historial
    res = minimize(
        problem,
        algorithm,
        ("n_gen", generaciones),
        seed=1,
        save_history=True,
        verbose=False,
    )

    fin = time.perf_counter()
    tiempo_ejecucion_seg = round(fin - inicio, 4)

    # Extracción de soluciones óptimas
    candidatos = []
    if res.opt is not None and len(res.opt) > 0:
        candidatos = list(res.opt)
    elif res.pop is not None and len(res.pop) > 0:
        candidatos = list(res.pop)

    soluciones_procesadas = []
    vistos_set = set()

    for sol in candidatos:
        perm = list(map(int, sol.X))
        perm_key = tuple(perm)
        if perm_key in vistos_set:
            continue
        vistos_set.add(perm_key)

        afinidad = float(-sol.F[0]) if hasattr(sol, "F") and sol.F is not None else 0.0
        tiempo_total_min = float(sol.F[1]) if hasattr(sol, "F") and sol.F is not None else 0.0

        # Validación de cumplimiento de restricciones
        feasible = bool(sol.feasible[0]) if hasattr(sol, "feasible") and sol.feasible is not None else True
        if hasattr(sol, "G") and sol.G is not None:
            feasible = bool(np.all(sol.G <= 1e-5))

        # Reconstruir desglose detallado de la ruta
        ids_ordenados = [atractivos[idx]["id"] for idx in perm]
        nombres_ordenados = [atractivos[idx]["nombre"] for idx in perm]
        categorias_ordenadas = [atractivos[idx].get("categoria", "General") for idx in perm]
        subcategorias_ordenadas = [atractivos[idx].get("subcategoria", "General") for idx in perm]
        costos_ordenados = [float(atractivos[idx].get("costo_entrada", 0.0) or 0.0) for idx in perm]
        tiempos_visita_ordenados = [int(atractivos[idx].get("tiempo_visita", 60) or 60) for idx in perm]

        # Tramos intermedios
        tramos = []
        distancia_total_km = 0.0
        tiempo_traslado_total_min = 0.0
        costo_total_traslados = 0.0

        for s in range(len(perm) - 1):
            idx_orig = perm[s]
            idx_dest = perm[s + 1]
            orig = atractivos[idx_orig]
            dest = atractivos[idx_dest]

            dist_km = haversine_km(
                float(orig["lat"]), float(orig["lon"]),
                float(dest["lat"]), float(dest["lon"])
            )
            t_traslado_min = (dist_km / velocidad_kmh) * 60.0
            distancia_total_km += dist_km
            tiempo_traslado_total_min += t_traslado_min
            costo_total_traslados += costo_tramo_transporte

            tramos.append({
                "tramo_numero": s + 1,
                "origen_id": orig["id"],
                "origen_nombre": orig["nombre"],
                "destino_id": dest["id"],
                "destino_nombre": dest["nombre"],
                "distancia_km": round(dist_km, 2),
                "tiempo_traslado_min": round(t_traslado_min, 1),
                "transporte_usado": transporte_optimo.get("nombre", "Transporte Óptimo"),
                "transporte_tipo": transporte_optimo.get("tipo", "General"),
                "costo_tramo_bob": round(costo_tramo_transporte, 2),
            })

        costo_total_entradas = sum(costos_ordenados)
        costo_total_bob = costo_total_entradas + costo_total_traslados
        tiempo_visitas_total_min = sum(tiempos_visita_ordenados)

        soluciones_procesadas.append({
            "atractivos_ids": ids_ordenados,
            "atractivos_nombres": nombres_ordenados,
            "categorias": categorias_ordenadas,
            "subcategorias": subcategorias_ordenadas,
            "tiempo_total_min": round(tiempo_total_min, 1),
            "tiempo_visitas_min": round(tiempo_visitas_total_min, 1),
            "tiempo_traslado_min": round(tiempo_traslado_total_min, 1),
            "distancia_total_km": round(distancia_total_km, 2),
            "afinidad": round(max(0.0, min(1.0, afinidad)), 4),
            "costo_total_bob": round(costo_total_bob, 2),
            "costo_entradas_bob": round(costo_total_entradas, 2),
            "costo_traslados_bob": round(costo_total_traslados, 2),
            "num_atractivos": len(perm),
            "cumple_restricciones": feasible,
            "transporte_asignado": {
                "id": transporte_optimo.get("id"),
                "nombre": transporte_optimo.get("nombre"),
                "velocidad_kmh": round(velocidad_kmh, 1),
                "costo_tramo_bob": round(costo_tramo_transporte, 2),
            },
            "tramos": tramos,
        })

    # Ordenar soluciones por afinidad descendente y luego por menor tiempo
    soluciones_procesadas.sort(key=lambda s: (-s["afinidad"], s["tiempo_total_min"]))

    # Construir Frente de Pareto [(tiempo_min, afinidad), ...]
    frente_pareto = [
        [sol["tiempo_total_min"], sol["afinidad"]]
        for sol in soluciones_procesadas
    ]

    # Extracción de historiales de convergencia y diversidad por generación
    historial_generaciones = []
    mejor_afinidad_por_gen = []
    mejor_tiempo_por_gen = []
    diversidad_por_gen = []

    if res.history is not None:
        for idx_g, gen in enumerate(res.history):
            historial_generaciones.append(idx_g + 1)
            pop = gen.pop
            F = pop.get("F")
            if F is not None and len(F) > 0:
                afinidades_gen = -F[:, 0]
                tiempos_gen = F[:, 1]
                mejor_afinidad_por_gen.append(round(float(np.max(afinidades_gen)), 4))
                mejor_tiempo_por_gen.append(round(float(np.min(tiempos_gen)), 1))
                diversidad_por_gen.append(round(float(np.std(afinidades_gen)), 4))
            else:
                mejor_afinidad_por_gen.append(0.0)
                mejor_tiempo_por_gen.append(0.0)
                diversidad_por_gen.append(0.0)

    return {
        "soluciones": soluciones_procesadas,
        "frente_pareto": frente_pareto,
        "historial_convergencia": {
            "generaciones": historial_generaciones,
            "mejor_afinidad": mejor_afinidad_por_gen,
            "mejor_tiempo": mejor_tiempo_por_gen,
        },
        "historial_diversidad": {
            "generaciones": historial_generaciones,
            "diversidad": diversidad_por_gen,
        },
        "parametros_usados": {
            "num_atractivos_seleccionados": len(atractivos),
            "presupuesto_max_bob": float(presupuesto_max),
            "tiempo_disponible_horas": float(tiempo_disponible_horas),
            "tamano_poblacion": tamano_poblacion,
            "generaciones": generaciones,
            "prob_cruce": prob_cruce,
            "prob_mutacion": prob_mutacion,
            "transporte_seleccionado": transporte_optimo.get("nombre"),
            "velocidad_transporte_kmh": round(velocidad_kmh, 1),
            "intereses": intereses,
        },
        "operadores_configurados": {
            "seleccion": "Torneo Binario (Binary Tournament)",
            "cruce": "Order Crossover (OX)",
            "mutacion": "Inversion Mutation",
            "sampling": "Permutation Random Sampling",
        },
        "tiempo_ejecucion_seg": tiempo_ejecucion_seg,
    }
