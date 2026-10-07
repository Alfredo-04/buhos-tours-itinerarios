import logging
from typing import Any
from app.services.distance_service import obtener_distancia, consultar_osrm

logger = logging.getLogger(__name__)

# Caché en memoria para evitar redundancias
_ROUTING_CACHE: dict[tuple[int, int], dict[str, float]] = {}

def obtener_ruta_real(origen_id: int, destino_id: int, lat1: float | None = None, lon1: float | None = None, lat2: float | None = None, lon2: float | None = None) -> dict[str, float]:
    """
    Obtiene la distancia y tiempo de ruta real por calles:
    1. Consulta primero OSRM / Base de datos DISTANCIA_ATRACTIVO a través de distance_service.
    2. Si OSRM falla, recurre a la matriz pre-calculada en DISTANCIA_ATRACTIVO.
    3. Si tampoco existe en BD, lanza un error claro. NUNCA utiliza Haversine.

    Retorna un diccionario:
    {
        "distancia_km": float,
        "duracion_min": float
    }
    """
    if origen_id == destino_id:
        return {"distancia_km": 0.0, "duracion_min": 0.0}

    cache_key = (origen_id, destino_id)
    if cache_key in _ROUTING_CACHE:
        return _ROUTING_CACHE[cache_key]

    # distance_service busca en DISTANCIA_ATRACTIVO o consulta OSRM (5s) y guarda en BD
    # Si todo falla, lanza RuntimeError
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
        "duracion_min": float(res["duracion_min"])
    }
    _ROUTING_CACHE[cache_key] = resultado
    return resultado
