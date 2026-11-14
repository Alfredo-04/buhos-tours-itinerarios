import time
import json
import numpy as np
from pymoo.indicators.hv import HV

from app import create_app, db
from app.models.archivo_pareto import ArchivoPareto
from app.models.receta_entrenamiento import RecetaEntrenamiento
from app.services.nsga2_service import ejecutar_nsga2
from app.services.itinerario_service import preparar_datos_nsga2
from app.services.metricas_pareto_service import extraer_vector_instancia

app = create_app()

# ==========================================
# CONFIGURACIÓN DE CORRIDAS
# ==========================================
CORRIDAS_MOLDE_ORO = 20      # Molde de oro (Fase A) — 20 corridas
CORRIDAS_POR_CONFIG = 10     # Grid Search (Fase B) — 10 corridas

# ==========================================
# EXTREMO MIN
# ==========================================
ESCENARIO_MIN = {
    "nombre": "EXTREMO MIN - 1 día, 1 persona, caminata, presupuesto 50, 2 paradas",
    "atractivos_ids": [],
    "categorias_activas_ids": [1],
    "subcategorias_activas_ids": [3],
    "transporte_ids": [4],
    "forzar_transporte": True,
    "presupuesto_max": 50.0,
    "num_dias": 1,
    "num_personas": 1,
    "fecha_inicio": "2026-11-15",
    "hora_inicio_dia": "06:00",
    "hora_fin_dia": "12:00",
    "auto_fechas": False,
    "auto_rango_paradas": False,
    "min_paradas": 2,
    "max_paradas": 2,
    "permitir_multiples_vehiculos": False,
    "usar_clima": False,
    "forzar_atractivos": False,
    "intereses": {
        "Cultural": 1.0, "Sitios Patrimoniales y Calles Históricas": 1.0,
        "Naturaleza": 0.0, "Urbano": 0.0, "Gastronomía": 0.0,
        "Museos": 0.0, "Iglesias y Templos": 0.0,
        "Miradores": 0.0, "Parques y Bosquecillos": 0.0, "Áreas Protegidas": 0.0,
        "Plazas": 0.0, "Mercados Tradicionales": 0.0, "Gastronomía Tradicional": 0.0
    }
}

# ==========================================
# EXTREMO MAX (forzar_atractivos=True — extremo puro)
# ==========================================
ESCENARIO_MAX = {
    "nombre": "EXTREMO MAX - 14 días, 50 personas, todos los transportes, 31 atractivos forzados",
    "atractivos_ids": list(range(1, 32)),
    "categorias_activas_ids": [1, 2, 3, 4],
    "subcategorias_activas_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9],
    "transporte_ids": [1, 2, 3, 4],
    "forzar_transporte": False,
    "presupuesto_max": 100000.0,
    "num_dias": 14,
    "num_personas": 50,
    "fecha_inicio": "2026-11-15",
    "hora_inicio_dia": "06:00",
    "hora_fin_dia": "19:59",
    "auto_fechas": False,
    "auto_rango_paradas": False,
    "min_paradas": 2,
    "max_paradas": 31,
    "permitir_multiples_vehiculos": True,
    "usar_clima": True,
    "forzar_atractivos": True,   # ← EXTREMO PURO (degenerado, 1 solución esperada)
    "intereses": {
        "Cultural": 1.0, "Naturaleza": 1.0, "Urbano": 1.0, "Gastronomía": 1.0,
        "Museos": 1.0, "Iglesias y Templos": 1.0, "Sitios Patrimoniales y Calles Históricas": 1.0,
        "Miradores": 1.0, "Parques y Bosquecillos": 1.0, "Áreas Protegidas": 1.0,
        "Plazas": 1.0, "Mercados Tradicionales": 1.0, "Gastronomía Tradicional": 1.0
    }
}

# ==========================================
# GRID SEARCH
# ==========================================
MOLDE_POBLACION = 200
MOLDE_GENERACIONES = 300
POBLACIONES = [40, 80, 150, 300]
GENERACIONES = [50, 100, 200]
MUTACIONES = [0.05, 0.15, 0.25]

# ==========================================
# HELPERS
# ==========================================

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

def _promediar_historiales(lista_historiales):
    if not lista_historiales:
        return []
    max_len = max(len(h) for h in lista_historiales)
    resultado = []
    for i in range(max_len):
        valores = [h[i] for h in lista_historiales if i < len(h) and h[i] is not None]
        resultado.append(round(float(np.mean(valores)), 6) if valores else None)
    return resultado

def _procesar_historial_raw(historial_F_raw, pf_ref_raw, ref_point_raw):
    hist_hv, hist_gd, hist_spread = [], [], []
    for F_gen_list in historial_F_raw:
        if not F_gen_list:
            hist_hv.append(None)
            hist_gd.append(None)
            hist_spread.append(None)
            continue
        F_gen = np.array(F_gen_list, dtype=float)
        F_frente = _filtrar_no_dominados(F_gen)
        hv = _calcular_hv(F_frente, ref_point_raw) if len(F_frente) > 0 else None
        gd = _calcular_gd(F_frente, pf_ref_raw) if pf_ref_raw is not None and len(pf_ref_raw) > 0 else None
        sp = _calcular_spread(F_frente, pf_ref_raw)
        hist_hv.append(hv)
        hist_gd.append(gd)
        hist_spread.append(sp)
    return hist_hv, hist_gd, hist_spread


def entrenar_escenario(ESCENARIO):
    print("\n" + "="*70)
    print(f"INICIANDO ENTRENAMIENTO: {ESCENARIO['nombre']}")
    print(f"  Molde de oro: {CORRIDAS_MOLDE_ORO} corridas | Grid Search: {CORRIDAS_POR_CONFIG} corridas")
    print("="*70)

    atractivos_data, transportes_data = preparar_datos_nsga2(
        atractivos_ids=ESCENARIO['atractivos_ids'],
        transporte_ids=ESCENARIO['transporte_ids'],
        categorias_activas_ids=ESCENARIO.get('categorias_activas_ids'),
        subcategorias_activas_ids=ESCENARIO.get('subcategorias_activas_ids'),
    )
    print(f"[INFO] Atractivos: {len(atractivos_data)}, Transportes: {len(transportes_data)}")

    contexto_vector = {
        "atractivos_ids": ESCENARIO['atractivos_ids'],
        "num_dias": ESCENARIO['num_dias'],
        "presupuesto_max": ESCENARIO['presupuesto_max'],
        "num_personas": ESCENARIO['num_personas'],
        "intereses": ESCENARIO['intereses'],
        "usar_clima": ESCENARIO['usar_clima'],
        "forzar_atractivos": ESCENARIO['forzar_atractivos'],
    }
    vector = extraer_vector_instancia(
        contexto=contexto_vector,
        atractivos_data=atractivos_data,
    )
    print(f"[INFO] Vector ({len(vector)}D): {vector.round(4).tolist()}")

    archivo = ArchivoPareto(
        vector_instancia_json=json.dumps(vector.tolist()),
        ref_point_json=json.dumps([0.0, 1.0]),
        valores_json=json.dumps([]),
        num_puntos=0,
        total_ejecuciones=0,
    )
    db.session.add(archivo)
    db.session.commit()
    print(f"[INFO] ArchivoPareto id={archivo.id_archivo}")

    # ============ FASE A: MOLDE DE ORO (20 corridas) ============
    print(f"\n[FASE A] Molde de Oro (P={MOLDE_POBLACION}, G={MOLDE_GENERACIONES}, {CORRIDAS_MOLDE_ORO} corridas)")
    
    frentes_decoded, frentes_raw, historiales_F_molde = [], [], []

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
        f_dec = _extraer_frente(res)
        if f_dec is not None:
            frentes_decoded.append(f_dec)
        f_raw = res.get("frente_pareto_raw", [])
        if f_raw:
            frentes_raw.append(np.array(f_raw, dtype=float))
        hist_F = res.get("historial_F_raw_por_gen", [])
        if hist_F:
            historiales_F_molde.append(hist_F)
        print("OK")

    if not frentes_decoded or not frentes_raw:
        print("[ERROR] Sin soluciones. Abortando escenario.")
        return

    pf_ref = _filtrar_no_dominados(np.vstack(frentes_decoded))
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
    print(f"[INFO] Molde: {len(pf_ref)} puntos únicos. Ref point: {ref_point}")

    # ============ FASE B: GRID SEARCH (10 corridas) ============
    total_configs = len(POBLACIONES) * len(GENERACIONES) * len(MUTACIONES)
    print(f"\n[FASE B] Grid Search ({total_configs} configs × {CORRIDAS_POR_CONFIG} corridas)")
    
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
                        seed=corrida,
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
                t_prom = float(np.mean(tiempos))

                receta = RecetaEntrenamiento(
                    id_archivo=archivo.id_archivo,
                    poblacion=pop,
                    generaciones=gen,
                    mutacion=mut,
                    gd_promedio=gd_prom,
                    spread_promedio=sp_prom,
                    hv_promedio=hv_prom,
                    tiempo_promedio_seg=t_prom,
                    historial_hv_json=json.dumps(_promediar_historiales(hist_hv_runs)),
                    historial_gd_json=json.dumps(_promediar_historiales(hist_gd_runs)),
                    historial_spread_json=json.dumps(_promediar_historiales(hist_spread_runs)),
                    es_ganadora=False,
                )
                db.session.add(receta)
                db.session.commit()
                print(f"GD={gd_prom:.6f}, Spread={sp_prom:.6f}, HV={hv_prom:.6f}, t={t_prom:.2f}s")

    archivo.total_ejecuciones = CORRIDAS_MOLDE_ORO + (total_configs * CORRIDAS_POR_CONFIG)
    db.session.commit()

    # ============ SELECCIÓN DE RECETA GANADORA ============
    recetas = RecetaEntrenamiento.query.filter_by(id_archivo=archivo.id_archivo).all()
    recetas_validas = [r for r in recetas if r.gd_promedio is not None and r.spread_promedio is not None]
    if not recetas_validas:
        print("[ERROR] Sin recetas válidas.")
        return

    receta_ganadora = min(recetas_validas, key=lambda r: (float(r.gd_promedio), float(r.spread_promedio)))
    receta_ganadora.es_ganadora = True
    archivo.poblacion_optima = receta_ganadora.poblacion
    archivo.generaciones_optimas = receta_ganadora.generaciones
    archivo.prob_mutacion_optima = receta_ganadora.mutacion
    db.session.commit()

    print(f"\n[GANADORA] P={receta_ganadora.poblacion}, G={receta_ganadora.generaciones}, M={receta_ganadora.mutacion}")
    print(f"  GD: {receta_ganadora.gd_promedio}, Spread: {receta_ganadora.spread_promedio}, HV: {receta_ganadora.hv_promedio}")


def main():
    with app.app_context():
        for esc in [ESCENARIO_MIN, ESCENARIO_MAX]:
            entrenar_escenario(esc)
        print("\n" + "="*70)
        print("TODOS LOS ESCENARIOS ENTRENADOS.")
        print("="*70)

if __name__ == "__main__":
    main()