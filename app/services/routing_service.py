import logging
from typing import Any
from app.services.distance_service import obtener_distancia, precalcular_matriz_completa

logger = logging.getLogger(__name__)

# Caché en memoria para evitar consultas redundantes dentro del mismo proceso/request
_ROUTING_CACHE: dict[tuple[int, int], dict[str, Any]] = {}


def obtener_ruta_real(
    origen_id: int,
    destino_id: int,
    lat1: float | None = None,
    lon1: float | None = None,
    lat2: float | None = None,
    lon2: float | None = None
) -> dict[str, Any]:
    """
    Obtiene la distancia, tiempo y polyline de ruta real por calles:
    1. Si origen == destino, retorna distancia 0 y polyline vacío.
    2. Si ya está en _ROUTING_CACHE, retorna el resultado en memoria inmediatamente.
    3. Consulta la base de datos a través de distance_service (cero llamadas a OSRM en generación).
    4. Retorna un diccionario:
    {
        "distancia_km": float,
        "duracion_min": float,
        "polyline_coords": [[lat1, lon1], [lat2, lon2], ...]
    }
    """
    if origen_id == destino_id:
        return {"distancia_km": 0.0, "duracion_min": 0.0, "polyline_coords": []}

    cache_key = (origen_id, destino_id)
    if cache_key in _ROUTING_CACHE:
        return _ROUTING_CACHE[cache_key]

    # distance_service busca en DISTANCIA_ATRACTIVO en BD
    res = obtener_distancia(
        origen_id=origen_id,
        destino_id=destino_id,
        lat1=lat1,
        lon1=lon1,
        lat2=lat2,
        lon2=lon2
    )

    resultado = {
        "distancia_km": float(res["distancia_km"]),
        "duracion_min": float(res["duracion_min"]),
        "polyline_coords": res.get("polyline_coords", []) or []
    }
    _ROUTING_CACHE[cache_key] = resultado
    return resultado
