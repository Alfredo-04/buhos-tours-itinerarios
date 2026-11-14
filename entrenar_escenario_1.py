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
# DEFINICIÓN FIJA DEL ESCENARIO 1
# ==========================================
ESCENARIO = {
    "nombre": "Escenario 1 - Plazas y Parques",
    "atractivos_ids": [3, 6, 19, 26, 27, 28, 29, 30],
    "transporte_ids": [1],
    "presupuesto_max": 1000.0,
    "num_dias": 3,
    "hora_inicio_dia": "09:00",
    "hora_fin_dia": "18:00",
    "fecha_inicio": "2026-11-09",
    "num_personas": 1,
    "intereses": {"Parques y Bosquecillos": 0.70, "Plazas": 0.70},
    "usar_clima": False,
    "auto_fechas": False,
    "auto_rango_paradas": False,
    "min_paradas": 4,
    "max_paradas": 10,
    "permitir_multiples_vehiculos": False,
    "forzar_atractivos": False,
    "forzar_transporte": False,
}

# === CONFIGURACIÓN DEFINITIVA ===
CORRIDAS_POR_CONFIG = 20
MOLDE_POBLACION = 200
MOLDE_GENERACIONES = 300

POBLACIONES = [40, 80, 150, 300]
GENERACIONES = [50, 100, 200]
MUTACIONES = [0.05, 0.15, 0.25]
# Total: 4 × 3 × 3 = 36 configuraciones


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
    """
    Spread (Delta) de Deb et al. (2002).
    🔧 FIX 1: Filtrar duplicados y dominados ANTES de calcular.
    La fórmula original NO está acotada a [0,1] si el frente tiene
    duplicados o outliers. Al filtrar, se cumple la condición matemática
    y el valor resultante es interpretable.
    """
    if frente_actual is None or len(frente_actual) < 2:
        return 0.0

    # 🔧 FIX: Filtrar el frente antes de calcular
    f_limpio = _filtrar_no_dominados(np.array(frente_actual, dtype=float))
    if f_limpio is None or len(f_limpio) < 2:
        return 0.0

    # Normalización basada en frente_ref (o frente limpio si no hay ref)
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
    """Promedia N historiales elemento a elemento (ignora None)."""
    if not lista_historiales:
        return []
    max_len = max(len(h) for h in lista_historiales)
    resultado = []
    for i in range(max_len):
        valores = [h[i] for h in lista_historiales if i < len(h) and h[i] is not None]
        resultado.append(round(float(np.mean(valores)), 6) if valores else None)
    return resultado


def _procesar_historial_raw(historial_F_raw, pf_ref_raw, ref_point_raw):
    """Calcula HV, GD, Spread por generación desde F raw."""
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


# ==========================================
# MAIN
# ==========================================

def main():
    with app.app_context():
        print("=" * 60)
        print(f"INICIANDO ENTRENAMIENTO: {ESCENARIO['nombre']}")
        print("=" * 60)

        # 1. Vector de instancia
        atractivos_data, _ = preparar_datos_nsga2(
            atractivos_ids=ESCENARIO['atractivos_ids'],
            transporte_ids=ESCENARIO['transporte_ids'],
        )
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
        print(f"[INFO] Vector de instancia ({len(vector)}D): {vector.tolist()}")

        # 2. Crear ArchivoPareto (vacío, se llena después)
        archivo = ArchivoPareto(
            vector_instancia_json=json.dumps(vector.tolist()),
            ref_point_json=json.dumps([0.0, 1.0]),
            valores_json=json.dumps([]),
            num_puntos=0,
            total_ejecuciones=0,
        )
        db.session.add(archivo)
        db.session.commit()
        print(f"[INFO] ArchivoPareto creado con id={archivo.id_archivo}")

        # ============ FASE A: MOLDE DE ORO ============
        print("\n" + "=" * 60)
        print(f"FASE A: MOLDE DE ORO (P={MOLDE_POBLACION}, G={MOLDE_GENERACIONES}, {CORRIDAS_POR_CONFIG} corridas)")
        print("=" * 60)

        frentes_decoded = []
        frentes_raw = []
        historiales_F_molde = []  # 🔧 FIX 3: Guardar historiales del molde

        for i in range(CORRIDAS_POR_CONFIG):
            print(f"  Corrida molde {i+1}/{CORRIDAS_POR_CONFIG}...", end=" ", flush=True)
            res = ejecutar_nsga2(
                atractivos=atractivos_data,
                transportes=[{"id": 1, "nombre": "Taxi", "tipo": "Privado", "tipo_costo": "por_dia",
                              "velocidad_promedio_kmh": 15.0, "costo": 150.0, "capacidad": 4}],
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
                modo_entrenamiento=True,
            )
            f_dec = _extraer_frente(res)
            if f_dec is not None:
                frentes_decoded.append(f_dec)
            f_raw = res.get("frente_pareto_raw", [])
            if f_raw:
                frentes_raw.append(np.array(f_raw, dtype=float))

            # 🔧 FIX 3: Guardar historial F raw del molde
            hist_F = res.get("historial_F_raw_por_gen", [])
            if hist_F:
                historiales_F_molde.append(hist_F)

            print("OK")

        if not frentes_decoded or not frentes_raw:
            print("[ERROR] Sin soluciones. Abortando.")
            return

        pf_ref = _filtrar_no_dominados(np.vstack(frentes_decoded))
        pf_ref_raw = _filtrar_no_dominados(np.vstack(frentes_raw))

        # 🔧 FIX 2: ref_point con +0.1 en AMBOS ejes (antes era +10.0)
        ref_point = [float(pf_ref[:, 0].max()) + 0.1, float(pf_ref[:, 1].max()) + 0.1]
        ref_point_raw = [float(pf_ref_raw[:, 0].max()) + 0.1, float(pf_ref_raw[:, 1].max()) + 0.1]

        # 🔧 FIX 3: Calcular historial de HV por generación del molde
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
        # 🔧 FIX 3: Guardar historial_hv_json en ArchivoPareto
        archivo.historial_hv_json = json.dumps(hist_hv_molde)
        db.session.commit()
        print(f"[INFO] Molde de oro: {len(pf_ref)} puntos únicos")
        print(f"[INFO] Ref point decoded: {ref_point}")
        print(f"[INFO] Ref point raw: {ref_point_raw}")
        print(f"[INFO] Historial HV del molde: {len(hist_hv_molde)} generaciones")

        # ============ FASE B: GRID SEARCH 3D ============
        print("\n" + "=" * 60)
        print(f"FASE B: GRID SEARCH ({len(POBLACIONES)} pop × {len(GENERACIONES)} gen × {len(MUTACIONES)} mut = {len(POBLACIONES)*len(GENERACIONES)*len(MUTACIONES)} configs)")
        print("=" * 60)

        total_configs = len(POBLACIONES) * len(GENERACIONES) * len(MUTACIONES)
        config_actual = 0

        for pop in POBLACIONES:
            for gen in GENERACIONES:
                for mut in MUTACIONES:
                    config_actual += 1
                    print(f"\n[CONFIG {config_actual}/{total_configs}] P={pop}, G={gen}, M={mut}")

                    gds, spreads, hvs, tiempos = [], [], [], []
                    hist_hv_runs, hist_gd_runs, hist_spread_runs = [], [], []

                    for corrida in range(CORRIDAS_POR_CONFIG):
                        inicio = time.perf_counter()
                        res = ejecutar_nsga2(
                            atractivos=atractivos_data,
                            transportes=[{"id": 1, "nombre": "Taxi", "tipo": "Privado", "tipo_costo": "por_dia",
                                          "velocidad_promedio_kmh": 15.0, "costo": 150.0, "capacidad": 4}],
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

                    hist_hv_prom = _promediar_historiales(hist_hv_runs)
                    hist_gd_prom = _promediar_historiales(hist_gd_runs)
                    hist_spread_prom = _promediar_historiales(hist_spread_runs)

                    receta = RecetaEntrenamiento(
                        id_archivo=archivo.id_archivo,
                        poblacion=pop,
                        generaciones=gen,
                        mutacion=mut,
                        gd_promedio=gd_prom,
                        spread_promedio=sp_prom,
                        hv_promedio=hv_prom,
                        tiempo_promedio_seg=t_prom,
                        historial_hv_json=json.dumps(hist_hv_prom),
                        historial_gd_json=json.dumps(hist_gd_prom),
                        historial_spread_json=json.dumps(hist_spread_prom),
                        es_ganadora=False,
                    )
                    db.session.add(receta)
                    db.session.commit()
                    print(f"  → GD={gd_prom}, Spread={sp_prom}, HV={hv_prom}, t={t_prom:.2f}s")

        archivo.total_ejecuciones = CORRIDAS_POR_CONFIG + (total_configs * CORRIDAS_POR_CONFIG)
        db.session.commit()
        print(f"\n[INFO] total_ejecuciones actualizado a {archivo.total_ejecuciones}")

        # ============ SELECCIÓN DE RECETA GANADORA ============
        print("\n" + "=" * 60)
        print("SELECCIONANDO RECETA GANADORA")
        print("=" * 60)

        recetas = RecetaEntrenamiento.query.filter_by(id_archivo=archivo.id_archivo).all()
        recetas_validas = [r for r in recetas if r.gd_promedio is not None and r.spread_promedio is not None]
        if not recetas_validas:
            print("[ERROR] No hay recetas válidas.")
            return

        receta_ganadora = min(recetas_validas, key=lambda r: (float(r.gd_promedio), float(r.spread_promedio)))
        receta_ganadora.es_ganadora = True

        archivo.poblacion_optima = receta_ganadora.poblacion
        archivo.generaciones_optimas = receta_ganadora.generaciones
        archivo.prob_mutacion_optima = receta_ganadora.mutacion
        db.session.commit()

        print(f"\n[GANADORA] Receta #{receta_ganadora.id_receta}")
        print(f"  Población: {receta_ganadora.poblacion}")
        print(f"  Generaciones: {receta_ganadora.generaciones}")
        print(f"  Mutación: {receta_ganadora.mutacion}")
        print(f"  GD: {receta_ganadora.gd_promedio}")
        print(f"  Spread: {receta_ganadora.spread_promedio}")
        print(f"  HV: {receta_ganadora.hv_promedio}")
        print(f"  Tiempo: {receta_ganadora.tiempo_promedio_seg}s")

        # Verificación final de rango
        print("\n" + "=" * 60)
        print("VERIFICACIÓN DE RANGOS")
        print("=" * 60)
        spreads_fuera_rango = [r.id_receta for r in recetas_validas if r.spread_promedio is not None and (r.spread_promedio < 0 or r.spread_promedio > 1)]
        hvs_fuera_rango = [r.id_receta for r in recetas_validas if r.hv_promedio is not None and (r.hv_promedio < 0 or r.hv_promedio > 1)]
        if spreads_fuera_rango:
            print(f"[ALERTA] {len(spreads_fuera_rango)} recetas con spread fuera de [0,1]: {spreads_fuera_rango[:10]}")
        else:
            print(f"[OK] Todos los spreads están en [0,1]")
        if hvs_fuera_rango:
            print(f"[ALERTA] {len(hvs_fuera_rango)} recetas con HV fuera de [0,1]: {hvs_fuera_rango[:10]}")
        else:
            print(f"[OK] Todos los HV están en [0,1]")

        print("\n" + "=" * 60)
        print("ENTRENAMIENTO COMPLETADO")
        print("=" * 60)


if __name__ == "__main__":
    main()