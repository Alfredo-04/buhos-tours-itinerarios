from typing import Any
from app.models.atractivo import Atractivo
from app.models.transporte import Transporte
from app.models.categoria import Categoria
from app.services.nsga2_service import ejecutar_nsga2


def preparar_datos_nsga2(
    atractivos_ids: list[int],
    transporte_ids: list[int]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Carga atractivos y transportes activos desde la base de datos según los IDs seleccionados.
    Retorna dos listas de diccionarios con el formato exacto requerido por el motor NSGA-II.

    :param atractivos_ids: Lista de IDs de atractivos a incluir
    :param transporte_ids: Lista de IDs de transportes disponibles
    :return: Tupla (lista_atractivos_dict, lista_transportes_dict)
    """
    # Consultar atractivos activos
    query_atractivos = Atractivo.query.filter(
        Atractivo.id_atractivo.in_(atractivos_ids),
        Atractivo.deleted_at.is_(None)
    ).all()

    atractivos_dict = []
    for a in query_atractivos:
        nombre_cat = a.categoria.nombre if a.categoria and not a.categoria.is_deleted else "General"
        atractivos_dict.append({
            "id": a.id_atractivo,
            "nombre": a.nombre,
            "lat": float(a.latitud) if a.latitud is not None else 0.0,
            "lon": float(a.longitud) if a.longitud is not None else 0.0,
            "tiempo_visita": int(a.tiempo_visita_estimado or 60),
            "categoria": nombre_cat,
            "costo_entrada": float(a.costo_entrada or 0.0),
            "direccion": a.direccion or "",
            "imagen_url": a.imagen_url or "",
        })

    # Consultar transportes activos
    query_transportes = Transporte.query.filter(
        Transporte.id_transporte.in_(transporte_ids),
        Transporte.deleted_at.is_(None)
    ).all()

    transportes_dict = []
    for t in query_transportes:
        transportes_dict.append({
            "id": t.id_transporte,
            "nombre": t.nombre,
            "tipo": t.tipo,
            "tipo_costo": t.tipo_costo,
            "velocidad_promedio_kmh": float(t.velocidad_promedio_kmh or 30.0),
            "costo_por_tramo": float(t.costo_por_tramo or 0.0),
            "capacidad": t.capacidad,
        })

    return atractivos_dict, transportes_dict


def generar_itinerarios(
    atractivos_ids: list[int],
    transporte_ids: list[int],
    presupuesto_max: float,
    tiempo_disponible_horas: float,
    intereses: dict[str, float],
    tamano_poblacion: int = 50,
    generaciones: int = 40,
    prob_cruce: float = 0.9,
    prob_mutacion: float = 0.1,
    **kwargs: Any
) -> dict[str, Any]:
    """
    Orquesta el flujo de generación de itinerarios turísticos multiobjetivo:
    1. Prepara y transforma los datos desde la BD.
    2. Ejecuta el motor genético NSGA-II con pymoo.
    3. Retorna la respuesta completa estructurada para el controlador y vistas.

    :param atractivos_ids: Lista de IDs de atractivos seleccionados
    :param transporte_ids: Lista de IDs de transportes seleccionados
    :param presupuesto_max: Presupuesto máximo en BOB
    :param tiempo_disponible_horas: Tiempo total en horas
    :param intereses: Mapa de categorías a pesos de preferencia {categoria: peso (0.0-1.0)}
    :param tamano_poblacion: Tamaño de población del algoritmo (default 50)
    :param generaciones: Número de generaciones evolutivas (default 40)
    :param prob_cruce: Probabilidad de cruce OX (default 0.9)
    :param prob_mutacion: Probabilidad de mutación por inversión (default 0.1)
    :return: Diccionario con soluciones, Pareto, convergencia, diversidad y parámetros
    """
    if not atractivos_ids or len(atractivos_ids) < 2:
        raise ValueError("Debes seleccionar al menos 2 atractivos turísticos para construir un itinerario.")

    if not transporte_ids or len(transporte_ids) < 1:
        raise ValueError("Debes seleccionar al menos un medio de transporte disponible.")

    # 1. Preparar datos desde la base de datos
    atractivos_data, transportes_data = preparar_datos_nsga2(atractivos_ids, transporte_ids)

    if len(atractivos_data) < 2:
        raise ValueError("Los atractivos seleccionados no están disponibles o están eliminados en la base de datos.")

    if len(transportes_data) < 1:
        raise ValueError("Los transportes seleccionados no están disponibles en la base de datos.")

    # 2. Ejecutar el motor puro NSGA-II
    resultado = ejecutar_nsga2(
        atractivos=atractivos_data,
        transportes=transportes_data,
        presupuesto_max=float(presupuesto_max),
        tiempo_disponible_horas=float(tiempo_disponible_horas),
        intereses=intereses,
        tamano_poblacion=int(tamano_poblacion),
        generaciones=int(generaciones),
        prob_cruce=float(prob_cruce),
        prob_mutacion=float(prob_mutacion),
    )

    return resultado
