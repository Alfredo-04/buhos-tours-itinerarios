import json
import numpy as np
from app import db
from app.models.archivo_pareto import ArchivoPareto

try:
    from pymoo.indicators.hv import HV
    from pymoo.indicators.gd import GD
    PYMOO_INDICADORES_DISPONIBLES = True
except ImportError:
    PYMOO_INDICADORES_DISPONIBLES = False

# Pesos por dimensión del vector 17D según impacto en complejidad y parametrización NSGA-II:
# D1 (4): [modo_explicito, n_candidatos, dias, exclusividad]
# D2 (4): [varianza_pesos, ratio_subcats, peso_promedio, sesgo_dominante]
# D3 (3): [radio_disp, zonas_distintas, sev_trafico]
# D4 (3): [presupuesto_norm, velocidad_norm, capacidad_norm]
# D5 (2): [ratio_tiempo, ratio_rigidas]
# D6 (1): [clima_activo]
PESOS_VECTOR_17D = np.array([
    1.5, 2.5, 2.0, 2.0,
    0.6, 1.0, 1.0, 0.6,
    1.2, 0.5, 0.5,
    1.2, 0.8, 1.2,
    1.5, 0.5,
    1.2,
], dtype=float)


def extraer_vector_instancia(
    contexto: dict,
    atractivos_data: list,
    matriz_distancias: np.ndarray = None,
    zonas_trafico: list = None,
    transporte_info: dict = None
) -> np.ndarray:
    """
    Calcula el Vector de 6 Dimensiones (17 sub-variables) normalizado (0 a 1).
    D1: Combinatoria y Escala (4)
    D2: Sesgo de Afinidad (4)
    D3: Topología y Grafo (3)
    D4: Logística y Economía (3)
    D5: Holgura Temporal (2)
    D6: Ambiental (1)
    Total: 17 dimensiones.
    """
    try:
        # --- DIMENSIÓN 1: Combinatoria y Escala (4 valores) ---
        modo_explicito = 1.0 if contexto.get("atractivos_ids") else 0.0
        n_candidatos_norm = min(len(atractivos_data) / 50.0, 1.0)
        dias = int(contexto.get("num_dias", 1))
        dias_norm = min(dias / 14.0, 1.0)
        exclusividad = 1.0 if contexto.get("forzar_atractivos", False) else 0.0

        # --- DIMENSIÓN 2: Sesgo de Afinidad (4 valores) ---
        intereses = contexto.get("intereses") or {}
        pesos = []
        for v in intereses.values():
            try:
                fv = float(v)
                if fv > 0.0:
                    pesos.append(fv)
            except (TypeError, ValueError):
                continue
        varianza_pesos = min(float(np.var(pesos)) if len(pesos) > 1 else 0.0, 1.0)
        ratio_subcats = min(len(pesos) / 13.0, 1.0)
        peso_promedio = min(float(np.mean(pesos)) if pesos else 0.0, 1.0)
        sesgo_dominante = min((max(pesos) / (sum(pesos) + 0.01)) if pesos else 0.0, 1.0)

        # --- DIMENSIÓN 3: Topología y Grafo (3 valores) ---
        if matriz_distancias is not None and np.any(matriz_distancias > 0):
            radio_disp = min(float(np.mean(matriz_distancias[matriz_distancias > 0])) / 20.0, 1.0)
        else:
            radio_disp = min(len(atractivos_data) / 30.0, 1.0)

        def _getv(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        zonas_distintas = 0.0
        if zonas_trafico:
            zonas_ids = set(
                _getv(z, 'id_zona') for z in zonas_trafico if _getv(z, 'id_zona')
            )
            zonas_distintas = min(len(zonas_ids) / 5.0, 1.0)

        sev_trafico = 0.0
        if zonas_trafico:
            factores = [
                float(_getv(p, 'factor_congestion', 1.0) or 1.0)
                for z in zonas_trafico
                for p in (_getv(z, 'patrones', []) or [])
            ]
            if factores:
                sev_trafico = min(float(np.mean(factores)) / 2.0, 1.0)

        # --- DIMENSIÓN 4: Logística y Economía (3 valores) ---
        presupuesto = float(contexto.get("presupuesto_max", 0))
        personas = int(contexto.get("num_personas", 1))
        p_diario = presupuesto / (personas * max(dias, 1))
        presupuesto_norm = min(p_diario / 500.0, 1.0)

        velocidad_kmh = float(transporte_info.get("velocidad_promedio_kmh", 30.0)) if transporte_info else 30.0
        velocidad_norm = min(velocidad_kmh / 60.0, 1.0)

        capacidad = float(transporte_info.get("capacidad", 100.0)) if transporte_info else 100.0
        capacidad_norm = min(personas / max(capacidad, 1.0), 1.0)

        # --- DIMENSIÓN 5: Holgura Temporal (2 valores) ---
        tiempo_visitas = sum(int(a.get("tiempo_visita", 60)) for a in atractivos_data)
        horas_disponibles = dias * 9.0 * 60
        ratio_tiempo = min(tiempo_visitas / max(horas_disponibles, 1), 1.0)

        ventanas_rigidas = sum(1 for a in atractivos_data if a.get("horario_cierre"))
        ratio_rigidas = min(ventanas_rigidas / max(len(atractivos_data), 1), 1.0)

        # --- DIMENSIÓN 6: Ambiental (1 valor) ---
        clima_activo = 1.0 if contexto.get("usar_clima", True) else 0.0

        # Vector final (17 dimensiones)
        vector = [
            modo_explicito, n_candidatos_norm, dias_norm, exclusividad,
            varianza_pesos, ratio_subcats, peso_promedio, sesgo_dominante,
            radio_disp, zonas_distintas, sev_trafico,
            presupuesto_norm, velocidad_norm, capacidad_norm,
            ratio_tiempo, ratio_rigidas,
            clima_activo
        ]
        return np.array(vector, dtype=float)

    except Exception as e:
        import traceback
        print(f"[ERROR] Error generando vector 17D: {e}")
        traceback.print_exc()
        return np.zeros(17)


def _distancia_ponderada_17d(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calcula distancia Euclidiana ponderada y normalizada en [0, 1] entre dos vectores 17D.
    """
    if len(v1) != len(v2):
        n = min(len(v1), len(v2))
        v1 = v1[:n]
        v2 = v2[:n]
    pesos = PESOS_VECTOR_17D[:len(v1)] if len(v1) <= len(PESOS_VECTOR_17D) else np.ones(len(v1))
    suma_pesos = float(np.sum(pesos)) or 1.0
    diff2 = (v1 - v2) ** 2
    return float(np.sqrt(np.sum(pesos * diff2) / suma_pesos))


def _rankear_archivos_por_distancia(vector: np.ndarray, solo_calibrados: bool = False) -> list[tuple[float, ArchivoPareto]]:
    """
    Consulta en SOLO LECTURA la tabla ArchivoPareto y ordena los registros
    por distancia ponderada ascendente respecto al vector de consulta.
    """
    query = ArchivoPareto.query
    if solo_calibrados:
        query = query.filter(
            ArchivoPareto.poblacion_optima.isnot(None),
            ArchivoPareto.generaciones_optimas.isnot(None),
        )
    archivos = query.all()
    rankeados = []

    for arch in archivos:
        try:
            vec_hist = np.array(json.loads(arch.vector_instancia_json), dtype=float)
            dist = _distancia_ponderada_17d(vector, vec_hist)
            rankeados.append((dist, arch))
        except Exception:
            continue

    rankeados.sort(key=lambda item: (item[0], item[1].id_archivo))
    return rankeados


def buscar_vecino_mas_cercano(vector: np.ndarray, umbral: float | None = None) -> ArchivoPareto | None:
    """
    Busca el ArchivoPareto más cercano usando distancia ponderada 17D.
    Por defecto (umbral=None) siempre retorna el vecino más cercano disponible
    para garantizar que ninguna generación en producción quede sin referencia.
    """
    rankeados = _rankear_archivos_por_distancia(vector, solo_calibrados=False)
    if not rankeados:
        return None
    mejor_dist, mejor_arch = rankeados[0]
    if umbral is not None and mejor_dist > umbral:
        return None
    return mejor_arch


def predecir_parametros_knn(vector: np.ndarray, k: int = 3) -> dict | None:
    """
    Motor KNN ponderado (K vecinos más cercanos con Inverse Distance Weighting):
    - Solo lectura sobre ArchivoPareto (no inserta ni modifica registros de entrenamiento).
    - Selecciona siempre el escenario más cercano como referencia principal (`archivo_ref`)
      para garantizar trazabilidad del 100% de las consultas en producción.
    - Predice (poblacion, generaciones, prob_mutacion) combinando los K vecinos calibrados
      más cercanos mediante ponderación inversa al cuadrado de la distancia.
    """
    calibrados = _rankear_archivos_por_distancia(vector, solo_calibrados=True)
    if not calibrados:
        calibrados = _rankear_archivos_por_distancia(vector, solo_calibrados=False)
    if not calibrados:
        return None

    dist_min, archivo_ref = calibrados[0]
    top_k = calibrados[:max(1, min(k, len(calibrados)))]
    similitud_pct = round(max(0.0, min(100.0, (1.0 - dist_min) * 100.0)), 1)

    # Coincidencia prácticamente exacta con un escenario entrenado: usar su receta exacta
    if dist_min < 0.03 and archivo_ref.poblacion_optima and archivo_ref.generaciones_optimas:
        return {
            "archivo_ref": archivo_ref,
            "id_archivo_pareto": archivo_ref.id_archivo,
            "vecinos_ids": [archivo_ref.id_archivo],
            "distancia_min": round(dist_min, 4),
            "similitud_pct": similitud_pct,
            "tamano_poblacion": int(archivo_ref.poblacion_optima),
            "generaciones": int(archivo_ref.generaciones_optimas),
            "prob_mutacion": round(float(archivo_ref.prob_mutacion_optima or 0.15), 2),
        }

    # Regresión K-NN ponderada por distancia inversa al cuadrado (IDW)
    eps = 1e-4
    suma_w = 0.0
    suma_p = 0.0
    suma_g = 0.0
    suma_m = 0.0
    vecinos_ids = []

    for d, arch in top_k:
        p = arch.poblacion_optima or 100
        g = arch.generaciones_optimas or 100
        m = float(arch.prob_mutacion_optima if arch.prob_mutacion_optima is not None else 0.15)
        w = 1.0 / ((d ** 2) + eps)
        suma_w += w
        suma_p += w * float(p)
        suma_g += w * float(g)
        suma_m += w * m
        vecinos_ids.append(arch.id_archivo)

    pobs_validas = sorted({int(a.poblacion_optima) for _, a in calibrados if a.poblacion_optima}) or [40, 80, 150]
    gens_validas = sorted({int(a.generaciones_optimas) for _, a in calibrados if a.generaciones_optimas}) or [50, 100]
    muts_validas = sorted({round(float(a.prob_mutacion_optima), 2) for _, a in calibrados if a.prob_mutacion_optima is not None}) or [0.05, 0.15, 0.25]

    pob_raw = suma_p / suma_w
    gen_raw = suma_g / suma_w
    mut_raw = suma_m / suma_w

    # Ajustar al valor discreto calibrado más cercano de la rejilla entrenada
    pob_pred = min(pobs_validas, key=lambda v: (abs(v - pob_raw), v))
    gen_pred = min(gens_validas, key=lambda v: (abs(v - gen_raw), v))
    mut_pred = min(muts_validas, key=lambda v: (abs(v - mut_raw), v))

    return {
        "archivo_ref": archivo_ref,
        "id_archivo_pareto": archivo_ref.id_archivo,
        "vecinos_ids": vecinos_ids,
        "distancia_min": round(dist_min, 4),
        "similitud_pct": similitud_pct,
        "tamano_poblacion": pob_pred,
        "generaciones": gen_pred,
        "prob_mutacion": mut_pred,
    }


def _filtrar_no_dominados(puntos: np.ndarray) -> np.ndarray:
    if puntos is None or len(puntos) == 0:
        return puntos
    puntos_unicos = np.unique(np.round(puntos, 6), axis=0)
    n = len(puntos_unicos)
    if n == 0:
        return puntos_unicos
    no_dom = np.ones(n, dtype=bool)
    for i in range(n):
        for j in range(n):
            if i != j and np.all(puntos_unicos[j] <= puntos_unicos[i]) and np.any(puntos_unicos[j] < puntos_unicos[i]):
                no_dom[i] = False
                break
    return puntos_unicos[no_dom]


def _calcular_hv_normalizado(frente_actual: np.ndarray, ref_point: np.ndarray) -> float | None:
    if frente_actual is None or len(frente_actual) == 0 or not PYMOO_INDICADORES_DISPONIBLES:
        return None
    try:
        f = np.array(frente_actual, dtype=float)
        rp = np.array(ref_point, dtype=float)
        # Expandir ref_point solo si algún punto de producción excede la caja de referencia
        rp_eff = np.where(f.max(axis=0) >= rp, f.max(axis=0) + 0.1, rp)
        combinado = np.vstack([f, rp_eff.reshape(1, -1)])
        min_vals = combinado.min(axis=0)
        max_vals = combinado.max(axis=0)
        rango = max_vals - min_vals
        rango[rango == 0] = 1.0
        f_norm = (f - min_vals) / rango
        rp_norm = (rp_eff - min_vals) / rango
        return round(float(HV(ref_point=rp_norm)(f_norm)), 6)
    except Exception:
        return None


def _calcular_gd_normalizado(frente_actual: np.ndarray, frente_ref: np.ndarray) -> float | None:
    if frente_actual is None or len(frente_actual) == 0 or frente_ref is None or len(frente_ref) == 0:
        return None
    try:
        combinado = np.vstack([frente_actual, frente_ref])
        min_vals = combinado.min(axis=0)
        max_vals = combinado.max(axis=0)
        rango = max_vals - min_vals
        rango[rango == 0] = 1.0
        fa_norm = (np.array(frente_actual, dtype=float) - min_vals) / rango
        fr_norm = (np.array(frente_ref, dtype=float) - min_vals) / rango
        distancias = [np.min(np.linalg.norm(fr_norm - p, axis=1)) for p in fa_norm]
        return round(float(np.mean(distancias)), 6)
    except Exception:
        return None


def _calcular_spread_normalizado(frente_actual: np.ndarray, frente_ref: np.ndarray | None = None) -> float:
    if frente_actual is None or len(frente_actual) < 2:
        return 0.0
    f_limpio = _filtrar_no_dominados(np.array(frente_actual, dtype=float))
    if f_limpio is None or len(f_limpio) < 2:
        return 0.0
    if frente_ref is not None and len(frente_ref) >= 2:
        combinado = np.vstack([f_limpio, frente_ref])
    else:
        combinado = f_limpio
    min_vals = combinado.min(axis=0)
    max_vals = combinado.max(axis=0)
    rango = max_vals - min_vals
    rango[rango == 0] = 1.0
    f_ord = (f_limpio - min_vals) / rango
    f_ord = f_ord[f_ord[:, 0].argsort()]
    distancias = [np.linalg.norm(f_ord[i] - f_ord[i - 1]) for i in range(1, len(f_ord))]
    d_prom = float(np.mean(distancias)) if distancias else 0.0
    if frente_ref is not None and len(frente_ref) >= 2:
        ref_norm = (np.array(frente_ref, dtype=float) - min_vals) / rango
        ref_ord = ref_norm[ref_norm[:, 0].argsort()]
        d_f = np.linalg.norm(f_ord[0] - ref_ord[0])
        d_l = np.linalg.norm(f_ord[-1] - ref_ord[-1])
    else:
        d_f = np.linalg.norm(f_ord[0] - f_ord[-1])
        d_l = d_f
    sum_dif = sum(abs(d - d_prom) for d in distancias)
    denom = d_f + d_l + len(distancias) * d_prom
    return round(float((d_f + d_l + sum_dif) / denom) if denom > 0 else 0.0, 6)


def evaluar_metricas_pareto_produccion(
    F_crudo,
    vector_instancia: np.ndarray,
    archivo_ref: ArchivoPareto | None = None,
) -> dict:
    """
    Evalúa HV, GD y Spread de una corrida en PRODUCCIÓN contra su ArchivoPareto de referencia
    de forma 100% SOLO LECTURA (nunca inserta ni altera ArchivoPareto ni RecetaEntrenamiento).
    """
    resultado = {
        "hipervolumen": None,
        "gd": None,
        "spread": None,
        "id_archivo_pareto": None,
        "num_soluciones_archivo_ref": 0,
    }
    if F_crudo is None or len(F_crudo) == 0:
        return resultado

    try:
        F_arr = _filtrar_no_dominados(np.array(F_crudo, dtype=float))
        if F_arr is None or len(F_arr) == 0:
            return resultado

        if archivo_ref is None and vector_instancia is not None:
            archivo_ref = buscar_vecino_mas_cercano(vector_instancia, umbral=None)

        ref_point = None
        valores_previos = None
        if archivo_ref is not None:
            resultado["id_archivo_pareto"] = archivo_ref.id_archivo
            try:
                ref_point = np.array(json.loads(archivo_ref.ref_point_json), dtype=float)
            except Exception:
                ref_point = None
            try:
                valores_previos = np.array(json.loads(archivo_ref.valores_json), dtype=float)
            except Exception:
                valores_previos = None
            resultado["num_soluciones_archivo_ref"] = int(
                archivo_ref.num_puntos or (len(valores_previos) if valores_previos is not None else 0)
            )

        if ref_point is None or len(ref_point) != F_arr.shape[1]:
            ref_point = F_arr.max(axis=0) + np.full(F_arr.shape[1], 0.1)

        resultado["hipervolumen"] = _calcular_hv_normalizado(F_arr, ref_point)
        if valores_previos is not None and len(valores_previos) > 0:
            resultado["gd"] = _calcular_gd_normalizado(F_arr, valores_previos)
        resultado["spread"] = _calcular_spread_normalizado(F_arr, valores_previos)

    except Exception as e:
        print(f"[WARN] Error evaluando métricas Pareto en producción: {e}")

    return resultado


def calcular_y_actualizar_metricas_pareto(
    F_crudo,
    contexto: dict,
    vector_instancia: np.ndarray,
    solo_lectura: bool = True,
    archivo_ref: ArchivoPareto | None = None,
) -> dict:
    """
    Wrapper compatible: en producción (solo_lectura=True por defecto) evalúa métricas
    sin insertar ni modificar ArchivoPareto ni RecetaEntrenamiento.
    """
    return evaluar_metricas_pareto_produccion(
        F_crudo=F_crudo,
        vector_instancia=vector_instancia,
        archivo_ref=archivo_ref,
    )
