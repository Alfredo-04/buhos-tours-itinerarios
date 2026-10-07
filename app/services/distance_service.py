import time
import logging
from datetime import datetime
from typing import Any
import requests
from app import db
from app.models.distancia_atractivo import DistanciaAtractivo
from app.models.atractivo import Atractivo

logger = logging.getLogger(__name__)

OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"


def consultar_osrm(lat1: float, lon1: float, lat2: float, lon2: float, timeout_seg: float = 5.0) -> dict[str, float] | None:
    """
    Consulta OSRM público con timeout de 5s.
    Retorna {'distancia_km': float, 'duracion_min': float} o None si falla/da timeout.
    """
    if abs(lat1 - lat2) < 1e-6 and abs(lon1 - lon2) < 1e-6:
        return {'distancia_km': 0.0, 'duracion_min': 0.0}

    url = f"{OSRM_BASE_URL}/{lon1},{lat1};{lon2},{lat2}?overview=false"
    try:
        response = requests.get(url, timeout=timeout_seg)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "Ok" and data.get("routes"):
                primera_ruta = data["routes"][0]
                distancia_m = float(primera_ruta.get("distance", 0.0))
                duracion_s = float(primera_ruta.get("duration", 0.0))
                return {
                    "distancia_km": round(distancia_m / 1000.0, 3),
                    "duracion_min": round(duracion_s / 60.0, 2)
                }
    except Exception as e:
        logger.debug(f"Fallo consultando OSRM ({lat1},{lon1} -> {lat2},{lon2}): {e}")

    return None


def obtener_distancia(origen_id: int, destino_id: int, lat1: float | None = None, lon1: float | None = None, lat2: float | None = None, lon2: float | None = None) -> dict[str, Any]:
    """
    Obtiene la distancia entre dos atractivos:
    1. Busca en DISTANCIA_ATRACTIVO (origen -> destino).
    2. Si NO existe:
       a. Intenta OSRM (con timeout de 5s).
       b. Si OSRM responde: guarda en DISTANCIA_ATRACTIVO con fuente='osrm'.
       c. Si OSRM falla: verifica la distancia invertida (destino -> origen) en BD.
          - Si existe en BD invertida, la usa y la guarda también en la dirección solicitada.
          - Si no existe tampoco, lanza error claro indicando que se debe precalcular la matriz.
    3. Retorna dict: { 'distancia_km': float, 'duracion_min': float, 'fuente': str }
    """
    if origen_id == destino_id:
        return {"distancia_km": 0.0, "duracion_min": 0.0, "fuente": "mismo_punto"}

    # 1. Buscar en BD
    reg = DistanciaAtractivo.query.filter_by(
        id_atractivo_origen=origen_id,
        id_atractivo_destino=destino_id
    ).first()

    if reg:
        return {
            "distancia_km": float(reg.distancia_km),
            "duracion_min": float(reg.duracion_min),
            "fuente": reg.fuente
        }

    # Si no se proveyeron coordenadas, consultarlas
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        atractivo_orig = Atractivo.query.get(origen_id)
        atractivo_dest = Atractivo.query.get(destino_id)
        if not atractivo_orig or not atractivo_dest:
            raise ValueError(f"Atractivos inválidos para distancia: {origen_id} o {destino_id} no existen.")
        lat1 = float(atractivo_orig.latitud)
        lon1 = float(atractivo_orig.longitud)
        lat2 = float(atractivo_dest.latitud)
        lon2 = float(atractivo_dest.longitud)

    # 2a. Intentar OSRM
    res_osrm = consultar_osrm(lat1, lon1, lat2, lon2, timeout_seg=5.0)
    if res_osrm:
        try:
            nuevo = DistanciaAtractivo(
                id_atractivo_origen=origen_id,
                id_atractivo_destino=destino_id,
                distancia_km=res_osrm["distancia_km"],
                duracion_min=res_osrm["duracion_min"],
                fuente="osrm",
                fecha_calculo=datetime.utcnow()
            )
            db.session.add(nuevo)
            db.session.commit()
            return {
                "distancia_km": res_osrm["distancia_km"],
                "duracion_min": res_osrm["duracion_min"],
                "fuente": "osrm"
            }
        except Exception as e:
            db.session.rollback()
            logger.warning(f"No se pudo guardar distancia en BD: {e}")
            return {
                "distancia_km": res_osrm["distancia_km"],
                "duracion_min": res_osrm["duracion_min"],
                "fuente": "osrm_memoria"
            }

    # 2c. Si OSRM falla: verificar la distancia invertida (destino -> origen)
    reg_invertido = DistanciaAtractivo.query.filter_by(
        id_atractivo_origen=destino_id,
        id_atractivo_destino=origen_id
    ).first()

    if reg_invertido:
        # Guardar en BD también la dirección origen -> destino para optimizar futuras llamadas
        try:
            nuevo = DistanciaAtractivo(
                id_atractivo_origen=origen_id,
                id_atractivo_destino=destino_id,
                distancia_km=reg_invertido.distancia_km,
                duracion_min=reg_invertido.duracion_min,
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
            "fuente": "simetrico_bd"
        }

    # Si tampoco existe en BD invertida, lanzar error claro (NUNCA usar Haversine)
    raise RuntimeError(
        f"No se pudo calcular la ruta real por calles entre el atractivo #{origen_id} y #{destino_id}. "
        f"OSRM no respondió y no existe registro previo en la matriz pre-calculada de la base de datos. "
        f"Por favor ejecuta el comando: 'flask precalcular-distancias'."
    )


def precalcular_matriz_completa(delay_seg: float = 0.5) -> dict[str, int]:
    """
    Para todos los pares de atractivos activos que no estén ya en la tabla DISTANCIA_ATRACTIVO,
    consulta OSRM (con delay entre consultas para no saturar) y guarda los resultados en la BD.
    Retorna un diccionario con estadísticas: {'calculados': int, 'omitidos': int, 'errores': int}
    """
    atractivos = Atractivo.query.filter(
        Atractivo.deleted_at.is_(None),
        Atractivo.latitud.isnot(None),
        Atractivo.longitud.isnot(None)
    ).order_by(Atractivo.id_atractivo.asc()).all()

    total_atractivos = len(atractivos)
    logger.info(f"Iniciando precalculo de matriz para {total_atractivos} atractivos activos.")

    stats = {'calculados': 0, 'omitidos': 0, 'errores': 0}

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

            # Verificar si ya existe
            existe = DistanciaAtractivo.query.filter_by(
                id_atractivo_origen=a1.id_atractivo,
                id_atractivo_destino=a2.id_atractivo
            ).first()

            if existe:
                stats['omitidos'] += 1
                continue

            # Consultar OSRM
            res = consultar_osrm(lat1, lon1, lat2, lon2, timeout_seg=6.0)

            if not res:
                # Si falló, intentar ver si existe el invertido para usarlo
                reg_inv = DistanciaAtractivo.query.filter_by(
                    id_atractivo_origen=a2.id_atractivo,
                    id_atractivo_destino=a1.id_atractivo
                ).first()
                if reg_inv:
                    res = {
                        "distancia_km": float(reg_inv.distancia_km),
                        "duracion_min": float(reg_inv.duracion_min)
                    }

            if res:
                try:
                    nuevo = DistanciaAtractivo(
                        id_atractivo_origen=a1.id_atractivo,
                        id_atractivo_destino=a2.id_atractivo,
                        distancia_km=res["distancia_km"],
                        duracion_min=res["duracion_min"],
                        fuente="osrm",
                        fecha_calculo=datetime.utcnow()
                    )
                    db.session.add(nuevo)
                    db.session.commit()
                    stats['calculados'] += 1
                    logger.info(f"[OK] Distancia #{a1.id_atractivo} -> #{a2.id_atractivo}: {res['distancia_km']} km, {res['duracion_min']} min")
                except Exception as e:
                    db.session.rollback()
                    logger.warning(f"Error guardando distancia #{a1.id_atractivo}->#{a2.id_atractivo}: {e}")
                    stats['errores'] += 1
            else:
                stats['errores'] += 1
                logger.warning(f"[FAIL] OSRM no respondió para #{a1.id_atractivo} ({a1.nombre}) -> #{a2.id_atractivo} ({a2.nombre})")

            # Delay respetuoso
            time.sleep(delay_seg)

    return stats
