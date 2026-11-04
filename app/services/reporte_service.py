import json
from collections import defaultdict
from sqlalchemy import func, desc
from app import db
from app.models.itinerario import Itinerario
from app.models.itinerario_detalle import ItinerarioDetalle
from app.models.atractivo import Atractivo
from app.models.generacion import Generacion
from app.models.consulta_nsga2 import ConsultaNSGA2


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
    Retorna los últimos registros de ConsultaNSGA2 con parámetros y métricas académicas
    extraídas de los campos nativos y de resultados_json.
    """
    consultas = ConsultaNSGA2.query.order_by(
        desc(ConsultaNSGA2.fecha)
    ).limit(limit).all()

    filas = []
    for c in consultas:
        hv = None
        gd = None
        spread = None
        ref_n = 0

        if c.resultados_json:
            try:
                res_dict = json.loads(c.resultados_json)
                hv = res_dict.get("hipervolumen")
                gd = res_dict.get("gd")
                spread = res_dict.get("spread")
                ref_n = res_dict.get("num_soluciones_archivo_ref", 0)
            except Exception:
                pass

        filas.append({
            "id_consulta": c.id_consulta,
            "fecha": c.fecha.strftime("%Y-%m-%d %H:%M") if c.fecha else "-",
            "tamano_poblacion": c.tamano_poblacion,
            "generaciones": c.generaciones,
            "tiempo_ejecucion_seg": round(float(c.tiempo_ejecucion_seg), 2) if c.tiempo_ejecucion_seg is not None else "-",
            "num_soluciones": c.num_soluciones,
            "hipervolumen": round(float(hv), 4) if hv is not None else "-",
            "gd": round(float(gd), 4) if gd is not None else "-",
            "spread": round(float(spread), 4) if spread is not None else "-",
            "num_soluciones_archivo_ref": ref_n,
        })

    return filas
