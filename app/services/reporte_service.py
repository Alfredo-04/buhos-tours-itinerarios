import json
from datetime import datetime, date
from collections import defaultdict
from sqlalchemy import func, desc, cast, Date
from app import db
from app.models.itinerario import Itinerario
from app.models.itinerario_detalle import ItinerarioDetalle
from app.models.atractivo import Atractivo
from app.models.transporte import Transporte
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


def obtener_metricas_algoritmo(limit: int | None = None) -> list[dict]:
    """
    Retorna los registros de ConsultaNSGA2 (generaciones reales en producción)
    con los parámetros elegidos por KNN, métricas de calidad y escenario de referencia vinculado.
    Por defecto retorna todas las consultas registradas si limit es None.
    """
    q = ConsultaNSGA2.query.order_by(
        desc(ConsultaNSGA2.fecha),
        desc(ConsultaNSGA2.id_consulta),
    )
    if limit is not None:
        q = q.limit(limit)
    consultas = q.all()

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


# ==============================================================================
# LISTA DE COTEJO DE VIABILIDAD OPERATIVA (MÉTODOS AUDITORÍA METODOLÓGICA)
# ==============================================================================

def parsear_dias_cerrado_set(dias_str: str | None) -> set[str]:
    """Parsea y normaliza días de cierre a minúsculas sin acento."""
    if not dias_str:
        return set()
    import unicodedata
    def normalizar(s: str) -> str:
        s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
        return s.strip().lower()
    return {normalizar(d) for d in str(dias_str).split(',') if d.strip()}


DIAS_SEMANA_NORM = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']


def _time_a_minutos(t) -> int | None:
    """Convierte objeto time o string HH:MM / HH:MM:SS a minutos desde medianoche."""
    if t is None:
        return None
    if isinstance(t, str):
        t_str = t.strip()
        parts = t_str.split(':')
        if len(parts) >= 2:
            try:
                return int(parts[0]) * 60 + int(parts[1])
            except ValueError:
                return None
        return None
    if hasattr(t, 'hour') and hasattr(t, 'minute'):
        return t.hour * 60 + t.minute
    return None


def evaluar_lista_cotejo_itinerario(
    paradas: list[dict],
    num_personas: int = 1,
    cat_atractivos: dict | None = None,
    cat_transportes: dict | None = None
) -> dict:
    """
    Evalúa las 4 condiciones de la Lista de Cotejo de Viabilidad Operativa
    para una secuencia de paradas de un itinerario.

    C1: Apertura y días laborables de cada atractivo.
    C2: Cierre de atractivos (la visita concluye antes o a la hora de cierre).
    C3: Suficiencia de traslados sin solapamientos (salida_ant + traslado <= llegada_sig).
    C4: Disponibilidad y capacidad de transporte asignado.
    """
    if cat_atractivos is None:
        cat_atractivos = {a.id_atractivo: a for a in Atractivo.query.all()}
    if cat_transportes is None:
        cat_transportes = {t.id_transporte: t for t in Transporte.query.all()}

    c1_ok = True
    c2_ok = True
    c3_ok = True
    c4_ok = True

    c1_motivos = []
    c2_motivos = []
    c3_motivos = []
    c4_motivos = []

    paradas_evaluadas = []

    # Agrupar por día para evaluar C3 entre paradas consecutivas
    paradas_por_dia = defaultdict(list)
    for p in paradas:
        dia_n = p.get('dia') or 1
        paradas_por_dia[dia_n].append(p)

    for dia_n, paradas_dia in paradas_por_dia.items():
        # Ordenar por orden o por hora de llegada
        paradas_dia_ord = sorted(paradas_dia, key=lambda x: (x.get('orden') or x.get('numero') or 0))

        for idx, p in enumerate(paradas_dia_ord):
            atr_id = p.get('id_atractivo') or p.get('id')
            atr = cat_atractivos.get(atr_id)
            atr_nombre = p.get('nombre') or (atr.nombre if atr else f"Atractivo #{atr_id}")

            h_llegada_min = _time_a_minutos(p.get('hora_llegada_estimada') or p.get('hora_llegada'))
            h_salida_min = _time_a_minutos(p.get('hora_salida_estimada') or p.get('hora_salida'))
            tiempo_traslado = p.get('tiempo_traslado_desde_anterior')
            if tiempo_traslado is None:
                tiempo_traslado = 0
            else:
                try:
                    tiempo_traslado = int(tiempo_traslado)
                except (ValueError, TypeError):
                    tiempo_traslado = 0

            # --------------------------------------------------------------
            # EVALUACIÓN C1 & C2: Horarios del Atractivo
            # --------------------------------------------------------------
            p_c1 = True
            p_c2 = True
            p_c1_obs = []
            p_c2_obs = []

            # Verificar día cerrado si hay fecha
            fecha_str = p.get('fecha')
            if fecha_str and atr and atr.dias_cerrado:
                try:
                    if isinstance(fecha_str, str):
                        f_dt = datetime.strptime(fecha_str[:10], '%Y-%m-%d')
                    else:
                        f_dt = fecha_str
                    dia_nombre = DIAS_SEMANA_NORM[f_dt.weekday()]
                    cerrados = parsear_dias_cerrado_set(atr.dias_cerrado)
                    if dia_nombre in cerrados:
                        p_c1 = False
                        msg = f"{atr_nombre} está cerrado los {dia_nombre.capitalize()}s"
                        p_c1_obs.append(msg)
                        c1_motivos.append(msg)
                except Exception:
                    pass

            # Apertura (C1) y Cierre (C2)
            h_apertura_atr = atr.horario_apertura if atr else None
            h_cierre_atr = atr.horario_cierre if atr else None
            h_apertura_min = _time_a_minutos(h_apertura_atr)
            h_cierre_min = _time_a_minutos(h_cierre_atr)

            if h_apertura_min is not None and h_llegada_min is not None:
                if h_llegada_min < h_apertura_min:
                    p_c1 = False
                    ap_str = h_apertura_atr.strftime('%H:%M') if hasattr(h_apertura_atr, 'strftime') else str(h_apertura_atr)[:5]
                    ll_str = f"{h_llegada_min//60:02d}:{h_llegada_min%60:02d}"
                    msg = f"Llegada a {atr_nombre} a las {ll_str} antes de apertura ({ap_str})"
                    p_c1_obs.append(msg)
                    c1_motivos.append(msg)

            if h_cierre_min is not None and h_salida_min is not None:
                if h_salida_min > h_cierre_min:
                    p_c2 = False
                    ci_str = h_cierre_atr.strftime('%H:%M') if hasattr(h_cierre_atr, 'strftime') else str(h_cierre_atr)[:5]
                    sa_str = f"{h_salida_min//60:02d}:{h_salida_min%60:02d}"
                    msg = f"Salida de {atr_nombre} a las {sa_str} posterior al cierre ({ci_str})"
                    p_c2_obs.append(msg)
                    c2_motivos.append(msg)

            if not p_c1:
                c1_ok = False
            if not p_c2:
                c2_ok = False

            # --------------------------------------------------------------
            # EVALUACIÓN C3: Consistencia de traslados sin solapamientos
            # --------------------------------------------------------------
            p_c3 = True
            p_c3_obs = []
            if idx > 0:
                p_ant = paradas_dia_ord[idx - 1]
                h_salida_ant_min = _time_a_minutos(p_ant.get('hora_salida_estimada') or p_ant.get('hora_salida'))
                if h_salida_ant_min is not None and h_llegada_min is not None:
                    tiempo_disponible = h_llegada_min - h_salida_ant_min
                    if tiempo_disponible < 0:
                        p_c3 = False
                        msg = f"Solapamiento horario entre parada {idx} y {idx+1} (llegada antes de salir de la anterior)"
                        p_c3_obs.append(msg)
                        c3_motivos.append(msg)
                    elif tiempo_disponible < tiempo_traslado:
                        p_c3 = False
                        msg = f"Traslado insuficiente hacia {atr_nombre}: se requieren {tiempo_traslado} min pero hay {tiempo_disponible} min"
                        p_c3_obs.append(msg)
                        c3_motivos.append(msg)

            if not p_c3:
                c3_ok = False

            # --------------------------------------------------------------
            # EVALUACIÓN C4: Disponibilidad y capacidad del transporte
            # --------------------------------------------------------------
            p_c4 = True
            p_c4_obs = []
            trans_id = p.get('id_transporte')
            trans = cat_transportes.get(trans_id) if trans_id else None
            trans_nombre = trans.nombre if trans else (p.get('transporte_usado') or 'Transporte no especificado')

            if trans_id and not trans:
                p_c4 = False
                msg = f"Transporte ID {trans_id} no existe en catálogo"
                p_c4_obs.append(msg)
                c4_motivos.append(msg)
            elif trans:
                if trans.deleted_at is not None:
                    p_c4 = False
                    msg = f"Transporte '{trans.nombre}' se encuentra inactivo/eliminado"
                    p_c4_obs.append(msg)
                    c4_motivos.append(msg)

                # Capacidad
                if trans.capacidad and num_personas > (trans.capacidad + 1):
                    p_c4 = False
                    msg = f"Capacidad insuficiente en '{trans.nombre}' ({trans.capacidad} asientos) para {num_personas} personas"
                    p_c4_obs.append(msg)
                    c4_motivos.append(msg)

                # Franja horaria del transporte
                t_ini_min = _time_a_minutos(trans.horario_inicio)
                t_fin_min = _time_a_minutos(trans.horario_fin)
                if t_ini_min is not None and h_llegada_min is not None:
                    # Si el traslado ocurrió antes del horario de servicio
                    hora_traslado_min = max(0, h_llegada_min - tiempo_traslado)
                    if hora_traslado_min < t_ini_min:
                        p_c4 = False
                        msg = f"Traslado en '{trans.nombre}' inicia antes de su horario operativo"
                        p_c4_obs.append(msg)
                        c4_motivos.append(msg)
                if t_fin_min is not None and h_salida_min is not None:
                    if h_salida_min > t_fin_min:
                        p_c4 = False
                        msg = f"Servicio de '{trans.nombre}' concluye antes de finalizar la parada ({atr_nombre})"
                        p_c4_obs.append(msg)
                        c4_motivos.append(msg)

            if not p_c4:
                c4_ok = False

            # Desglose de parada para modal detallado
            paradas_evaluadas.append({
                "numero": p.get('numero') or (idx + 1),
                "dia": dia_n,
                "atractivo": atr_nombre,
                "hora_llegada": f"{h_llegada_min//60:02d}:{h_llegada_min%60:02d}" if h_llegada_min is not None else "--:--",
                "hora_salida": f"{h_salida_min//60:02d}:{h_salida_min%60:02d}" if h_salida_min is not None else "--:--",
                "horario_atractivo": f"{atr.horario_apertura.strftime('%H:%M') if atr and atr.horario_apertura else '00:00'} - {atr.horario_cierre.strftime('%H:%M') if atr and atr.horario_cierre else '23:59'}" if atr else "Sin restricción",
                "tiempo_traslado_min": tiempo_traslado,
                "transporte": trans_nombre,
                "c1": p_c1,
                "c2": p_c2,
                "c3": p_c3,
                "c4": p_c4,
                "observaciones": p_c1_obs + p_c2_obs + p_c3_obs + p_c4_obs,
            })

    es_viable_global = c1_ok and c2_ok and c3_ok and c4_ok
    todos_motivos = c1_motivos + c2_motivos + c3_motivos + c4_motivos

    return {
        "c1": c1_ok,
        "c2": c2_ok,
        "c3": c3_ok,
        "c4": c4_ok,
        "es_viable": es_viable_global,
        "estado": "Viable" if es_viable_global else "Con conflicto",
        "motivos_c1": c1_motivos,
        "motivos_c2": c2_motivos,
        "motivos_c3": c3_motivos,
        "motivos_c4": c4_motivos,
        "observaciones": "; ".join(todos_motivos) if todos_motivos else "Cumple todas las restricciones operativas",
        "total_conflictos": len(todos_motivos),
        "paradas_evaluadas": paradas_evaluadas,
    }


def obtener_auditoria_lista_cotejo(
    fuente: str = 'auto',
    fecha_filtro: str | None = None,
    id_consulta: int | None = None
) -> dict:
    """
    Realiza la auditoría integral de la Lista de Cotejo de Viabilidad Operativa
    sincronizada con las consultas del motor NSGA-II.
    
    fuente:
      - 'consultas' / 'auto': Evalúa directamente las soluciones en consulta_nsga2.resultados_json
                              filtradas por fecha de ejecución y/o id_consulta (sin duplicación).
      - 'itinerarios': Evalúa la tabla itinerario (guardados en BD).
    fecha_filtro:
      - 'YYYY-MM-DD': Fecha de ejecución del algoritmo (por defecto hoy o la más reciente).
      - 'todas': Sin filtro de fecha.
    id_consulta:
      - int: ID específico de consulta_nsga2 a auditar.
    """
    cat_atractivos = {a.id_atractivo: a for a in Atractivo.query.all()}
    cat_transportes = {t.id_transporte: t for t in Transporte.query.all()}

    # 1. Obtener todas las fechas de ejecución disponibles en consulta_nsga2
    fechas_disponibles = []
    try:
        fechas_raw = ConsultaNSGA2.query.with_entities(ConsultaNSGA2.fecha).distinct().all()
        fechas_unicas = set()
        for f in fechas_raw:
            val = f[0]
            if val:
                if hasattr(val, 'strftime'):
                    fechas_unicas.add(val.strftime('%Y-%m-%d'))
                else:
                    fechas_unicas.add(str(val)[:10])
        fechas_disponibles = sorted(list(fechas_unicas), reverse=True)
    except Exception:
        fechas_disponibles = []

    if not fecha_filtro or fecha_filtro == 'todas':
        fecha_filtro = 'todas'

    # 2. Filtrar consultas según la fecha para el selector de consultas
    q_selector = ConsultaNSGA2.query
    if fecha_filtro != 'todas':
        try:
            f_date = datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
            dt_inicio = datetime.combine(f_date, datetime.min.time())
            dt_fin = datetime.combine(f_date, datetime.max.time())
            q_selector = q_selector.filter(ConsultaNSGA2.fecha >= dt_inicio, ConsultaNSGA2.fecha <= dt_fin)
        except Exception:
            pass
    consultas_del_filtro = q_selector.order_by(ConsultaNSGA2.id_consulta.desc()).all()

    consultas_selector = []
    for c in consultas_del_filtro:
        n_sols = c.num_soluciones or 0
        if c.resultados_json:
            try:
                rd = json.loads(c.resultados_json)
                s_list = rd.get('soluciones') or rd.get('soluciones_viables') or []
                if len(s_list) > 0:
                    n_sols = len(s_list)
            except Exception:
                pass
        hora_txt = c.fecha.strftime('%H:%M') if c.fecha else '--:--'
        fecha_txt = c.fecha.strftime('%Y-%m-%d') if c.fecha else ''
        consultas_selector.append({
            'id_consulta': c.id_consulta,
            'hora': hora_txt,
            'fecha': fecha_txt,
            'num_soluciones': n_sols,
            'label': f"Consulta #{c.id_consulta} - {hora_txt} ({n_sols} opciones)"
        })

    # 3. Determinar el conjunto exacto de consultas a evaluar
    consultas_a_evaluar = []
    if id_consulta:
        consultas_a_evaluar = [c for c in consultas_del_filtro if c.id_consulta == id_consulta]
        if not consultas_a_evaluar:
            c_direct = ConsultaNSGA2.query.get(id_consulta)
            if c_direct:
                consultas_a_evaluar = [c_direct]
    else:
        consultas_a_evaluar = consultas_del_filtro

    lista_evaluados = []

    # 4. Evaluación de soluciones
    if fuente in ['consultas', 'auto']:
        for c in consultas_a_evaluar:
            if not c.resultados_json:
                continue
            try:
                res_dict = json.loads(c.resultados_json)
                # IMPORTANTE: Priorizar soluciones sin concatenar con soluciones_viables para evitar duplicados
                sols = res_dict.get('soluciones') or res_dict.get('soluciones_viables') or []

                for idx, sol in enumerate(sols):
                    paradas_sol = sol.get('paradas', [])
                    num_personas = 1
                    if c.intereses and isinstance(c.intereses, str) and c.intereses.startswith('{'):
                        try:
                            num_personas = json.loads(c.intereses).get('num_personas', 1)
                        except Exception:
                            num_personas = 1

                    evaluacion = evaluar_lista_cotejo_itinerario(
                        paradas=paradas_sol,
                        num_personas=num_personas,
                        cat_atractivos=cat_atractivos,
                        cat_transportes=cat_transportes
                    )

                    fecha_vis = sol.get('fecha_inicio') or (c.fecha_inicio_viaje.strftime('%Y-%m-%d') if c.fecha_inicio_viaje else "-")
                    fecha_ejec = c.fecha.strftime('%Y-%m-%d %H:%M') if c.fecha else "-"

                    lista_evaluados.append({
                        "id_codigo": f"C{c.id_consulta}-S{idx+1:02d}",
                        "id_consulta": c.id_consulta,
                        "numero_solucion": idx + 1,
                        "origen": f"Consulta #{c.id_consulta} ({c.fecha.strftime('%H:%M') if c.fecha else ''})",
                        "tipo_fuente": "consulta",
                        "fecha": fecha_vis,
                        "fecha_visita": fecha_vis,
                        "fecha_ejecucion": fecha_ejec,
                        "dias": sol.get('dias_totales') or 1,
                        "paradas_count": len(paradas_sol),
                        "num_personas": num_personas,
                        "costo_bob": float(sol.get('costo_total_bob') or 0.0),
                        "c1": evaluacion["c1"],
                        "c2": evaluacion["c2"],
                        "c3": evaluacion["c3"],
                        "c4": evaluacion["c4"],
                        "es_viable": evaluacion["es_viable"],
                        "estado": evaluacion["estado"],
                        "estado_texto": evaluacion["estado"],
                        "observaciones": evaluacion["observaciones"],
                        "total_conflictos": evaluacion["total_conflictos"],
                        "paradas_detalle": evaluacion["paradas_evaluadas"],
                        "paradas_desglose": evaluacion["paradas_evaluadas"],
                    })
            except Exception:
                continue

    elif fuente == 'itinerarios':
        q_it = Itinerario.query.filter(Itinerario.deleted_at.is_(None))
        if fecha_filtro and fecha_filtro != 'todas':
            try:
                f_date = datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
                q_it = q_it.join(Generacion).filter(cast(Generacion.fecha_generacion, Date) == f_date)
            except Exception:
                pass
        itinerarios_db = q_it.order_by(Itinerario.id_itinerario.desc()).all()
        for it in itinerarios_db:
            paradas_raw = []
            for d in it.detalles:
                paradas_raw.append({
                    "numero": d.orden,
                    "dia": d.dia,
                    "id_atractivo": d.id_atractivo,
                    "hora_llegada_estimada": d.hora_llegada_estimada,
                    "hora_salida_estimada": d.hora_salida_estimada,
                    "tiempo_traslado_desde_anterior": d.tiempo_traslado_desde_anterior,
                    "id_transporte": d.id_transporte,
                    "fecha": it.fecha_inicio.strftime('%Y-%m-%d') if it.fecha_inicio else None,
                })

            evaluacion = evaluar_lista_cotejo_itinerario(
                paradas=paradas_raw,
                num_personas=it.num_personas or 1,
                cat_atractivos=cat_atractivos,
                cat_transportes=cat_transportes
            )

            f_ejec = it.generacion.fecha_generacion.strftime('%Y-%m-%d %H:%M') if (it.generacion and it.generacion.fecha_generacion) else "-"
            f_vis = it.fecha_inicio.strftime('%Y-%m-%d') if it.fecha_inicio else "-"

            lista_evaluados.append({
                "id_codigo": f"ITIN-{it.id_itinerario:04d}",
                "id_consulta": it.id_generacion,
                "numero_solucion": it.numero_solucion,
                "origen": f"Itinerario #{it.id_itinerario}",
                "tipo_fuente": "itinerario",
                "fecha": f_vis,
                "fecha_visita": f_vis,
                "fecha_ejecucion": f_ejec,
                "dias": it.dias_totales or 1,
                "paradas_count": len(it.detalles),
                "num_personas": it.num_personas or 1,
                "costo_bob": float(it.costo_total_bob or 0.0),
                "c1": evaluacion["c1"],
                "c2": evaluacion["c2"],
                "c3": evaluacion["c3"],
                "c4": evaluacion["c4"],
                "es_viable": evaluacion["es_viable"],
                "estado": evaluacion["estado"],
                "estado_texto": evaluacion["estado"],
                "observaciones": evaluacion["observaciones"],
                "total_conflictos": evaluacion["total_conflictos"],
                "paradas_detalle": evaluacion["paradas_evaluadas"],
                "paradas_desglose": evaluacion["paradas_evaluadas"],
            })

    # 5. Consolidación cuantitativa de cumplimiento
    total_eval = len(lista_evaluados)
    viables_tot = sum(1 for it in lista_evaluados if it["es_viable"])
    conflictos_tot = total_eval - viables_tot

    c1_si = sum(1 for it in lista_evaluados if it["c1"])
    c2_si = sum(1 for it in lista_evaluados if it["c2"])
    c3_si = sum(1 for it in lista_evaluados if it["c3"])
    c4_si = sum(1 for it in lista_evaluados if it["c4"])

    pct_viabilidad = round((viables_tot / total_eval * 100), 2) if total_eval > 0 else 0.0

    tabla_criterios = [
        {
            "codigo": "C1",
            "criterio": "Apertura y Días Hábiles de Atractivos",
            "descripcion": "Hora de llegada posterior o igual a la apertura y día hábil de visita sin cierres programados.",
            "si_count": c1_si,
            "si_pct": round((c1_si / total_eval * 100), 1) if total_eval > 0 else 0.0,
            "no_count": total_eval - c1_si,
            "no_pct": round(((total_eval - c1_si) / total_eval * 100), 1) if total_eval > 0 else 0.0,
        },
        {
            "codigo": "C2",
            "criterio": "Cierre de Atractivos",
            "descripcion": "Hora de salida de cada atractivo anterior o igual al límite de cierre operativo.",
            "si_count": c2_si,
            "si_pct": round((c2_si / total_eval * 100), 1) if total_eval > 0 else 0.0,
            "no_count": total_eval - c2_si,
            "no_pct": round(((total_eval - c2_si) / total_eval * 100), 1) if total_eval > 0 else 0.0,
        },
        {
            "codigo": "C3",
            "criterio": "Suficiencia de Tiempo de Traslado",
            "descripcion": "Tiempos de traslado suficientes entre paradas consecutivas sin solapamientos horarios.",
            "si_count": c3_si,
            "si_pct": round((c3_si / total_eval * 100), 1) if total_eval > 0 else 0.0,
            "no_count": total_eval - c3_si,
            "no_pct": round(((total_eval - c3_si) / total_eval * 100), 1) if total_eval > 0 else 0.0,
        },
        {
            "codigo": "C4",
            "criterio": "Disponibilidad y Capacidad de Transporte",
            "descripcion": "Vehículo activo, dentro de su franja horaria de servicio y con capacidad para los pasajeros.",
            "si_count": c4_si,
            "si_pct": round((c4_si / total_eval * 100), 1) if total_eval > 0 else 0.0,
            "no_count": total_eval - c4_si,
            "no_pct": round(((total_eval - c4_si) / total_eval * 100), 1) if total_eval > 0 else 0.0,
        },
    ]

    # 6. Métricas dinámicas calculadas sobre las consultas filtradas
    if consultas_a_evaluar:
        tiempos = [float(c.tiempo_ejecucion_seg) for c in consultas_a_evaluar if c.tiempo_ejecucion_seg is not None]
        hvs = [float(c.hipervolumen) for c in consultas_a_evaluar if c.hipervolumen is not None]
        gds = [float(c.generational_distance) for c in consultas_a_evaluar if c.generational_distance is not None]
        spreads = [float(c.spread_spacing) for c in consultas_a_evaluar if c.spread_spacing is not None]
        nums_sol = [int(c.num_soluciones) for c in consultas_a_evaluar if c.num_soluciones is not None]

        prom_tiempo_seg = sum(tiempos) / len(tiempos) if tiempos else 0.0
        prom_hv = sum(hvs) / len(hvs) if hvs else 0.0
        prom_gd = sum(gds) / len(gds) if gds else 0.0
        prom_spread = sum(spreads) / len(spreads) if spreads else 0.0
        prom_soluciones = sum(nums_sol) / len(nums_sol) if nums_sol else 0.0
    else:
        prom_tiempo_seg = 0.0
        prom_hv = 0.0
        prom_gd = 0.0
        prom_spread = 0.0
        prom_soluciones = 0.0

    fuente_desc = "Soluciones NSGA-II (Consultas filtradas)" if fuente in ['consultas', 'auto'] else "Itinerarios Guardados"
    if id_consulta:
        fuente_desc += f" · Consulta #{id_consulta}"
    elif fecha_filtro and fecha_filtro != 'todas':
        fuente_desc += f" · {fecha_filtro}"

    return {
        "resumen": {
            "total_evaluados": total_eval,
            "viables": viables_tot,
            "con_conflictos": conflictos_tot,
            "porcentaje_viabilidad": pct_viabilidad,
            "tiempo_promedio_nsga2": round(float(prom_tiempo_seg), 2),
            "hipervolumen_promedio": round(float(prom_hv), 4),
            "gd_promedio": round(float(prom_gd), 4),
            "spread_promedio": round(float(prom_spread), 4),
            "soluciones_promedio": round(float(prom_soluciones), 1),
            "fuente_utilizada": fuente_desc,
            "fecha_filtro": fecha_filtro,
            "id_consulta": id_consulta,
        },
        "tabla_criterios": tabla_criterios,
        "itinerarios": lista_evaluados,
        "fechas_disponibles": fechas_disponibles,
        "consultas_selector": consultas_selector,
    }
