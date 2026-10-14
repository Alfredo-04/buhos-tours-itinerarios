import time
import json
import logging
from datetime import datetime
from typing import Any
import requests
from sqlalchemy import text
from app import db
from app.models.distancia_atractivo import DistanciaAtractivo
from app.models.atractivo import Atractivo

logger = logging.getLogger(__name__)

OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"


def consultar_osrm(lat1: float, lon1: float, lat2: float, lon2: float, timeout_seg: float = 5.0) -> dict[str, Any] | None:
    """
    Consulta OSRM público con timeout especificado.
    Retorna {'distancia_km': float, 'duracion_min': float, 'polyline_coords': [[lat, lon], ...]} o None si falla/da timeout.
    """
    if abs(lat1 - lat2) < 1e-6 and abs(lon1 - lon2) < 1e-6:
        return {'distancia_km': 0.0, 'duracion_min': 0.0, 'polyline_coords': []}

    url = f"{OSRM_BASE_URL}/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    try:
        response = requests.get(url, timeout=timeout_seg)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "Ok" and data.get("routes"):
                primera_ruta = data["routes"][0]
                distancia_m = float(primera_ruta.get("distance", 0.0))
                duracion_s = float(primera_ruta.get("duration", 0.0))
                
                geometry = primera_ruta.get("geometry", {})
                coords_raw = geometry.get("coordinates", []) if isinstance(geometry, dict) else []
                # OSRM entrega [lon, lat], Leaflet espera [lat, lon]
                polyline_coords = [[float(c[1]), float(c[0])] for c in coords_raw if len(c) >= 2]
                
                return {
                    "distancia_km": round(distancia_m / 1000.0, 3),
                    "duracion_min": round(duracion_s / 60.0, 2),
                    "polyline_coords": polyline_coords
                }
    except Exception as e:
        logger.debug(f"Fallo consultando OSRM ({lat1},{lon1} -> {lat2},{lon2}): {e}")

    return None


def obtener_distancia(origen_id: int, destino_id: int, lat1: float | None = None, lon1: float | None = None, lat2: float | None = None, lon2: float | None = None) -> dict[str, Any]:
    """
    Obtiene la distancia entre dos atractivos:
    1. Busca en DISTANCIA_ATRACTIVO (origen -> destino).
    2. Si existe: decodifica polyline_coords (JSON array [[lat, lon], ...]) y retorna.
    3. Si NO existe en dirección directa:
       - Busca en dirección simétrica (destino -> origen).
       - Si existe en invertido:
         - invierte el polyline (coords[::-1])
         - guarda en BD la dirección origen -> destino con su polyline
         - retorna el resultado
    4. Si NO existe en BD:
       - CERO llamadas a OSRM durante la generación.
       - Lanza un RuntimeError claro indicando que se debe ejecutar 'flask precalcular-distancias'.
    """
    if origen_id == destino_id:
        return {"distancia_km": 0.0, "duracion_min": 0.0, "polyline_coords": [], "fuente": "mismo_punto"}

    # 1. Buscar en BD directo
    reg = DistanciaAtractivo.query.filter_by(
        id_atractivo_origen=origen_id,
        id_atractivo_destino=destino_id
    ).first()

    if reg:
        polyline = []
        if reg.polyline_coords:
            try:
                polyline = json.loads(reg.polyline_coords)
            except Exception:
                polyline = []

        return {
            "distancia_km": float(reg.distancia_km),
            "duracion_min": float(reg.duracion_min),
            "polyline_coords": polyline,
            "fuente": reg.fuente
        }

    # 2. Si no existe directo, buscar el simétrico en BD (destino -> origen)
    reg_invertido = DistanciaAtractivo.query.filter_by(
        id_atractivo_origen=destino_id,
        id_atractivo_destino=origen_id
    ).first()

    if reg_invertido:
        polyline_orig = []
        if reg_invertido.polyline_coords:
            try:
                polyline_orig = json.loads(reg_invertido.polyline_coords)
            except Exception:
                polyline_orig = []

        polyline_invertida = [coord for coord in reversed(polyline_orig)] if polyline_orig else []

        try:
            nuevo = DistanciaAtractivo(
                id_atractivo_origen=origen_id,
                id_atractivo_destino=destino_id,
                distancia_km=reg_invertido.distancia_km,
                duracion_min=reg_invertido.duracion_min,
                polyline_coords=json.dumps(polyline_invertida) if polyline_invertida else None,
                fuente="simetrico_bd",
                fecha_calculo=datetime.utcnow()
            )
            db.session.add(nuevo)
            db.session.commit()
        except Exception:
            db.session.rollback()

        return {
            "distancia_km": float(reg_invertido.distancia_km),
            "duracion_min": float(reg_invertido.duracion_min),
            "polyline_coords": polyline_invertida,
            "fuente": "simetrico_bd"
        }

    # 3. Si no existe en BD, LANZAR ERROR CLARO (CERO consultas a OSRM durante generación)
    raise RuntimeError(
        f"No se encontró la distancia entre el atractivo #{origen_id} y #{destino_id} en la base de datos. "
        f"Durante la generación de itinerarios las consultas externas a OSRM están desactivadas para optimizar el rendimiento. "
        f"Por favor ejecuta el comando: 'flask precalcular-distancias'."
    )


def precalcular_matriz_completa(delay_seg: float = 0.5) -> dict[str, int]:
    """
    1. Asegura que la columna polyline_coords exista en BD.
    2. Actualiza todos los registros existentes donde polyline_coords IS NULL consultando OSRM.
    3. Calcula los pares de atractivos activos faltantes en DISTANCIA_ATRACTIVO.
    4. Respeta el delay entre consultas a OSRM (por defecto 0.5s).
    """
    try:
        db.session.execute(text("ALTER TABLE distancia_atractivo ADD COLUMN IF NOT EXISTS polyline_coords TEXT;"))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.warning(f"Aviso verificando columna polyline_coords: {e}")

    stats = {'calculados': 0, 'actualizados': 0, 'omitidos': 0, 'errores': 0}

    # 1. Buscar todos los pares existentes donde polyline_coords IS NULL
    pendientes = DistanciaAtractivo.query.filter(
        (DistanciaAtractivo.polyline_coords.is_(None)) | (DistanciaAtractivo.polyline_coords == '')
    ).all()

    if pendientes:
        logger.info(f"Encontrados {len(pendientes)} registros con polyline_coords pendiente. Actualizando con OSRM...")
        for reg in pendientes:
            a1 = Atractivo.query.get(reg.id_atractivo_origen)
            a2 = Atractivo.query.get(reg.id_atractivo_destino)
            if not a1 or not a2 or not a1.latitud or not a2.latitud:
                stats['errores'] += 1
                continue

            lat1 = float(a1.latitud)
            lon1 = float(a1.longitud)
            lat2 = float(a2.latitud)
            lon2 = float(a2.longitud)

            res = consultar_osrm(lat1, lon1, lat2, lon2, timeout_seg=6.0)
            if res and res.get("polyline_coords"):
                try:
                    reg.polyline_coords = json.dumps(res["polyline_coords"])
                    reg.distancia_km = res["distancia_km"]
                    reg.duracion_min = res["duracion_min"]
                    reg.fuente = "osrm"
                    db.session.commit()
                    stats['actualizados'] += 1
                    logger.info(f"[ACTUALIZADO] #{a1.id_atractivo} -> #{a2.id_atractivo} ({len(res['polyline_coords'])} puntos)")
                except Exception as e:
                    db.session.rollback()
                    logger.warning(f"Error actualizando polyline #{reg.id_distancia}: {e}")
                    stats['errores'] += 1
            else:
                # Intentar si el registro invertido ya tiene polyline
                reg_rev = DistanciaAtractivo.query.filter_by(
                    id_atractivo_origen=reg.id_atractivo_destino,
                    id_atractivo_destino=reg.id_atractivo_origen
                ).first()
                if reg_rev and reg_rev.polyline_coords:
                    try:
                        p_orig = json.loads(reg_rev.polyline_coords)
                        p_inv = [c for c in reversed(p_orig)]
                        reg.polyline_coords = json.dumps(p_inv)
                        db.session.commit()
                        stats['actualizados'] += 1
                    except Exception:
                        db.session.rollback()
                        stats['errores'] += 1
                else:
                    stats['errores'] += 1

            time.sleep(delay_seg)

    # 2. Verificar pares faltantes entre todos los atractivos activos
    atractivos = Atractivo.query.filter(
        Atractivo.deleted_at.is_(None),
        Atractivo.latitud.isnot(None),
        Atractivo.longitud.isnot(None)
    ).order_by(Atractivo.id_atractivo.asc()).all()

    total_atractivos = len(atractivos)
    logger.info(f"Verificando matriz completa para {total_atractivos} atractivos activos.")

    for i in range(total_atractivos):
        a1 = atractivos[i]
        lat1 = float(a1.latitud)
        lon1 = float(a1.longitud)

        for j in range(total_atractivos):
            if i == j:
                continue

            a2 = atractivos[j]
            lat2 = float(a2.latitud)
            lon2 = float(a2.longitud)

            existe = DistanciaAtractivo.query.filter_by(
                id_atractivo_origen=a1.id_atractivo,
                id_atractivo_destino=a2.id_atractivo
            ).first()

            if existe and existe.polyline_coords:
                stats['omitidos'] += 1
                continue

            if existe:
                # Ya fue procesado en paso 1
                continue

            # Consultar OSRM
            res = consultar_osrm(lat1, lon1, lat2, lon2, timeout_seg=6.0)
            if res:
                try:
                    nuevo = DistanciaAtractivo(
                        id_atractivo_origen=a1.id_atractivo,
                        id_atractivo_destino=a2.id_atractivo,
                        distancia_km=res["distancia_km"],
                        duracion_min=res["duracion_min"],
                        polyline_coords=json.dumps(res["polyline_coords"]) if res.get("polyline_coords") else None,
                        fuente="osrm",
                        fecha_calculo=datetime.utcnow()
                    )
                    db.session.add(nuevo)
                    db.session.commit()
                    stats['calculados'] += 1
                    logger.info(f"[NUEVO] Distancia #{a1.id_atractivo} -> #{a2.id_atractivo}: {res['distancia_km']} km, {res['duracion_min']} min")
                except Exception as e:
                    db.session.rollback()
                    logger.warning(f"Error guardando distancia #{a1.id_atractivo}->#{a2.id_atractivo}: {e}")
                    stats['errores'] += 1
            else:
                stats['errores'] += 1
                logger.warning(f"[FAIL] OSRM no respondió para #{a1.id_atractivo} -> #{a2.id_atractivo}")

            time.sleep(delay_seg)

    return stats
