import json
from collections import defaultdict
from sqlalchemy import func, desc
from app import db
from app.models.itinerario import Itinerario
from app.models.itinerario_detalle import ItinerarioDetalle
from app.models.atractivo import Atractivo
from app.models.generacion import Generacion
from app.models.consulta_nsga2 import ConsultaNSGA2
from app.models.archivo_pareto import ArchivoPareto
from app.models.receta_entrenamiento import RecetaEntrenamiento


def obtener_metricas_negocio() -> dict:
    """
    Calcula métricas clave de negocio agregadas desde la base de datos:
    - Total de itinerarios guardados
    - Top 10 atractivos más solicitados
    - Presupuesto promedio (BOB)
    - Duración promedio (días)
    - Tiempo de proceso promedio del algoritmo (segundos)
    - Porcentaje de viabilidad de itinerarios
    - Distribución mensual de itinerarios guardados
    """
    total_itinerarios = Itinerario.query.filter(Itinerario.deleted_at.is_(None)).count()

    # Top 10 atractivos más visitados en itinerarios guardados
    top_atractivos_raw = db.session.query(
        Atractivo.nombre,
        func.count(ItinerarioDetalle.id_detalle).label('total_visitas')
    ).join(
        ItinerarioDetalle, Atractivo.id_atractivo == ItinerarioDetalle.id_atractivo
    ).join(
        Itinerario, ItinerarioDetalle.id_itinerario == Itinerario.id_itinerario
    ).filter(
        Itinerario.deleted_at.is_(None)
    ).group_by(
        Atractivo.nombre
    ).order_by(
        desc('total_visitas')
    ).limit(10).all()

    top_atractivos = [
        {"nombre": row[0], "visitas": int(row[1])}
        for row in top_atractivos_raw
    ]

    # Presupuesto y duración promedio
    prom_presupuesto = db.session.query(
        func.avg(Itinerario.costo_total_bob)
    ).filter(Itinerario.deleted_at.is_(None)).scalar()

    prom_duracion = db.session.query(
        func.avg(Itinerario.dias_totales)
    ).filter(Itinerario.deleted_at.is_(None)).scalar()

    # Tiempo de proceso promedio en consultas de optimización NSGA-II
    prom_tiempo_algoritmo = db.session.query(
        func.avg(ConsultaNSGA2.tiempo_ejecucion_seg)
    ).scalar()

    # Viabilidad de itinerarios
    itinerarios_viables = Itinerario.query.filter(
        Itinerario.deleted_at.is_(None),
        Itinerario.es_viable.is_(True)
    ).count()

    porcentaje_viabilidad = round((itinerarios_viables / total_itinerarios * 100), 1) if total_itinerarios > 0 else 0.0

    # Distribución por mes (Itinerarios guardados por mes)
    itinerarios_por_mes = []
    try:
        registros_mes = db.session.query(
            Generacion.fecha_generacion
        ).join(
            Itinerario, Itinerario.id_generacion == Generacion.id_generacion
        ).filter(
            Itinerario.deleted_at.is_(None)
        ).all()

        conteo_mes = defaultdict(int)
        for reg in registros_mes:
            if reg[0]:
                clave = reg[0].strftime("%Y-%m")
                conteo_mes[clave] += 1

        itinerarios_por_mes = [
            {"mes": mes, "cantidad": conteo_mes[mes]}
            for mes in sorted(conteo_mes.keys())
        ]
    except Exception as e_mes:
        print(f"[WARN REPORTES] Error calculando itinerarios por mes: {e_mes}")

    return {
        "total_itinerarios": total_itinerarios,
        "top_atractivos": top_atractivos,
        "presupuesto_promedio": round(float(prom_presupuesto), 2) if prom_presupuesto is not None else 0.0,
        "duracion_promedio": round(float(prom_duracion), 1) if prom_duracion is not None else 0.0,
        "tiempo_proceso_promedio": round(float(prom_tiempo_algoritmo), 2) if prom_tiempo_algoritmo is not None else 0.0,
        "porcentaje_viabilidad": porcentaje_viabilidad,
        "itinerarios_por_mes": itinerarios_por_mes,
    }


def obtener_metricas_algoritmo(limit: int = 20) -> list[dict]:
    """
    Retorna los últimos registros de ConsultaNSGA2 (generaciones reales en producción)
    con los parámetros elegidos por KNN, métricas de calidad y escenario de referencia vinculado.
    """
    consultas = ConsultaNSGA2.query.order_by(
        desc(ConsultaNSGA2.fecha),
        desc(ConsultaNSGA2.id_consulta),
    ).limit(limit).all()

    filas = []
    for c in consultas:
        hv = float(c.hipervolumen) if c.hipervolumen is not None else None
        gd = float(c.generational_distance) if c.generational_distance is not None else None
        spread = float(c.spread_spacing) if c.spread_spacing is not None else None
        id_arch = c.id_archivo_pareto
        ref_n = int(c.archivo_pareto_rel.num_puntos) if c.archivo_pareto_rel and c.archivo_pareto_rel.num_puntos is not None else 0
        similitud_pct = None

        if c.resultados_json:
            try:
                res_dict = json.loads(c.resultados_json)
                if hv is None:
                    hv = res_dict.get("hipervolumen")
                if gd is None:
                    gd = res_dict.get("gd")
                if spread is None:
                    spread = res_dict.get("spread")
                if id_arch is None:
                    id_arch = res_dict.get("id_archivo_pareto")
                if ref_n == 0:
                    ref_n = int(res_dict.get("num_soluciones_archivo_ref", 0) or 0)
                knn_info = res_dict.get("knn_info") or {}
                if isinstance(knn_info, dict) and knn_info.get("similitud_pct") is not None:
                    similitud_pct = float(knn_info.get("similitud_pct"))
            except Exception:
                pass

        hv_val = round(float(hv), 4) if hv is not None else None
        gd_val = round(float(gd), 4) if gd is not None else None
        sp_val = round(float(spread), 4) if spread is not None else None

        hv_lbl, hv_col = _clasificar_hv(hv_val)
        gd_lbl, gd_col = _clasificar_gd(gd_val, ref_n)
        sp_lbl, sp_col = _clasificar_spread(sp_val, ref_n)

        mut_pct = int(round(float(c.prob_mutacion or 0.15) * 100))
        afinidad_pct = round(float(c.mejor_afinidad) * 100, 1) if c.mejor_afinidad is not None else None

        filas.append({
            "id_consulta": c.id_consulta,
            "fecha": c.fecha.strftime("%Y-%m-%d %H:%M") if c.fecha else "-",
            "tamano_poblacion": int(c.tamano_poblacion),
            "generaciones": int(c.generaciones),
            "prob_mutacion_pct": mut_pct,
            "tiempo_ejecucion_seg": round(float(c.tiempo_ejecucion_seg), 2) if c.tiempo_ejecucion_seg is not None else "-",
            "num_soluciones": int(c.num_soluciones or 0),
            "soluciones_viables": int(c.soluciones_viables or 0),
            "hubo_viables": bool(c.hubo_soluciones_viables),
            "mejor_afinidad_pct": afinidad_pct,
            "presupuesto": round(float(c.presupuesto), 2) if c.presupuesto is not None else 0.0,
            "num_atractivos": int(c.num_atractivos or 0),
            "hipervolumen": hv_val if hv_val is not None else "-",
            "gd": gd_val if gd_val is not None else "-",
            "spread": sp_val if sp_val is not None else "-",
            "hv_label": hv_lbl,
            "hv_color": hv_col,
            "gd_label": gd_lbl,
            "gd_color": gd_col,
            "spread_label": sp_lbl,
            "spread_color": sp_col,
            "id_archivo_pareto": id_arch,
            "num_soluciones_archivo_ref": ref_n,
            "similitud_pct": similitud_pct,
        })

    return filas


def obtener_resumen_consultas_produccion() -> dict:
    """
    Calcula estadísticas agregadas de todas las consultas reales generadas en producción (ConsultaNSGA2)
    y la distribución de escenarios de referencia asignados por el motor KNN.
    """
    consultas = ConsultaNSGA2.query.order_by(ConsultaNSGA2.id_consulta.asc()).all()
    total = len(consultas)
    if total == 0:
        return {
            "total_consultas": 0,
            "consultas_con_ref": 0,
            "cobertura_ref_pct": 0.0,
            "tasa_viabilidad_pct": 0.0,
            "hv_promedio": 0.0,
            "gd_promedio": 0.0,
            "spread_promedio": 0.0,
            "tiempo_promedio": 0.0,
            "distribucion_referencias": [],
        }

    con_ref = 0
    viables = 0
    hvs, gds, spreads, tiempos = [], [], [], []
    conteo_refs = defaultdict(int)

    archivos_map = {a.id_archivo: a for a in ArchivoPareto.query.all()}

    for c in consultas:
        if c.id_archivo_pareto is not None:
            con_ref += 1
            conteo_refs[int(c.id_archivo_pareto)] += 1
        if c.hubo_soluciones_viables:
            viables += 1
        if c.hipervolumen is not None:
            hvs.append(float(c.hipervolumen))
        if c.generational_distance is not None:
            gds.append(float(c.generational_distance))
        if c.spread_spacing is not None:
            spreads.append(float(c.spread_spacing))
        if c.tiempo_ejecucion_seg is not None:
            tiempos.append(float(c.tiempo_ejecucion_seg))

    distribucion = []
    for arch_id, cantidad in sorted(conteo_refs.items(), key=lambda kv: (-kv[1], kv[0])):
        arch = archivos_map.get(arch_id)
        perfil = _describir_perfil_escenario(arch)["perfil"] if arch else "Referencia histórica"
        distribucion.append({
            "id_archivo": arch_id,
            "etiqueta": f"Escenario #{arch_id}",
            "perfil": perfil,
            "cantidad": cantidad,
        })

    return {
        "total_consultas": total,
        "consultas_con_ref": con_ref,
        "cobertura_ref_pct": round((con_ref / total) * 100, 1),
        "tasa_viabilidad_pct": round((viables / total) * 100, 1),
        "hv_promedio": round(sum(hvs) / len(hvs), 4) if hvs else 0.0,
        "gd_promedio": round(sum(gds) / len(gds), 4) if gds else 0.0,
        "spread_promedio": round(sum(spreads) / len(spreads), 4) if spreads else 0.0,
        "tiempo_promedio": round(sum(tiempos) / len(tiempos), 2) if tiempos else 0.0,
        "distribucion_referencias": distribucion,
    }


def _parse_json_seguro(raw: str | None, default):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


def _muestrear_serie(serie: list, max_puntos: int = 60) -> list[dict]:
    """
    Reduce una serie larga de generaciones manteniendo el punto inicial, puntos equidistantes
    y el punto final para graficar curvas suaves sin sobrecargar el navegador.
    """
    if not serie:
        return []
    n = len(serie)
    if n <= max_puntos:
        return [
            {"gen": idx + 1, "valor": round(float(val), 4) if val is not None else None}
            for idx, val in enumerate(serie)
        ]

    indices = sorted(set(
        [0, n - 1] + [int(round(i * (n - 1) / (max_puntos - 1))) for i in range(max_puntos)]
    ))
    return [
        {"gen": idx + 1, "valor": round(float(serie[idx]), 4) if serie[idx] is not None else None}
        for idx in indices
    ]


def _describir_perfil_escenario(archivo: ArchivoPareto) -> dict:
    """
    Genera una descripción entendible en español a partir de las características guardadas
    del escenario (sin exponer términos técnicos complejos).
    """
    vec = _parse_json_seguro(archivo.vector_instancia_json, [])
    if not isinstance(vec, list) or len(vec) < 17:
        return {
            "titulo": f"Escenario #{archivo.id_archivo}",
            "perfil": "Configuración general de viaje",
            "tipo_escenario": "Entrenado",
            "dias_aprox": "-",
            "atractivos_aprox": "-",
            "clima_texto": "No especificado",
            "modo_texto": "Estándar",
            "forzar_texto": "Flexible",
        }

    dias_aprox = max(1, int(round(float(vec[2]) * 14)))
    atractivos_aprox = max(1, int(round(float(vec[1]) * 50)))
    modo_manual = float(vec[0]) >= 0.5
    forzar_todos = float(vec[3]) >= 0.5
    con_clima = float(vec[16]) >= 0.5
    sin_zonas_trafico = float(vec[9]) == 0.0

    modo_texto = "Selección manual" if modo_manual else "Catálogo automático"
    clima_texto = "Con clima" if con_clima else "Sin clima"
    forzar_texto = "Atractivos obligatorios" if forzar_todos else "Atractivos flexibles"

    if int(archivo.total_ejecuciones or 0) >= 350 or sin_zonas_trafico:
        if dias_aprox <= 2 and atractivos_aprox <= 5:
            tipo_escenario = "Extremo Mínimo"
        else:
            tipo_escenario = "Extremo Máximo"
    else:
        tipo_escenario = "Escenario Intermedio"

    dia_label = "día" if dias_aprox == 1 else "días"
    perfil = f"{dias_aprox} {dia_label} · ~{atractivos_aprox} atractivos · {clima_texto}"

    return {
        "titulo": f"Escenario #{archivo.id_archivo}",
        "perfil": perfil,
        "tipo_escenario": tipo_escenario,
        "dias_aprox": dias_aprox,
        "atractivos_aprox": atractivos_aprox,
        "clima_texto": clima_texto,
        "modo_texto": modo_texto,
        "forzar_texto": forzar_texto,
    }


def _clasificar_hv(hv: float | None) -> tuple[str, str]:
    if hv is None:
        return "Sin dato", "secondary"
    if hv >= 0.80:
        return "Excelente", "success"
    if hv >= 0.60:
        return "Bueno", "primary"
    return "Mejorable", "warning"


def _clasificar_gd(gd: float | None, num_puntos: int) -> tuple[str, str]:
    if gd is None:
        return "Sin dato", "secondary"
    if num_puntos <= 1 and gd >= 0.99:
        return "Solución única", "info"
    if gd <= 0.02:
        return "Excelente", "success"
    if gd <= 0.08:
        return "Bueno", "primary"
    return "Alejado", "warning"


def _clasificar_spread(sp: float | None, num_puntos: int) -> tuple[str, str]:
    if sp is None:
        return "Sin dato", "secondary"
    if num_puntos <= 1 and sp == 0.0:
        return "Solución única", "info"
    if sp <= 0.40:
        return "Muy variado", "success"
    if sp <= 0.70:
        return "Moderado", "primary"
    return "Concentrado", "warning"


def obtener_metricas_entrenamiento() -> dict:
    """
    Consolida la información de ArchivoPareto (escenarios de referencia y configuración ganadora)
    y RecetaEntrenamiento (todas las configuraciones evaluadas durante la calibración)
    para mostrar tablas, gráficos comparativos y resúmenes claros en el módulo de reportes.
    """
    archivos = ArchivoPareto.query.order_by(ArchivoPareto.id_archivo.asc()).all()
    if not archivos:
        return {
            "resumen": {
                "total_escenarios": 0,
                "total_recetas": 0,
                "total_ejecuciones": 0,
                "total_puntos_pareto": 0,
                "hv_promedio_ganadoras": 0.0,
                "tiempo_promedio_ganadoras": 0.0,
            },
            "escenarios": [],
        }

    recetas_todas = RecetaEntrenamiento.query.order_by(
        RecetaEntrenamiento.id_archivo.asc(),
        desc(RecetaEntrenamiento.es_ganadora),
        desc(RecetaEntrenamiento.hv_promedio),
        RecetaEntrenamiento.tiempo_promedio_seg.asc(),
    ).all()

    recetas_por_archivo = defaultdict(list)
    for r in recetas_todas:
        recetas_por_archivo[r.id_archivo].append(r)

    escenarios_lista = []
    hv_ganadoras = []
    tiempos_ganadoras = []
    total_puntos_pareto = 0
    total_ejecuciones = 0

    for arch in archivos:
        info = _describir_perfil_escenario(arch)
        num_puntos = int(arch.num_puntos or 0)
        tot_ej = int(arch.total_ejecuciones or 0)
        total_puntos_pareto += num_puntos
        total_ejecuciones += tot_ej

        recetas_arch = recetas_por_archivo.get(arch.id_archivo, [])
        recetas_serializadas = []
        receta_ganadora_dict = None

        for r in recetas_arch:
            hv_val = round(float(r.hv_promedio), 4) if r.hv_promedio is not None else None
            gd_val = round(float(r.gd_promedio), 4) if r.gd_promedio is not None else None
            sp_val = round(float(r.spread_promedio), 4) if r.spread_promedio is not None else None
            t_val = round(float(r.tiempo_promedio_seg), 2) if r.tiempo_promedio_seg is not None else None
            mut_val = round(float(r.mutacion), 2) if r.mutacion is not None else 0.0

            hv_lbl, hv_col = _clasificar_hv(hv_val)
            gd_lbl, gd_col = _clasificar_gd(gd_val, num_puntos)
            sp_lbl, sp_col = _clasificar_spread(sp_val, num_puntos)

            item_r = {
                "id_receta": r.id_receta,
                "poblacion": int(r.poblacion),
                "generaciones": int(r.generaciones),
                "mutacion": mut_val,
                "mutacion_pct": int(round(mut_val * 100)),
                "hv": hv_val,
                "gd": gd_val,
                "spread": sp_val,
                "tiempo": t_val,
                "hv_label": hv_lbl,
                "hv_color": hv_col,
                "gd_label": gd_lbl,
                "gd_color": gd_col,
                "spread_label": sp_lbl,
                "spread_color": sp_col,
                "es_ganadora": bool(r.es_ganadora),
                "historial_hv": _muestrear_serie(_parse_json_seguro(r.historial_hv_json, [])),
            }
            recetas_serializadas.append(item_r)
            if r.es_ganadora and receta_ganadora_dict is None:
                receta_ganadora_dict = item_r

        if receta_ganadora_dict is None and recetas_serializadas:
            receta_ganadora_dict = recetas_serializadas[0]

        if receta_ganadora_dict:
            if receta_ganadora_dict["hv"] is not None:
                hv_ganadoras.append(receta_ganadora_dict["hv"])
            if receta_ganadora_dict["tiempo"] is not None:
                tiempos_ganadoras.append(receta_ganadora_dict["tiempo"])

        # Métricas comparativas dentro del mismo escenario
        recetas_con_tiempo = [r for r in recetas_serializadas if r["tiempo"] is not None]
        recetas_con_hv = [r for r in recetas_serializadas if r["hv"] is not None]

        mas_rapida = min(recetas_con_tiempo, key=lambda x: x["tiempo"]) if recetas_con_tiempo else None
        mas_pesada = max(
            recetas_con_tiempo,
            key=lambda x: (x["poblacion"] * x["generaciones"], x["tiempo"])
        ) if recetas_con_tiempo else None
        mejor_hv_item = max(recetas_con_hv, key=lambda x: x["hv"]) if recetas_con_hv else None

        ahorro_tiempo_pct = 0.0
        calidad_relativa_pct = 100.0
        if receta_ganadora_dict and mas_pesada and mas_pesada["tiempo"] and mas_pesada["tiempo"] > 0:
            if receta_ganadora_dict["tiempo"] is not None:
                ahorro = (1.0 - (receta_ganadora_dict["tiempo"] / mas_pesada["tiempo"])) * 100.0
                ahorro_tiempo_pct = round(max(0.0, ahorro), 1)
        if receta_ganadora_dict and mejor_hv_item and mejor_hv_item["hv"] and mejor_hv_item["hv"] > 0:
            if receta_ganadora_dict["hv"] is not None:
                calidad_relativa_pct = round(min(100.0, (receta_ganadora_dict["hv"] / mejor_hv_item["hv"]) * 100.0), 1)

        prom_hv_esc = round(sum(r["hv"] for r in recetas_con_hv) / len(recetas_con_hv), 4) if recetas_con_hv else None
        prom_tiempo_esc = round(sum(r["tiempo"] for r in recetas_con_tiempo) / len(recetas_con_tiempo), 2) if recetas_con_tiempo else None

        # Puntos del frente de referencia (valores_json)
        puntos_raw = _parse_json_seguro(arch.valores_json, [])
        puntos_frente = []
        for p in puntos_raw:
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                try:
                    # f1 = -afinidad (+ penalización), f2 = tiempo relativo
                    afinidad_aprox = round(-float(p[0]), 4)
                    tiempo_rel = round(float(p[1]), 4)
                    puntos_frente.append({"tiempo_rel": tiempo_rel, "afinidad": afinidad_aprox})
                except Exception:
                    continue

        historial_molde = _muestrear_serie(_parse_json_seguro(arch.historial_hv_json, []))

        escenarios_lista.append({
            "id_archivo": arch.id_archivo,
            "titulo": info["titulo"],
            "perfil": info["perfil"],
            "tipo_escenario": info["tipo_escenario"],
            "dias_aprox": info["dias_aprox"],
            "atractivos_aprox": info["atractivos_aprox"],
            "clima_texto": info["clima_texto"],
            "modo_texto": info["modo_texto"],
            "forzar_texto": info["forzar_texto"],
            "num_puntos": num_puntos,
            "total_ejecuciones": tot_ej,
            "total_recetas": len(recetas_serializadas),
            "poblacion_optima": arch.poblacion_optima,
            "generaciones_optimas": arch.generaciones_optimas,
            "prob_mutacion_optima": round(float(arch.prob_mutacion_optima), 2) if arch.prob_mutacion_optima is not None else None,
            "prob_mutacion_pct": int(round(float(arch.prob_mutacion_optima) * 100)) if arch.prob_mutacion_optima is not None else 0,
            "fecha_actualizacion": arch.fecha_actualizacion.strftime("%Y-%m-%d %H:%M") if arch.fecha_actualizacion else "-",
            "ganadora": receta_ganadora_dict,
            "mas_rapida": mas_rapida,
            "mas_pesada": mas_pesada,
            "prom_hv": prom_hv_esc,
            "prom_tiempo": prom_tiempo_esc,
            "ahorro_tiempo_pct": ahorro_tiempo_pct,
            "calidad_relativa_pct": calidad_relativa_pct,
            "historial_molde": historial_molde,
            "puntos_frente": puntos_frente,
            "recetas": recetas_serializadas,
        })

    return {
        "resumen": {
            "total_escenarios": len(escenarios_lista),
            "total_recetas": len(recetas_todas),
            "total_ejecuciones": total_ejecuciones,
            "total_puntos_pareto": total_puntos_pareto,
            "hv_promedio_ganadoras": round(sum(hv_ganadoras) / len(hv_ganadoras), 4) if hv_ganadoras else 0.0,
            "tiempo_promedio_ganadoras": round(sum(tiempos_ganadoras) / len(tiempos_ganadoras), 2) if tiempos_ganadoras else 0.0,
        },
        "escenarios": escenarios_lista,
    }
