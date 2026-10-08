from typing import Any
from app.models.atractivo import Atractivo
from app.models.subcategoria import Subcategoria
from app.models.transporte import Transporte
from app.models.categoria import Categoria
from app.services.nsga2_service import ejecutar_nsga2


def preparar_datos_nsga2(
    atractivos_ids: list[int],
    transporte_ids: list[int],
    categorias_activas_ids: list[int] | None = None,
    subcategorias_activas_ids: list[int] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Carga atractivos y transportes activos desde la base de datos según los IDs seleccionados.
    Respetando estrictamente las categorías y subcategorías activas/desactivadas:
    - Subcategoría desactivada -> sus atractivos se excluyen.
    - Categoría desactivada -> todas sus subcategorías y atractivos se excluyen.
    - Atractivo deseleccionado individualmente -> no se considera.
    - Si no hay atractivos seleccionados -> solo se consideran los de categorías y subcategorías activas.
    """
    # 1. Atractivos
    query = Atractivo.query.filter(Atractivo.deleted_at.is_(None))

    if atractivos_ids and len(atractivos_ids) > 0:
        query = query.filter(Atractivo.id_atractivo.in_(atractivos_ids))
        if subcategorias_activas_ids is not None:
            query = query.filter(Atractivo.id_subcategoria.in_(subcategorias_activas_ids))
        if categorias_activas_ids is not None:
            query = query.filter(Atractivo.subcategoria.has(Subcategoria.id_categoria.in_(categorias_activas_ids)))
    else:
        # Modo catálogo completo filtrado por categorías y subcategorías activas
        if categorias_activas_ids is not None:
            query = query.filter(Atractivo.subcategoria.has(Subcategoria.id_categoria.in_(categorias_activas_ids)))
        if subcategorias_activas_ids is not None:
            query = query.filter(Atractivo.id_subcategoria.in_(subcategorias_activas_ids))

    query_atractivos = query.all()

    atractivos_dict = []
    for a in query_atractivos:
        nombre_cat = a.categoria.nombre if a.categoria and not a.categoria.is_deleted else "General"
        nombre_subcat = a.subcategoria.nombre if a.subcategoria and not a.subcategoria.is_deleted else "General"
        atractivos_dict.append({
            "id": a.id_atractivo,
            "nombre": a.nombre,
            "lat": float(a.latitud) if a.latitud is not None else 0.0,
            "lon": float(a.longitud) if a.longitud is not None else 0.0,
            "tiempo_visita": int(a.tiempo_visita_estimado or 60),
            "categoria": nombre_cat,
            "subcategoria": nombre_subcat,
            "id_categoria": a.id_categoria,
            "id_subcategoria": a.id_subcategoria,
            "costo_entrada": float(a.costo_entrada or 0.0),
            "direccion": a.direccion or "",
            "imagen_url": a.imagen_url or "",
        })

    # 2. Transportes
    if transporte_ids and len(transporte_ids) > 0:
        query_transportes = Transporte.query.filter(
            Transporte.id_transporte.in_(transporte_ids),
            Transporte.deleted_at.is_(None)
        ).all()
    else:
        # Si no selecciona nada, usar todos los transportes disponibles
        query_transportes = Transporte.query.filter(
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
            "costo": float(t.costo or 0.0),
            "costo_por_tramo": float(t.costo or 0.0),
            "capacidad": t.capacidad,
        })

    return atractivos_dict, transportes_dict


def generar_itinerarios(
    atractivos_ids: list[int],
    transporte_ids: list[int],
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
    categorias_activas_ids: list[int] | None = None,
    subcategorias_activas_ids: list[int] | None = None,
    **kwargs: Any
) -> dict[str, Any]:
    """
    Orquesta el flujo de generación de itinerarios turísticos multiobjetivo con NSGA-II:
    1. Filtra estrictamente por categorías y subcategorías activas.
    2. Ejecuta el motor genético NSGA-II con calibración K_ideal y formato enriquecido.
    """
    # 1. Preparar datos desde la base de datos
    atractivos_data, transportes_data = preparar_datos_nsga2(
        atractivos_ids=atractivos_ids,
        transporte_ids=transporte_ids,
        categorias_activas_ids=categorias_activas_ids,
        subcategorias_activas_ids=subcategorias_activas_ids,
    )

    if len(atractivos_data) < 2:
        raise ValueError("Se requieren al menos 2 atractivos turísticos activos para construir un itinerario.")

    if len(transportes_data) < 1:
        raise ValueError("No se encontraron medios de transporte disponibles para planificar el viaje.")

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
        num_personas=int(num_personas),
        forzar_atractivos=bool(forzar_atractivos),
        forzar_transporte=bool(forzar_transporte),
        min_paradas=int(min_paradas),
        max_paradas=int(max_paradas),
        auto_rango_paradas=bool(auto_rango_paradas),
    )

    return resultado
