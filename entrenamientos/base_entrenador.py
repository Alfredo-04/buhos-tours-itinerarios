# -*- coding: utf-8 -*-
"""
Motor Base de Calibración y Entrenamiento NSGA-II para Clústeres Temáticos (Búhos Tours).
Módulo central reutilizable para entrenar cualquiera de los 9 clústeres (Escenarios 11 al 100).

Garantiza:
1. Replicación idéntica de la lógica de calibración (Molde de Oro 20 corridas + Grid Search 10 corridas).
2. Cálculo exacto del vector 17D ponderado con distancias reales.
3. Compatibilidad con la corrección de diversidad Jaccard en forzar_atractivos=True (múltiples soluciones reales).
4. Idempotencia en ArchivoPareto y RecetaEntrenamiento.
"""

import sys
import os
import time
import json
import numpy as np

# Asegurar path raíz del proyecto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app, db
from app.models.archivo_pareto import ArchivoPareto
from app.models.receta_entrenamiento import RecetaEntrenamiento
from app.services.nsga2_service import ejecutar_nsga2, cargar_zonas_y_patrones_db
from app.services.routing_service import obtener_ruta_real
from app.services.itinerario_service import preparar_datos_nsga2
from app.services.metricas_pareto_service import extraer_vector_instancia

try:
    from pymoo.indicators.hv import HV
    from pymoo.indicators.gd import GD
    PYMOO_INDICADORES_DISPONIBLES = True
except ImportError:
    PYMOO_INDICADORES_DISPONIBLES = False

# ==========================================
# PARÁMETROS GLOBALES DE CALIBRACIÓN
# ==========================================
CORRIDAS_MOLDE_ORO = 20      # Molde de oro (Fase A)
CORRIDAS_POR_CONFIG = 10     # Grid Search (Fase B)

MOLDE_POBLACION = 200
MOLDE_GENERACIONES = 300

POBLACIONES = [40, 80, 150]
GENERACIONES = [50, 100]
MUTACIONES = [0.05, 0.15, 0.25]
# 3 x 2 x 3 = 18 combinaciones


def _extraer_frente(resultado):
    if 'frente_pareto_raw' in resultado and resultado['frente_pareto_raw']:
        return np.array(resultado['frente_pareto_raw'], dtype=float)
    return None


def _filtrar_no_dominados(puntos):
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


def _calcular_gd(frente_actual, frente_ref):
    if frente_actual is None or len(frente_actual) == 0 or frente_ref is None or len(frente_ref) == 0:
        return None
    combinado = np.vstack([frente_actual, frente_ref])
    min_vals = combinado.min(axis=0)
    max_vals = combinado.max(axis=0)
    rango = max_vals - min_vals
    rango[rango == 0] = 1.0
    fa_norm = (np.array(frente_actual, dtype=float) - min_vals) / rango
    fr_norm = (np.array(frente_ref, dtype=float) - min_vals) / rango
    distancias = [np.min(np.linalg.norm(fr_norm - p, axis=1)) for p in fa_norm]
    return float(np.mean(distancias))


def _calcular_spread(frente_actual, frente_ref=None):
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
    F_ord = (f_limpio - min_vals) / rango
    F_ord = F_ord[F_ord[:, 0].argsort()]
    distancias = [np.linalg.norm(F_ord[i] - F_ord[i-1]) for i in range(1, len(F_ord))]
    d_prom = float(np.mean(distancias)) if distancias else 0.0
    if frente_ref is not None and len(frente_ref) >= 2:
        ref_norm = (np.array(frente_ref, dtype=float) - min_vals) / rango
        ref_ord = ref_norm[ref_norm[:, 0].argsort()]
        d_f = np.linalg.norm(F_ord[0] - ref_ord[0])
        d_l = np.linalg.norm(F_ord[-1] - ref_ord[-1])
    else:
        d_f = np.linalg.norm(F_ord[0] - F_ord[-1])
        d_l = d_f
    sum_dif = sum(abs(d - d_prom) for d in distancias)
    denom = d_f + d_l + len(distancias) * d_prom
    return round(float((d_f + d_l + sum_dif) / denom) if denom > 0 else 0.0, 6)


def _calcular_hv(frente_actual, ref_point):
    if frente_actual is None or len(frente_actual) == 0:
        return None
    try:
        f = np.array(frente_actual, dtype=float)
        rp = np.array(ref_point, dtype=float)
        combinado = np.vstack([f, rp.reshape(1, -1)])
        min_vals = combinado.min(axis=0)
        max_vals = combinado.max(axis=0)
        rango = max_vals - min_vals
        rango[rango == 0] = 1.0
        f_norm = (f - min_vals) / rango
        rp_norm = (rp - min_vals) / rango
        hv_indicator = HV(ref_point=rp_norm)
        return float(hv_indicator(f_norm))
    except Exception as e:
        print(f"[WARN] Error HV: {e}")
        return None


def _procesar_historial_raw(historial_F_raw, pf_ref_raw, ref_point_raw):
    hist_hv, hist_gd, hist_spread = [], [], []
    for F_gen_list in historial_F_raw:
        if not F_gen_list:
            hist_hv.append(None)
            hist_gd.append(None)
            hist_spread.append(None)
            continue
        puntos = _filtrar_no_dominados(np.array(F_gen_list, dtype=float))
        if len(puntos) == 0:
            hist_hv.append(None)
            hist_gd.append(None)
            hist_spread.append(None)
            continue
        gd_val = _calcular_gd(puntos, pf_ref_raw)
        spread_val = _calcular_spread(puntos, pf_ref_raw)
        hv_val = _calcular_hv(puntos, ref_point_raw)
        hist_hv.append(round(hv_val, 4) if hv_val is not None else None)
        hist_gd.append(round(gd_val, 4) if gd_val is not None else None)
        hist_spread.append(round(spread_val, 4) if spread_val is not None else None)
    return hist_hv, hist_gd, hist_spread


def _promediar_historiales(lista_de_historiales):
    if not lista_de_historiales:
        return []
    longitud = min(len(h) for h in lista_de_historiales)
    promedios = []
    for g in range(longitud):
        valores = [h[g] for h in lista_de_historiales if h[g] is not None]
        promedios.append(round(float(np.mean(valores)), 4) if valores else None)
    return promedios


def _construir_vector_instancia_real(ESCENARIO, atractivos_data, transportes_data):
    contexto_vector = {
        "atractivos_ids": ESCENARIO.get('atractivos_ids', []),
        "num_dias": ESCENARIO['num_dias'],
        "presupuesto_max": ESCENARIO['presupuesto_max'],
        "num_personas": ESCENARIO['num_personas'],
        "intereses": ESCENARIO['intereses'],
        "usar_clima": ESCENARIO['usar_clima'],
        "forzar_atractivos": ESCENARIO['forzar_atractivos'],
        "forzar_transporte": ESCENARIO['forzar_transporte'],
        "min_paradas": ESCENARIO['min_paradas'],
        "max_paradas": ESCENARIO['max_paradas'],
        "auto_rango_paradas": ESCENARIO['auto_rango_paradas'],
    }
    zonas_trafico = cargar_zonas_y_patrones_db()
    n = len(atractivos_data)
    matriz_distancias = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            a_i = atractivos_data[i]
            a_j = atractivos_data[j]
            ruta = obtener_ruta_real(
                origen_id=a_i["id"], destino_id=a_j["id"],
                lat1=float(a_i["lat"]), lon1=float(a_i["lon"]),
                lat2=float(a_j["lat"]), lon2=float(a_j["lon"]),
            )
            matriz_distancias[i, j] = float(ruta["distancia_km"])
    transporte_info = transportes_data[0] if transportes_data else None
    return extraer_vector_instancia(
        contexto=contexto_vector,
        atractivos_data=atractivos_data,
        matriz_distancias=matriz_distancias,
        zonas_trafico=zonas_trafico,
        transporte_info=transporte_info,
    )


def entrenar_escenario_individual(ESCENARIO):
    print("\n" + "="*70)
    print(f"INICIANDO ENTRENAMIENTO: {ESCENARIO['nombre']}")
    print(f"  Molde de oro: {CORRIDAS_MOLDE_ORO} corridas | Grid Search: {CORRIDAS_POR_CONFIG} corridas")
    print("="*70)

    atractivos_data, transportes_data = preparar_datos_nsga2(
        atractivos_ids=ESCENARIO.get('atractivos_ids', []),
        transporte_ids=ESCENARIO['transporte_ids'],
        categorias_activas_ids=ESCENARIO.get('categorias_activas_ids'),
        subcategorias_activas_ids=ESCENARIO.get('subcategorias_activas_ids'),
    )
    print(f"[INFO] Atractivos disponibles: {len(atractivos_data)}, Transportes: {len(transportes_data)}")

    vector_17d = _construir_vector_instancia_real(ESCENARIO, atractivos_data, transportes_data)
    print(f"[INFO] Vector ({len(vector_17d)}D): {vector_17d.round(4).tolist()}")

    zonas_distintas = float(vector_17d[9]) if len(vector_17d) > 9 else 0.0
    sev_trafico = float(vector_17d[10]) if len(vector_17d) > 10 else 0.0
    if zonas_distintas == 0.0 or sev_trafico == 0.0:
        print(f"[WARN] D3 parcialmente vacía (zonas={zonas_distintas}, tráfico={sev_trafico}).")
    else:
        print(f"[INFO] D3 OK: zonas={zonas_distintas:.3f}, tráfico={sev_trafico:.3f}")

    archivo = ArchivoPareto(
        vector_instancia_json=json.dumps(vector_17d.tolist()),
        ref_point_json=json.dumps([0.0, 1.0]),
        valores_json=json.dumps([]),
        num_puntos=0,
        total_ejecuciones=0,
    )
    db.session.add(archivo)
    db.session.commit()
    print(f"[OK] ArchivoPareto registrado exitosamente (ID: {archivo.id_archivo})")

    # ============ FASE A: MOLDE DE ORO ============
    print(f"\n[FASE A] Molde de Oro ({CORRIDAS_MOLDE_ORO} corridas, Pop={MOLDE_POBLACION}, Gen={MOLDE_GENERACIONES})...")
    frentes_raw = []
    historiales_F_molde = []

    for i in range(CORRIDAS_MOLDE_ORO):
        print(f"  Corrida {i+1}/{CORRIDAS_MOLDE_ORO}...", end=" ", flush=True)
        res = ejecutar_nsga2(
            atractivos=atractivos_data,
            transportes=transportes_data,
            presupuesto_max=ESCENARIO['presupuesto_max'],
            fecha_inicio_viaje=ESCENARIO['fecha_inicio'],
            num_dias_disponibles=ESCENARIO['num_dias'],
            hora_inicio_dia=ESCENARIO['hora_inicio_dia'],
            hora_fin_dia=ESCENARIO['hora_fin_dia'],
            auto_fechas=ESCENARIO['auto_fechas'],
            intereses=ESCENARIO['intereses'],
            tamano_poblacion=MOLDE_POBLACION,
            generaciones=MOLDE_GENERACIONES,
            prob_mutacion=0.1,
            num_personas=ESCENARIO['num_personas'],
            min_paradas=ESCENARIO['min_paradas'],
            max_paradas=ESCENARIO['max_paradas'],
            auto_rango_paradas=ESCENARIO['auto_rango_paradas'],
            usar_clima=ESCENARIO['usar_clima'],
            permitir_multiples_vehiculos=ESCENARIO['permitir_multiples_vehiculos'],
            forzar_atractivos=ESCENARIO['forzar_atractivos'],
            forzar_transporte=ESCENARIO['forzar_transporte'],
            seed=i,
            modo_entrenamiento=True,
        )
        f_raw = res.get("frente_pareto_raw", [])
        if f_raw:
            frentes_raw.append(np.array(f_raw, dtype=float))
        hist_F = res.get("historial_F_raw_por_gen", [])
        if hist_F:
            historiales_F_molde.append(hist_F)
        print("OK")

    if not frentes_raw:
        print("[ERROR] Sin soluciones obtenidas en el Molde de Oro. Abortando escenario.")
        return

    pf_ref = _filtrar_no_dominados(np.vstack(frentes_raw))
    pf_ref_raw = _filtrar_no_dominados(np.vstack(frentes_raw))

    ref_point = [float(pf_ref[:, 0].max()) + 0.1, float(pf_ref[:, 1].max()) + 0.1]
    ref_point_raw = [float(pf_ref_raw[:, 0].max()) + 0.1, float(pf_ref_raw[:, 1].max()) + 0.1]

    hist_hv_molde = []
    if historiales_F_molde:
        hist_hv_runs_molde = []
        for hist_F in historiales_F_molde:
            h_hv, _, _ = _procesar_historial_raw(hist_F, pf_ref_raw, ref_point_raw)
            hist_hv_runs_molde.append(h_hv)
        hist_hv_molde = _promediar_historiales(hist_hv_runs_molde)

    archivo.ref_point_json = json.dumps(ref_point)
    archivo.valores_json = json.dumps(pf_ref.tolist())
    archivo.num_puntos = int(len(pf_ref))
    archivo.historial_hv_json = json.dumps(hist_hv_molde)
    db.session.commit()
    print(f"[INFO] Molde: {len(pf_ref)} puntos únicos de Pareto. Ref point: {ref_point}")

    # ============ FASE B: GRID SEARCH ============
    total_configs = len(POBLACIONES) * len(GENERACIONES) * len(MUTACIONES)
    print(f"\n[FASE B] Grid Search ({total_configs} configuraciones x {CORRIDAS_POR_CONFIG} corridas)")

    config_actual = 0
    for pop in POBLACIONES:
        for gen in GENERACIONES:
            for mut in MUTACIONES:
                config_actual += 1
                print(f"  [CONFIG {config_actual}/{total_configs}] P={pop}, G={gen}, M={mut}...", end=" ", flush=True)

                gds, spreads, hvs, tiempos = [], [], [], []
                hist_hv_runs, hist_gd_runs, hist_spread_runs = [], [], []

                for corrida in range(CORRIDAS_POR_CONFIG):
                    inicio = time.perf_counter()
                    res = ejecutar_nsga2(
                        atractivos=atractivos_data,
                        transportes=transportes_data,
                        presupuesto_max=ESCENARIO['presupuesto_max'],
                        fecha_inicio_viaje=ESCENARIO['fecha_inicio'],
                        num_dias_disponibles=ESCENARIO['num_dias'],
                        hora_inicio_dia=ESCENARIO['hora_inicio_dia'],
                        hora_fin_dia=ESCENARIO['hora_fin_dia'],
                        auto_fechas=ESCENARIO['auto_fechas'],
                        intereses=ESCENARIO['intereses'],
                        tamano_poblacion=pop,
                        generaciones=gen,
                        prob_mutacion=mut,
                        num_personas=ESCENARIO['num_personas'],
                        min_paradas=ESCENARIO['min_paradas'],
                        max_paradas=ESCENARIO['max_paradas'],
                        auto_rango_paradas=ESCENARIO['auto_rango_paradas'],
                        usar_clima=ESCENARIO['usar_clima'],
                        permitir_multiples_vehiculos=ESCENARIO['permitir_multiples_vehiculos'],
                        forzar_atractivos=ESCENARIO['forzar_atractivos'],
                        forzar_transporte=ESCENARIO['forzar_transporte'],
                        seed=100 + corrida,
                        modo_entrenamiento=True,
                    )
                    tiempos.append(time.perf_counter() - inicio)

                    f_actual = _extraer_frente(res)
                    if f_actual is not None:
                        gd = _calcular_gd(f_actual, pf_ref)
                        sp = _calcular_spread(f_actual, pf_ref)
                        hv = _calcular_hv(f_actual, ref_point)
                        if gd is not None: gds.append(gd)
                        if sp is not None: spreads.append(sp)
                        if hv is not None: hvs.append(hv)

                    hist_F = res.get("historial_F_raw_por_gen", [])
                    if hist_F:
                        h_hv, h_gd, h_sp = _procesar_historial_raw(hist_F, pf_ref_raw, ref_point_raw)
                        hist_hv_runs.append(h_hv)
                        hist_gd_runs.append(h_gd)
                        hist_spread_runs.append(h_sp)

                gd_prom = float(np.mean(gds)) if gds else None
                sp_prom = float(np.mean(spreads)) if spreads else None
                hv_prom = float(np.mean(hvs)) if hvs else None
                tiempo_prom = float(np.mean(tiempos))

                receta = RecetaEntrenamiento.query.filter_by(
                    id_archivo=archivo.id_archivo, poblacion=pop, generaciones=gen, mutacion=mut
                ).first()

                if not receta:
                    receta = RecetaEntrenamiento(
                        id_archivo=archivo.id_archivo,
                        poblacion=pop,
                        generaciones=gen,
                        mutacion=mut,
                        tiempo_promedio_seg=tiempo_prom,
                        gd_promedio=gd_prom,
                        spread_promedio=sp_prom,
                        hv_promedio=hv_prom,
                        historial_hv_json=json.dumps(_promediar_historiales(hist_hv_runs)),
                        historial_gd_json=json.dumps(_promediar_historiales(hist_gd_runs)),
                        historial_spread_json=json.dumps(_promediar_historiales(hist_spread_runs)),
                    )
                    db.session.add(receta)
                else:
                    receta.tiempo_promedio_seg = tiempo_prom
                    receta.gd_promedio = gd_prom
                    receta.spread_promedio = sp_prom
                    receta.hv_promedio = hv_prom
                    receta.historial_hv_json = json.dumps(_promediar_historiales(hist_hv_runs))
                    receta.historial_gd_json = json.dumps(_promediar_historiales(hist_gd_runs))
                    receta.historial_spread_json = json.dumps(_promediar_historiales(hist_spread_runs))

                db.session.commit()
                print(f"HV={hv_prom:.4f} | GD={gd_prom:.4f} | Spread={sp_prom:.4f} | Tiempo={tiempo_prom:.2f}s")

    archivo.total_ejecuciones = CORRIDAS_MOLDE_ORO + (total_configs * CORRIDAS_POR_CONFIG)
    db.session.commit()

    # ============ SELECCIÓN DE RECETA GANADORA ============
    recetas = RecetaEntrenamiento.query.filter_by(id_archivo=archivo.id_archivo).all()
    recetas_validas = [
        r for r in recetas
        if r.gd_promedio is not None and r.spread_promedio is not None and r.hv_promedio is not None
    ]
    if not recetas_validas:
        print("[ERROR] Sin recetas válidas guardadas.")
        return

    t_min = min(float(r.tiempo_promedio_seg) for r in recetas_validas)
    umbral_tiempo = max(5.0, t_min * 3.0)

    recetas_rapidas = [r for r in recetas_validas if float(r.tiempo_promedio_seg) <= umbral_tiempo]
    if not recetas_rapidas:
        recetas_rapidas = recetas_validas

    receta_ganadora = max(
        recetas_rapidas,
        key=lambda r: (float(r.hv_promedio), -float(r.spread_promedio))
    )

    RecetaEntrenamiento.query.filter_by(
        id_archivo=archivo.id_archivo, es_ganadora=True
    ).update({"es_ganadora": False})

    receta_ganadora.es_ganadora = True
    archivo.poblacion_optima = receta_ganadora.poblacion
    archivo.generaciones_optimas = receta_ganadora.generaciones
    archivo.prob_mutacion_optima = receta_ganadora.mutacion
    db.session.commit()

    print(f"\n[GANADORA SELECCIONADA] P={receta_ganadora.poblacion}, G={receta_ganadora.generaciones}, M={receta_ganadora.mutacion}")
    print(f"  HV: {receta_ganadora.hv_promedio:.4f} | GD: {receta_ganadora.gd_promedio:.4f} | Spread: {receta_ganadora.spread_promedio:.4f} | Tiempo: {receta_ganadora.tiempo_promedio_seg:.2f}s")
