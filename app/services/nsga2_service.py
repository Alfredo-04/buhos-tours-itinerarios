import time
import logging
from datetime import datetime, time as dtime, timezone, timedelta
from typing import Any
import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.core.mutation import Mutation
from pymoo.optimize import minimize

from app.services.routing_service import obtener_ruta_real

logger = logging.getLogger(__name__)

# Zona horaria oficial de Bolivia: UTC-4
BOLIVIA_TZ = timezone(timedelta(hours=-4))

def obtener_hora_bolivia() -> datetime:
    """Retorna la fecha y hora actual en la zona horaria de Bolivia (UTC-4)."""
    return datetime.now(timezone.utc).astimezone(BOLIVIA_TZ)

# Intentar importar shapely para intersección de geometría WKT
try:
    from shapely import wkt
    from shapely.geometry import LineString, Point
    SHAPELY_DISPONIBLE = True
except ImportError:
    SHAPELY_DISPONIBLE = False
    logger.warning("Shapely no está instalado. El cálculo de zonas de tráfico utilizará verificación simplificada.")


def dia_semana_espanol(fecha: datetime | None = None) -> str:
    """Retorna el día de la semana en español en minúsculas (lunes, martes, etc.) en hora de Bolivia"""
    f = fecha or obtener_hora_bolivia()
    dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    return dias[f.weekday()]


def cargar_zonas_y_patrones_db(fecha_referencia: datetime | None = None) -> list[dict[str, Any]]:
    """
    Carga de forma eficiente las zonas de tráfico activas y sus patrones correspondientes
    para el día de la semana actual/especificado.
    """
    try:
        from app.models.zona_trafico import ZonaTrafico
        from app.models.patron_trafico import PatronTrafico

        dia_actual = dia_semana_espanol(fecha_referencia)
        zonas = ZonaTrafico.query.filter(ZonaTrafico.deleted_at.is_(None)).all()

        zonas_procesadas = []
        for z in zonas:
            geom_obj = None
            if SHAPELY_DISPONIBLE and z.geometria_wkt:
                try:
                    geom_obj = wkt.loads(z.geometria_wkt)
                except Exception as e:
                    logger.debug(f"Error parseando WKT para zona {z.nombre}: {e}")

            patrones_zona = [
                p for p in z.patrones 
                if not p.is_deleted and (p.dia_semana.lower() == dia_actual or p.dia_semana.lower() == 'todos')
            ]

            zonas_procesadas.append({
                'id_zona': z.id_zona,
                'nombre': z.nombre,
                'tipo_geometria': z.tipo_geometria,
                'geometria_wkt': z.geometria_wkt,
                'geom_obj': geom_obj,
                'patrones': patrones_zona
            })

        return zonas_procesadas
    except Exception as e:
        logger.warning(f"Error al cargar zonas de tráfico desde BD: {e}")
        return []


def detectar_trafico_tramo(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    hora_tramo: dtime,
    zonas_trafico: list[dict[str, Any]]
) -> tuple[float, list[dict[str, Any]]]:
    """
    Verifica qué zonas de tráfico cruza la línea entre (lat1, lon1) y (lat2, lon2).
    Aplica el factor de congestión más alto y recopila los avisos de tráfico.
    Retorna: (factor_maximo, lista_avisos_no_verdes)
    """
    factor_maximo = 1.0
    avisos = []

    if not zonas_trafico:
        return factor_maximo, avisos

    linea_tramo = None
    if SHAPELY_DISPONIBLE:
        try:
            linea_tramo = LineString([(lon1, lat1), (lon2, lat2)])
        except Exception:
            linea_tramo = None

    for z in zonas_trafico:
        cruza = False

        if linea_tramo is not None and z.get('geom_obj') is not None:
            try:
                geom = z['geom_obj']
                if linea_tramo.intersects(geom) or geom.contains(linea_tramo):
                    cruza = True
            except Exception:
                cruza = False

        if cruza:
            for p in z.get('patrones', []):
                h_ini = p.hora_inicio
                h_fin = p.hora_fin
                if h_ini <= hora_tramo <= h_fin:
                    f_cong = float(p.factor_congestion or 1.0)
                    if f_cong > factor_maximo:
                        factor_maximo = f_cong

                    if p.color_nivel != 'verde':
                        avisos.append({
                            'zona_nombre': z['nombre'],
                            'factor_congestion': f_cong,
                            'color_nivel': p.color_nivel,
                            'tipo': p.tipo,
                            'hora_franja': f"{h_ini.strftime('%H:%M')} - {h_fin.strftime('%H:%M')}"
                        })

    return factor_maximo, avisos


def asignar_transporte_tramo(
    distancia_km: float,
    transportes_disponibles: list[dict[str, Any]],
    num_personas: int = 1,
    presupuesto_bajo: bool = False
) -> dict[str, Any]:
    """
    Asignación inteligente de transporte con regla estricta de caminata:
    - Si distancia < 0.3 km (300m) -> Caminata (si está disponible).
    - Si distancia >= 0.3 km -> Vehículo (Taxi, Van, Minibús, Teleférico).
    """
    if not transportes_disponibles:
        raise ValueError("No hay medios de transporte disponibles.")

    if len(transportes_disponibles) == 1:
        t_unico = transportes_disponibles[0]
        cap = t_unico.get("capacidad")
        if cap is not None and cap < num_personas:
            raise ValueError(f"El transporte '{t_unico.get('nombre')}' tiene capacidad para {cap} personas, pero el grupo es de {num_personas}.")
        return t_unico

    aptos = [t for t in transportes_disponibles if (t.get("capacidad") is None or t.get("capacidad") >= num_personas)]
    if not aptos:
        aptos = sorted(transportes_disponibles, key=lambda t: t.get("capacidad") or 0, reverse=True)

    def match_tipo(t, keywords):
        nombre = (t.get("nombre") or "").lower()
        tipo = (t.get("tipo") or "").lower()
        return any(kw in nombre or kw in tipo for kw in keywords)

    caminata = next((t for t in aptos if match_tipo(t, ["camin", "pie", "walk"])), None)
    teleferico = next((t for t in aptos if match_tipo(t, ["telef", "cable"])), None)
    van = next((t for t in aptos if match_tipo(t, ["van", "minibus", "bus", "micro"])), None)
    taxi = next((t for t in aptos if match_tipo(t, ["taxi", "auto", "movil", "privado"])), None)

    vehiculos = [t for t in aptos if t != caminata]
    if not vehiculos:
        vehiculos = aptos

    # Regla estricta: < 300m caminata; >= 300m vehículo
    if distancia_km < 0.3:
        if caminata:
            return caminata

    # Para distancias >= 300 metros, preferir vehículos
    if distancia_km < 2.0:
        return taxi or van or teleferico or vehiculos[0]
    elif 2.0 <= distancia_km < 5.0:
        if presupuesto_bajo:
            return teleferico or van or taxi or vehiculos[0]
        return teleferico or van or taxi or vehiculos[0]
    elif 5.0 <= distancia_km <= 15.0:
        if presupuesto_bajo:
            return teleferico or van or vehiculos[0]
        return van or taxi or teleferico or vehiculos[0]
    else:  # > 15 km
        return van or taxi or vehiculos[0]


class ItinerarioVariableProblem(Problem):
    """
    Problema de optimización multiobjetivo con CROMOSOMA DE TAMAÑO VARIABLE:
    
    Representación del Genoma:
        Parte 1: Gen continuo en índice N que codifica el entero K (rango min_paradas a max_paradas).
        Parte 2: Genes 0 .. N-1 como Random Keys que determinan la permutación de TODOS los atractivos.
        Evaluación: Solo se usan los primeros K atractivos de la permutación, en ese orden.
    """

    def __init__(
        self,
        atractivos: list[dict[str, Any]],
        matriz_distancias: np.ndarray,
        matriz_duraciones_base: np.ndarray,
        matriz_factores_trafico: np.ndarray,
        transportes_tramo_matriz: list[list[dict[str, Any]]],
        presupuesto_max: float,
        tiempo_disponible_horas: float,
        intereses: dict[str, float],
        num_personas: int = 1,
        forzar_todos: bool = False,
        min_paradas: int = 2,
        max_paradas: int = 15,
    ):
        n_atractivos = len(atractivos)
        self.n_atractivos = n_atractivos
        self.atractivos = atractivos
        self.matriz_distancias = matriz_distancias
        self.matriz_duraciones_base = matriz_duraciones_base
        self.matriz_factores_trafico = matriz_factores_trafico
        self.transportes_tramo_matriz = transportes_tramo_matriz
        self.presupuesto_max = float(presupuesto_max)
        self.tiempo_max_min = float(tiempo_disponible_horas) * 60.0
        self.intereses = intereses
        self.num_personas = max(1, int(num_personas))
        self.forzar_todos = forzar_todos
        
        # Rango configurable de paradas [k_min, k_max]
        if forzar_todos:
            self.k_min = n_atractivos
            self.k_max = n_atractivos
        else:
            self.k_min = max(1, min(int(min_paradas), n_atractivos))
            self.k_max = max(self.k_min, min(int(max_paradas), n_atractivos))

        # Matriz de tiempos con factor de congestión aplicado
        self.matriz_tiempos_reales = self.matriz_duraciones_base * self.matriz_factores_trafico

        # Afinidad individual de cada atractivo (si está desactivada en intereses, peso = 0.0)
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

        # Cálculo de K_ideal: número máximo de atractivos que caben en tiempo y presupuesto
        t_vis_prom = float(np.mean(self.tiempos_visitas)) if len(self.tiempos_visitas) > 0 else 60.0
        t_traslado_prom = 20.0
        tiempo_por_parada = max(30.0, t_vis_prom + t_traslado_prom)
        k_tiempo = self.tiempo_max_min / tiempo_por_parada

        costos_pos = self.costos_entradas[self.costos_entradas > 0]
        costo_prom = float(np.mean(costos_pos)) if len(costos_pos) > 0 else 10.0
        costo_por_parada = max(5.0, costo_prom * self.num_personas)
        k_presupuesto = self.presupuesto_max / costo_por_parada

        k_ideal_calc = min(k_tiempo, k_presupuesto, float(self.n_atractivos))
        self.k_ideal = max(self.k_min, min(self.k_max, max(2, int(np.floor(k_ideal_calc)))))

        # Suma de pesos de los K_ideal atractivos más afines disponibles (base ideal de comparación)
        pesos_desc = np.sort(self.afinidad_individual)[::-1]
        self.sum_pesos_ideal = float(np.sum(pesos_desc[:self.k_ideal]))
        if self.sum_pesos_ideal <= 0.0:
            self.sum_pesos_ideal = 1.0

        # Variables: N prioridades continuas (permutación) + 1 gen para K
        super().__init__(
            n_var=n_atractivos + 1,
            n_obj=2,
            n_ieq_constr=0,
            xl=0.0,
            xu=1.0,
        )

    def decodificar_individuo(self, ind: np.ndarray) -> tuple[list[int], int]:
        """
        Decodifica el genoma a una lista de índices de atractivos de tamaño K:
        1. Parte 2 (Genes 0..N-1): Permutación completa de TODOS los atractivos.
        2. Parte 1 (Gen N): Determina K entre k_min y k_max.
        3. Solo se usan los primeros K atractivos de la permutación, en ese orden.
        """
        prioridades = ind[:self.n_atractivos]
        orden_completo = np.argsort(-prioridades)

        if self.forzar_todos or self.k_min >= self.k_max:
            k = self.k_min
        else:
            gen_k = float(ind[self.n_atractivos])
            rango_k = max(1, self.k_max - self.k_min)
            k = int(round(self.k_min + gen_k * rango_k))
            k = max(self.k_min, min(self.k_max, k))

        seleccionados = list(map(int, orden_completo[:k]))
        return seleccionados, k

    def calcular_costo_transporte(self, indices_ruta: list[int]) -> float:
        """
        Calcula el costo del transporte respetando la regla:
        - por_dia: cobrado UNA VEZ por día (no acumulado por tramo).
        - por_persona: cobrado UNA VEZ por persona (costo * num_personas).
        """
        if len(indices_ruta) < 2:
            return 0.0

        costo_total = 0.0
        vistos = set()
        for s in range(len(indices_ruta) - 1):
            i = indices_ruta[s]
            j = indices_ruta[s + 1]
            t = self.transportes_tramo_matriz[i][j]
            if t and t.get("id") not in vistos:
                vistos.add(t.get("id"))
                tipo_c = t.get("tipo_costo", "por_dia")
                c_unit = float(t.get("costo", 0.0) or 0.0)
                if tipo_c == "por_persona":
                    costo_total += c_unit * self.num_personas
                else:  # por_dia
                    costo_total += c_unit

        return costo_total

    def _evaluate(self, x: np.ndarray, out: dict[str, Any], *args: Any, **kwargs: Any) -> None:
        n_individuos = x.shape[0]
        f1 = np.zeros(n_individuos, dtype=float)
        f2 = np.zeros(n_individuos, dtype=float)
        g1 = np.zeros(n_individuos, dtype=float)
        g2 = np.zeros(n_individuos, dtype=float)

        t_max_ref = max(60.0, self.tiempo_max_min)

        for idx_ind in range(n_individuos):
            ind = x[idx_ind]
            ruta, k = self.decodificar_individuo(ind)

            # 1. Nueva fórmula calibrada: sum(pesos incluidos) / sum_pesos_ideal
            suma_pesos_incluidos = float(np.sum(self.afinidad_individual[ruta]))
            afinidad = min(1.0, suma_pesos_incluidos / self.sum_pesos_ideal)

            # 2. Tiempos de visita y traslados
            tiempo_visitas = float(np.sum(self.tiempos_visitas[ruta]))
            tiempo_traslados = 0.0
            if k > 1:
                origs = ruta[:-1]
                dests = ruta[1:]
                tiempo_traslados = float(np.sum(self.matriz_tiempos_reales[origs, dests]))

            tiempo_total = tiempo_visitas + tiempo_traslados

            # 3. Costo total: entradas * num_personas + tarifa transporte
            costo_entradas = float(np.sum(self.costos_entradas[ruta])) * self.num_personas
            costo_transporte = self.calcular_costo_transporte(ruta)
            costo_total = costo_entradas + costo_transporte

            # Restricciones
            exceso_tiempo = max(0.0, tiempo_total - self.tiempo_max_min)
            exceso_costo = max(0.0, costo_total - self.presupuesto_max)

            g1[idx_ind] = exceso_tiempo
            g2[idx_ind] = exceso_costo

            # Normalización de objetivos:
            # f1: maximizar afinidad -> minimizar -afinidad (rango [-1.0, 0.0])
            # f2: minimizar tiempo total normalizado (rango [0.0, ~1.0])
            tiempo_norm = tiempo_total / t_max_ref

            penalizacion = 0.0
            if exceso_tiempo > 0:
                penalizacion += 3.0 * (exceso_tiempo / 60.0)
            if exceso_costo > 0:
                penalizacion += 3.0 * (exceso_costo / max(1.0, self.presupuesto_max))

            f1[idx_ind] = -afinidad + penalizacion
            f2[idx_ind] = tiempo_norm + penalizacion

        out["F"] = np.column_stack([f1, f2])


def simplificar_nombre_experiencia(nombre_tecnico: str) -> str:
    """Mapea nombres formales de categorías o subcategorías a términos turísticos coloquiales."""
    mapa = {
        "Sitios Patrimoniales y Calles Históricas": "sitios históricos y calles coloniales",
        "Iglesias y Templos": "iglesias y templos tradicionales",
        "Museos": "museos",
        "Miradores": "miradores panorámicos",
        "Parques y Bosquecillos": "parques y áreas verdes",
        "Áreas Protegidas": "paisajes naturales",
        "Plazas": "plazas emblemáticas",
        "Mercados Tradicionales": "mercados típicos",
        "Gastronomía Tradicional": "gastronomía paceña",
        "Cultural": "espacios culturales",
        "Naturaleza": "naturaleza y miradores",
        "Urbano": "puntos urbanos icónicos",
        "Gastronomía": "sabores locales",
    }
    return mapa.get(nombre_tecnico, nombre_tecnico.lower())


def generar_descripcion_solucion(
    sol: dict[str, Any],
    min_tiempo: float,
    max_tiempo: float,
    min_costo: float,
    max_costo: float,
    intereses: dict[str, float]
) -> str:
    """
    Genera una descripción natural, cercana y turística para la solución (2-3 líneas):
    - NO menciona pesos numéricos (ej. peso 0.95).
    - NO menciona porcentajes de afinidad ni números de afinidad.
    - NO usa nombres técnicos fríos.
    - Describe la experiencia, para quién es ideal y cómo se compara en tiempo/costo.
    """
    n_atractivos = sol["num_atractivos"]
    subcats = sol.get("subcategorias", [])
    cats = sol.get("categorias", [])

    # Agrupar experiencias presentes en la ruta
    conteo_experiencias = {}
    for s_nom, c_nom in zip(subcats, cats):
        nombre_item = s_nom if (s_nom and s_nom != "General") else c_nom
        nombre_coloquial = simplificar_nombre_experiencia(nombre_item)
        peso = float(intereses.get(nombre_item, 0.5))
        if nombre_coloquial not in conteo_experiencias:
            conteo_experiencias[nombre_coloquial] = {"count": 0, "peso": peso}
        conteo_experiencias[nombre_coloquial]["count"] += 1

    # Ordenar por el interés/peso que el usuario asignó
    experiencias_ordenadas = sorted(
        conteo_experiencias.items(),
        key=lambda item: item[1]["peso"],
        reverse=True
    )

    nombres_exp = [exp[0] for exp in experiencias_ordenadas]
    if len(nombres_exp) >= 2:
        resumen_lugares = f"{nombres_exp[0]} con {nombres_exp[1]}"
        if len(nombres_exp) > 2:
            resumen_lugares += f" y {nombres_exp[2]}"
    elif len(nombres_exp) == 1:
        resumen_lugares = nombres_exp[0]
    else:
        resumen_lugares = "los principales atractivos de la ciudad"

    lo_mas_destacado = nombres_exp[0] if nombres_exp else "la historia y cultura paceña"

    afinidad_val = sol.get("afinidad", 0.0)

    # Variantes según el grado de afinidad
    if afinidad_val >= 0.70:
        texto_base = (
            f"Un recorrido por {n_atractivos} lugares que se ajusta mucho a lo que buscas, "
            f"combinando principalmente {resumen_lugares}. Ideal si quieres una experiencia centrada en {lo_mas_destacado}."
        )
    elif afinidad_val >= 0.45:
        texto_base = (
            f"Un recorrido equilibrado por {n_atractivos} paradas que combina {resumen_lugares}. "
            f"Buena opción si buscas variedad y conocer distintos aspectos de la ciudad sin alejarte de tus gustos."
        )
    else:
        texto_base = (
            f"Un recorrido diverso por {n_atractivos} lugares que abarca {resumen_lugares}. "
            f"Perfecto para una exploración variada y dinámica por la ciudad."
        )

    # Comparación relativa de tiempo y costo
    t_sol = sol["tiempo_total_min"]
    c_sol = sol["costo_total_bob"]
    rango_t = max(1.0, max_tiempo - min_tiempo)
    rango_c = max(1.0, max_costo - min_costo)

    pos_t = (t_sol - min_tiempo) / rango_t
    pos_c = (c_sol - min_costo) / rango_c

    frases_comparacion = []
    if pos_t <= 0.25 and pos_c <= 0.35:
        frases_comparacion.append("Es una de las opciones más rápidas y económicas.")
    elif pos_t <= 0.30:
        frases_comparacion.append("Es una de las opciones más ágiles y de menor duración.")
    elif pos_t >= 0.75:
        frases_comparacion.append("Es la opción más amplia y completa del recorrido.")
    else:
        frases_comparacion.append("Tiene una duración intermedia y bien aprovechada.")

    if not ("rápidas y económicas" in " ".join(frases_comparacion)):
        if pos_c <= 0.30:
            frases_comparacion.append("Mantiene un presupuesto muy bajo y accesible.")
        elif pos_c >= 0.75:
            frases_comparacion.append("Presenta un presupuesto algo mayor para cubrir todas sus paradas.")

    texto_final = f"{texto_base} {' '.join(frases_comparacion)}"
    return texto_final.strip()


def generar_sugerencias_no_viable(
    tiempo_total_min: float,
    tiempo_max_min: float,
    costo_total_bob: float,
    presupuesto_max_bob: float,
    num_atractivos: int
) -> list[str]:
    """Genera recomendaciones prácticas para flexibilizar una solución que excede límites."""
    sugerencias = []
    exceso_t = max(0.0, tiempo_total_min - tiempo_max_min)
    exceso_c = max(0.0, costo_total_bob - presupuesto_max_bob)

    if exceso_t > 0:
        horas_disp_actual = tiempo_max_min / 60.0
        horas_sugeridas = round(horas_disp_actual + (exceso_t / 60.0) + 0.5, 1)
        if num_atractivos > 2:
            sugerencias.append(f"Reduce 1-2 atractivos o aumenta el tiempo disponible a {horas_sugeridas}h.")
        else:
            sugerencias.append(f"Aumenta el tiempo disponible a {horas_sugeridas}h para cubrir la visita.")

    if exceso_c > 0:
        sug_presupuesto = round(presupuesto_max_bob + exceso_c + 15.0, 0)
        sugerencias.append(f"Usa transporte más económico o aumenta el presupuesto a Bs. {sug_presupuesto:.0f}.")

    return sugerencias


class SamplerDiversificado(FloatRandomSampling):
    """
    Muestreo inicial diversificado:
    Garantiza que la población inicial cubra uniformemente todos los valores de K
    desde k_min hasta k_max, sembrando diversidad estructural desde la generación 0.
    """
    def __init__(self, n_atractivos: int, k_min: int, k_max: int):
        super().__init__()
        self.n_atractivos = n_atractivos
        self.k_min = k_min
        self.k_max = k_max

    def _do(self, problem, n_samples, **kwargs):
        X = np.random.random((n_samples, self.n_atractivos + 1))
        rango_k = max(1, self.k_max - self.k_min)
        if rango_k > 0:
            k_vals = [self.k_min + (i % (rango_k + 1)) for i in range(n_samples)]
            np.random.shuffle(k_vals)
            for i in range(n_samples):
                X[i, self.n_atractivos] = (k_vals[i] - self.k_min) / float(rango_k)
        return X


class MutacionCompuesta(Mutation):
    """
    Operador de mutación para genoma mixto (Permutación Random Keys + Gen K):
    1. Aplica Polynomial Mutation a los genes continuos.
    2. Mutación de K: con probabilidad prob, incrementa o decrementa K en 1 aleatoriamente.
    """
    def __init__(self, n_atractivos: int, k_min: int, k_max: int, prob: float = 0.15, eta: float = 20.0):
        super().__init__()
        self.n_atractivos = n_atractivos
        self.k_min = k_min
        self.k_max = k_max
        self.prob = prob
        self.pm = PM(prob=prob, eta=eta)

    def _do(self, problem, X, **kwargs):
        X_mut = self.pm._do(problem, X.copy(), **kwargs)
        rango_k = max(1, self.k_max - self.k_min)
        if rango_k > 0:
            for i in range(len(X_mut)):
                if np.random.random() < self.prob:
                    paso = 1 if np.random.random() < 0.5 else -1
                    gen_k = X_mut[i, self.n_atractivos]
                    k_actual = int(round(self.k_min + gen_k * rango_k))
                    k_nuevo = max(self.k_min, min(self.k_max, k_actual + paso))
                    X_mut[i, self.n_atractivos] = (k_nuevo - self.k_min) / float(rango_k)
        return np.clip(X_mut, 0.0, 1.0)


def ejecutar_nsga2(
    atractivos: list[dict[str, Any]],
    transportes: list[dict[str, Any]],
    presupuesto_max: float,
    tiempo_disponible_horas: float,
    intereses: dict[str, float],
    tamano_poblacion: int = 100,
    generaciones: int = 100,
    prob_cruce: float = 0.85,
    prob_mutacion: float = 0.15,
    num_personas: int = 1,
    forzar_atractivos: bool = False,
    forzar_transporte: bool = False,
    min_paradas: int = 2,
    max_paradas: int = 15,
    auto_rango_paradas: bool = True,
    hora_inicio_tour: dtime | None = None
) -> dict[str, Any]:
    """
    Motor NSGA-II rediseñado con máxima diversidad de soluciones:
    1. Genoma de dos partes con K variable [min_paradas, max_paradas].
    2. Nueva fórmula de afinidad calibrada con K_ideal.
    3. Soluciones no viables condicionales con análisis y sugerencias prácticas.
    4. Descripción contextual detallada por cada solución generada.
    5. Horarios calculados en hora oficial de Bolivia (UTC-4).
    6. Sin Haversine: matrices de ruteo real y zonas de tráfico.
    """
    inicio = time.perf_counter()

    if not atractivos or len(atractivos) < 2:
        raise ValueError("Se requieren al menos 2 atractivos para generar un itinerario.")
    if not transportes or len(transportes) < 1:
        raise ValueError("Debes seleccionar al menos un medio de transporte disponible.")

    # Si auto_rango_paradas está activo, el algoritmo decide el rango de paradas internamente
    n_total_atractivos = len(atractivos)
    if auto_rango_paradas:
        min_paradas_efectivo = 2
        max_paradas_efectivo = max(2, min(15, n_total_atractivos))
    else:
        min_paradas_efectivo = max(1, min(int(min_paradas), n_total_atractivos))
        max_paradas_efectivo = max(min_paradas_efectivo, min(int(max_paradas), n_total_atractivos))

    # Hora de inicio oficial Bolivia (UTC-4)
    hora_bolivia_actual = obtener_hora_bolivia().time()
    hora_actual = hora_inicio_tour or dtime(9, 0)
    presupuesto_bajo = (presupuesto_max < 150.0)

    # 1. Validar transporte único o forzado
    transporte_fijo = None
    if len(transportes) == 1 or forzar_transporte:
        transporte_fijo = transportes[0]
        cap = transporte_fijo.get("capacidad")
        if cap is not None and cap < num_personas:
            raise ValueError(f"El transporte '{transporte_fijo.get('nombre')}' no tiene capacidad para el grupo ({num_personas} personas).")

    # 2. Cargar zonas de tráfico y patrones vigentes
    zonas_trafico = cargar_zonas_y_patrones_db()

    n = len(atractivos)
    matriz_distancias = np.zeros((n, n), dtype=float)
    matriz_duraciones_base = np.zeros((n, n), dtype=float)
    matriz_factores_trafico = np.ones((n, n), dtype=float)
    matriz_transportes_tramo: list[list[dict[str, Any] | None]] = [[None for _ in range(n)] for _ in range(n)]
    avisos_trafico_global = []

    # 3. Precomputar matrices por calles (usando OSRM o matriz pre-calculada en BD)
    for i in range(n):
        id_i = atractivos[i]["id"]
        lat_i = float(atractivos[i]["lat"])
        lon_i = float(atractivos[i]["lon"])

        for j in range(n):
            if i != j:
                id_j = atractivos[j]["id"]
                lat_j = float(atractivos[j]["lat"])
                lon_j = float(atractivos[j]["lon"])

                # Obtener distancia real por calles
                ruta_real = obtener_ruta_real(
                    origen_id=id_i,
                    destino_id=id_j,
                    lat1=lat_i,
                    lon1=lon_i,
                    lat2=lat_j,
                    lon2=lon_j
                )
                dist_km = ruta_real["distancia_km"]

                # Asignación de transporte (con umbral caminata < 300m)
                if transporte_fijo is not None:
                    t_tramo = transporte_fijo
                else:
                    t_tramo = asignar_transporte_tramo(
                        distancia_km=dist_km,
                        transportes_disponibles=transportes,
                        num_personas=num_personas,
                        presupuesto_bajo=presupuesto_bajo
                    )

                vel_transporte = max(1.0, float(t_tramo.get("velocidad_promedio_kmh", 30.0) or 30.0))
                dur_base_min = round((dist_km / vel_transporte) * 60.0, 2)

                # Factor de tráfico
                factor_trafico, avisos = detectar_trafico_tramo(lat_i, lon_i, lat_j, lon_j, hora_actual, zonas_trafico)
                if avisos:
                    avisos_trafico_global.extend(avisos)

                matriz_distancias[i, j] = dist_km
                matriz_duraciones_base[i, j] = dur_base_min
                matriz_factores_trafico[i, j] = factor_trafico
                matriz_transportes_tramo[i][j] = t_tramo

    # 4. Calibración de población y generaciones para máxima diversidad
    pob_calibrada = max(100, n * 5)
    gen_calibradas = max(100, n * 4)
    tamano_pob = max(tamano_poblacion, pob_calibrada)
    num_gen = max(generaciones, gen_calibradas)
    prob_crossover = 0.85
    prob_mutation = 0.15

    problem = ItinerarioVariableProblem(
        atractivos=atractivos,
        matriz_distancias=matriz_distancias,
        matriz_duraciones_base=matriz_duraciones_base,
        matriz_factores_trafico=matriz_factores_trafico,
        transportes_tramo_matriz=matriz_transportes_tramo,
        presupuesto_max=presupuesto_max,
        tiempo_disponible_horas=tiempo_disponible_horas,
        intereses=intereses,
        num_personas=num_personas,
        forzar_todos=forzar_atractivos,
        min_paradas=min_paradas_efectivo,
        max_paradas=max_paradas_efectivo,
    )

    algorithm = NSGA2(
        pop_size=tamano_pob,
        sampling=SamplerDiversificado(n, problem.k_min, problem.k_max),
        crossover=SBX(prob=prob_crossover, eta=15),
        mutation=MutacionCompuesta(n, problem.k_min, problem.k_max, prob=prob_mutation, eta=20),
        eliminate_duplicates=True,
    )

    res = minimize(
        problem,
        algorithm,
        ("n_gen", num_gen),
        seed=42,
        save_history=True,
        verbose=False,
    )

    fin = time.perf_counter()
    tiempo_ejecucion_seg = round(fin - inicio, 4)

    # 5. Extracción y decodificación de soluciones con Frente 1 y Frente 2 (F2)
    candidatos = []
    if res.opt is not None and len(res.opt) > 0:
        candidatos.extend(list(res.opt))

    # Si el frente de Pareto tiene pocas soluciones, enriquecer con Frente 2 (F2) y F3
    if res.pop is not None and len(res.pop) > 0:
        try:
            ranks = res.pop.get("rank")
            if ranks is not None and len(ranks) == len(res.pop):
                f2 = [res.pop[i] for i in range(len(res.pop)) if ranks[i] == 1]
                candidatos.extend(f2)
                if len(candidatos) < 15:
                    f3 = [res.pop[i] for i in range(len(res.pop)) if ranks[i] == 2]
                    candidatos.extend(f3)
            else:
                candidatos.extend(list(res.pop))
        except Exception as e:
            logger.debug(f"Aviso al extraer soluciones de frentes adicionales: {e}")
            candidatos.extend(list(res.pop))

    tiempo_max_min = float(tiempo_disponible_horas) * 60.0
    soluciones_procesadas = []
    vistos_rutas = set()

    for sol in candidatos:
        ind = np.array(sol.X)
        ruta, k = problem.decodificar_individuo(ind)

        # Evitar duplicados por ruta
        clave_ruta = tuple(ruta)
        clave_reversa = tuple(reversed(ruta))
        if clave_ruta in vistos_rutas or clave_reversa in vistos_rutas:
            continue
        vistos_rutas.add(clave_ruta)

        # Afinidad según la NUEVA FÓRMULA CALIBRADA: sum(pesos incluidos) / sum_pesos_ideal
        suma_pesos_incluidos = float(np.sum(problem.afinidad_individual[ruta]))
        afinidad = min(1.0, suma_pesos_incluidos / problem.sum_pesos_ideal)
        tiempo_visitas = float(np.sum(problem.tiempos_visitas[ruta]))
        costo_entradas = float(np.sum(problem.costos_entradas[ruta])) * num_personas

        tramos = []
        distancia_total_km = 0.0
        tiempo_traslados = 0.0
        transportes_en_solucion = []
        avisos_solucion = []

        # Cálculo de horarios paso a paso en hora de Bolivia (UTC-4)
        minutos_reloj = hora_actual.hour * 60 + hora_actual.minute
        paradas_detalle = []

        for s in range(k):
            idx_atr = ruta[s]
            atr = atractivos[idx_atr]
            t_vis = int(atr.get("tiempo_visita", 60) or 60)

            h_lleg_h = (minutos_reloj // 60) % 24
            h_lleg_m = minutos_reloj % 60
            hora_llegada_str = f"{h_lleg_h:02d}:{h_lleg_m:02d}"

            minutos_reloj += t_vis
            h_sal_h = (minutos_reloj // 60) % 24
            h_sal_m = minutos_reloj % 60
            hora_salida_str = f"{h_sal_h:02d}:{h_sal_m:02d}"

            paradas_detalle.append({
                "numero": s + 1,
                "id": atr["id"],
                "nombre": atr["nombre"],
                "categoria": atr.get("categoria", "General"),
                "subcategoria": atr.get("subcategoria", "General"),
                "tiempo_visita_min": t_vis,
                "costo_entrada_bob": float(atr.get("costo_entrada", 0.0) or 0.0),
                "hora_llegada": hora_llegada_str,
                "hora_salida": hora_salida_str,
            })

            # Tramo hacia el siguiente atractivo si existe
            if s < k - 1:
                idx_orig = ruta[s]
                idx_dest = ruta[s + 1]
                orig = atractivos[idx_orig]
                dest = atractivos[idx_dest]

                dist_km = matriz_distancias[idx_orig, idx_dest]
                t_traslado_min = matriz_duraciones_base[idx_orig, idx_dest] * matriz_factores_trafico[idx_orig, idx_dest]
                t_asignado = matriz_transportes_tramo[idx_orig][idx_dest]
                factor_trafico = matriz_factores_trafico[idx_orig, idx_dest]

                distancia_total_km += dist_km
                tiempo_traslados += t_traslado_min
                if t_asignado:
                    transportes_en_solucion.append(t_asignado.get("nombre"))

                hora_sal_tramo = hora_salida_str
                minutos_reloj += int(round(t_traslado_min))
                h_lleg_tr_h = (minutos_reloj // 60) % 24
                h_lleg_tr_m = minutos_reloj % 60
                hora_lleg_tramo = f"{h_lleg_tr_h:02d}:{h_lleg_tr_m:02d}"

                _, tramo_avisos = detectar_trafico_tramo(
                    float(orig["lat"]), float(orig["lon"]),
                    float(dest["lat"]), float(dest["lon"]),
                    hora_actual, zonas_trafico
                )
                for av in tramo_avisos:
                    avisos_solucion.append({
                        "tramo": f"Tramo {s+1}: {orig['nombre']} → {dest['nombre']}",
                        "zona": av["zona_nombre"],
                        "factor": av["factor_congestion"],
                        "color": av["color_nivel"]
                    })

                tramos.append({
                    "tramo_numero": s + 1,
                    "origen_id": orig["id"],
                    "origen_nombre": orig["nombre"],
                    "destino_id": dest["id"],
                    "destino_nombre": dest["nombre"],
                    "distancia_km": round(dist_km, 2),
                    "tiempo_traslado_min": round(t_traslado_min, 1),
                    "transporte_usado": t_asignado.get("nombre") if t_asignado else "Vehículo",
                    "transporte_tipo": t_asignado.get("tipo") if t_asignado else "General",
                    "factor_trafico": round(factor_trafico, 2),
                    "hora_salida": hora_sal_tramo,
                    "hora_llegada": hora_lleg_tramo,
                })

        tiempo_total_min = tiempo_visitas + tiempo_traslados
        costo_transporte = problem.calcular_costo_transporte(ruta)
        costo_total_bob = costo_entradas + costo_transporte

        # Verificación de excesos
        excesos = []
        feasible = True
        g1_exceso = max(0.0, tiempo_total_min - tiempo_max_min)
        g2_exceso = max(0.0, costo_total_bob - presupuesto_max)

        if g1_exceso > 1e-3:
            feasible = False
            h_exc = int(g1_exceso // 60)
            m_exc = int(g1_exceso % 60)
            h_tot = int(tiempo_total_min // 60)
            m_tot = int(tiempo_total_min % 60)
            h_lim = int(tiempo_max_min // 60)
            m_lim = int(tiempo_max_min % 60)
            excesos.append(f"Excede tiempo por {h_exc}h {m_exc}m (total: {h_tot}h {m_tot}m, límite: {h_lim}h {m_lim}m).")

        if g2_exceso > 1e-3:
            feasible = False
            excesos.append(f"Excede presupuesto por Bs. {g2_exceso:.2f} (total: Bs. {costo_total_bob:.2f}, límite: Bs. {presupuesto_max:.2f}).")

        ids_ordenados = [atractivos[idx]["id"] for idx in ruta]
        nombres_ordenados = [atractivos[idx]["nombre"] for idx in ruta]
        categorias_ordenadas = [atractivos[idx].get("categoria", "General") for idx in ruta]
        subcategorias_ordenadas = [atractivos[idx].get("subcategoria", "General") for idx in ruta]

        nombres_unicos_transporte = list(dict.fromkeys(transportes_en_solucion))
        transporte_resumen = ", ".join(nombres_unicos_transporte) if nombres_unicos_transporte else "Caminata / Estándar"

        sugerencias_no_viable = []
        if not feasible:
            sugerencias_no_viable = generar_sugerencias_no_viable(
                tiempo_total_min=tiempo_total_min,
                tiempo_max_min=tiempo_max_min,
                costo_total_bob=costo_total_bob,
                presupuesto_max_bob=presupuesto_max,
                num_atractivos=len(ruta)
            )

        soluciones_procesadas.append({
            "atractivos_ids": ids_ordenados,
            "atractivos_nombres": nombres_ordenados,
            "categorias": categorias_ordenadas,
            "subcategorias": subcategorias_ordenadas,
            "paradas": paradas_detalle,
            "tiempo_total_min": round(tiempo_total_min, 1),
            "tiempo_visitas_min": round(tiempo_visitas, 1),
            "tiempo_traslado_min": round(tiempo_traslados, 1),
            "distancia_total_km": round(distancia_total_km, 2),
            "afinidad": round(max(0.0, min(1.0, afinidad)), 4),
            "costo_total_bob": round(costo_total_bob, 2),
            "costo_entradas_bob": round(costo_entradas, 2),
            "costo_traslados_bob": round(costo_transporte, 2),
            "num_atractivos": len(ruta),
            "cumple_restricciones": feasible,
            "mensajes_exceso": excesos,
            "sugerencias_ajuste": sugerencias_no_viable,
            "transporte_asignado": {
                "nombre": transporte_resumen,
                "es_mixto": len(nombres_unicos_transporte) > 1,
            },
            "tramos": tramos,
            "avisos_trafico": avisos_solucion,
        })

    # SEPARAR SOLUCIONES VIABLES Y NO VIABLES
    soluciones_viables_raw = [s for s in soluciones_procesadas if s["cumple_restricciones"]]
    soluciones_no_viables_raw = [s for s in soluciones_procesadas if not s["cumple_restricciones"]]

    # 1. Procesar Soluciones Viables (diversidad de paradas K)
    soluciones_viables_final = []
    if len(soluciones_viables_raw) > 0:
        sol_por_k: dict[int, list[dict[str, Any]]] = {}
        for sol in soluciones_viables_raw:
            k_val = sol["num_atractivos"]
            if k_val not in sol_por_k:
                sol_por_k[k_val] = []
            sol_por_k[k_val].append(sol)

        mejores_k = []
        otras_v = []
        for k_val in sorted(sol_por_k.keys()):
            grupo = sol_por_k[k_val]
            grupo.sort(key=lambda s: (-s["afinidad"], s["tiempo_total_min"]))
            mejores_k.append(grupo[0])
            otras_v.extend(grupo[1:])

        soluciones_viables_final = list(mejores_k)
        otras_v.sort(key=lambda s: (-s["afinidad"], s["tiempo_total_min"]))

        vistas_m = {(s["num_atractivos"], round(s["afinidad"], 3), round(s["tiempo_total_min"], 0)) for s in soluciones_viables_final}
        for otra in otras_v:
            met = (otra["num_atractivos"], round(otra["afinidad"], 3), round(otra["tiempo_total_min"], 0))
            if met not in vistas_m:
                vistas_m.add(met)
                soluciones_viables_final.append(otra)
            if len(soluciones_viables_final) >= 12:
                break

        soluciones_viables_final.sort(key=lambda s: (-s["afinidad"], s["tiempo_total_min"]))

    # 2. Procesar Soluciones No Viables (hasta 10 con menor exceso relativo ponderado)
    soluciones_no_viables_final = []
    if len(soluciones_no_viables_raw) > 0:
        def exceso_ponderado(s: dict[str, Any]) -> float:
            exc_t = max(0.0, s["tiempo_total_min"] - tiempo_max_min) / max(60.0, tiempo_max_min)
            exc_c = max(0.0, s["costo_total_bob"] - presupuesto_max) / max(10.0, presupuesto_max)
            return exc_t + exc_c - (s["afinidad"] * 0.2)

        soluciones_no_viables_raw.sort(key=exceso_ponderado)

        # Deduplicar por (K, tiempo redondeado a 10 min, costo redondeado a Bs. 10)
        vistas_nv = set()
        candidatos_nv = []
        for sol in soluciones_no_viables_raw:
            clave_nv = (
                sol["num_atractivos"],
                int(round(sol["tiempo_total_min"] / 10.0) * 10),
                int(round(sol["costo_total_bob"] / 10.0) * 10)
            )
            if clave_nv not in vistas_nv:
                vistas_nv.add(clave_nv)
                candidatos_nv.append(sol)
            if len(candidatos_nv) >= 10:
                break

        # Si NO hay viables: tomar las 3-5 más cercanas (mínimo 1, máximo 5)
        # Si SÍ hay viables: tomar hasta 10 no viables para la sección colapsable
        limite_nv = 10 if len(soluciones_viables_final) == 0 else 10
        soluciones_no_viables_final = candidatos_nv[:limite_nv]

    hay_viables = len(soluciones_viables_final) > 0

    # Lista principal: si hay viables -> viables; si NO hay viables -> no viables (red de seguridad)
    soluciones_principales = soluciones_viables_final if hay_viables else soluciones_no_viables_final

    # 3. Generar descripciones turísticas para todas las soluciones a mostrar
    todas_a_describir = list(soluciones_principales)
    for snv in soluciones_no_viables_final:
        if snv not in todas_a_describir:
            todas_a_describir.append(snv)

    if todas_a_describir:
        tiempos_todos = [s["tiempo_total_min"] for s in todas_a_describir]
        costos_todos = [s["costo_total_bob"] for s in todas_a_describir]
        min_t, max_t = min(tiempos_todos), max(tiempos_todos)
        min_c, max_c = min(costos_todos), max(costos_todos)

        for sol in todas_a_describir:
            sol["descripcion"] = generar_descripcion_solucion(
                sol=sol,
                min_tiempo=min_t,
                max_tiempo=max_t,
                min_costo=min_c,
                max_costo=max_c,
                intereses=intereses,
            )

    frente_pareto = [
        [sol["tiempo_total_min"], sol["afinidad"]]
        for sol in soluciones_principales
    ]

    historial_generaciones = []
    mejor_afinidad_por_gen = []
    mejor_tiempo_por_gen = []
    diversidad_por_gen = []

    if res.history is not None:
        t_max_ref = max(60.0, tiempo_max_min)
        for idx_g, gen in enumerate(res.history):
            historial_generaciones.append(idx_g + 1)
            pop = gen.pop
            F = pop.get("F")
            if F is not None and len(F) > 0:
                afinidades_gen = np.clip(-F[:, 0], 0.0, 1.0)
                tiempos_gen = F[:, 1] * t_max_ref
                mejor_afinidad_por_gen.append(round(float(np.max(afinidades_gen)), 4))
                mejor_tiempo_por_gen.append(round(float(np.min(tiempos_gen)), 1))
                diversidad_por_gen.append(round(float(np.std(afinidades_gen)), 4))
            else:
                mejor_afinidad_por_gen.append(0.0)
                mejor_tiempo_por_gen.append(0.0)
                diversidad_por_gen.append(0.0)

    avisos_no_verdes_unicos = []
    claves_vistas = set()
    for av in avisos_trafico_global:
        clave = (av["zona_nombre"], av["color_nivel"])
        if clave not in claves_vistas:
            claves_vistas.add(clave)
            avisos_no_verdes_unicos.append(av)

    return {
        "soluciones": soluciones_principales,
        "soluciones_viables": soluciones_viables_final,
        "soluciones_no_viables": soluciones_no_viables_final,
        "hay_viables": hay_viables,
        "total_soluciones_viables": len(soluciones_viables_final),
        "total_soluciones_no_viables": len(soluciones_no_viables_final),
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
        "avisos_trafico": avisos_no_verdes_unicos,
        "parametros_usados": {
            "num_atractivos_seleccionados": len(atractivos),
            "presupuesto_max_bob": float(presupuesto_max),
            "tiempo_disponible_horas": float(tiempo_disponible_horas),
            "tamano_poblacion": tamano_pob,
            "generaciones": num_gen,
            "prob_cruce": prob_crossover,
            "prob_mutacion": prob_mutation,
            "min_paradas": min_paradas_efectivo,
            "max_paradas": max_paradas_efectivo,
            "auto_rango_paradas": auto_rango_paradas,
            "k_ideal": problem.k_ideal,
            "sum_pesos_ideal": round(problem.sum_pesos_ideal, 3),
            "hora_inicio_tour": hora_actual.strftime("%H:%M"),
            "transporte_seleccionado": transporte_fijo.get("nombre") if transporte_fijo else "Asignación Inteligente Dinámica",
            "velocidad_transporte_kmh": transporte_fijo.get("velocidad_promedio_kmh") if transporte_fijo else "Variable",
            "intereses": intereses,
            "forzar_atractivos": forzar_atractivos,
        },
        "operadores_configurados": {
            "seleccion": "Torneo Binario Elitista (NSGA-II)",
            "cruce": "Simulated Binary Crossover (SBX, prob=0.85)",
            "mutacion": "Mutación Compuesta (PM + Perturbación K ±1, prob=0.15)",
            "sampling": "Sampler Diversificado en Rango [k_min, k_max]",
        },
        "tiempo_ejecucion_seg": tiempo_ejecucion_seg,
    }
