import math
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
import requests

logger = logging.getLogger(__name__)

BOLIVIA_TZ = timezone(timedelta(hours=-4))

dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']

def dias_semana_espanol(fecha: datetime | Any = None) -> str:
    """Retorna el día de la semana en español en minúsculas (lunes, martes, etc.) en hora de Bolivia."""
    f = fecha or datetime.now(BOLIVIA_TZ)
    return dias_semana[f.weekday()]

# 4 zonas climáticas de La Paz (hardcoded, sin CRUD)
PUNTOS_CLIMA = {
    'centro':    (-16.498873591808877, -68.12827038130189),
    'pura_pura': (-16.459940605052843, -68.1490512294104),
    'zona_sur':  (-16.527613724124866, -68.07594869897271),
    'mallasa':   (-16.5736684702765,   -68.0592282220185),
}

# Umbrales de EXCLUSIÓN (solo para sensible_al_clima=true)
UMBRALES_EXCLUSION = {
    'precipitacion_mm_h': 3.0,       # > 3 mm/h → adverso
    'rafagas_kmh': 60.0,             # > 60 km/h → adverso
    'visibilidad_m': 500,            # < 500 m → adverso
}

# Códigos WMO que excluyen (tormenta + lluvia fuerte)
WMO_EXCLUYENTES = {65, 82, 95, 96, 97, 99}

# Caché en memoria
_CACHE_CLIMA: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL_SEGUNDOS = 3600  # 1 hora


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia en km usando Haversine para asignar la zona climática más cercana."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def asignar_zona_clima(lat: float, lon: float) -> str:
    """Retorna la clave de la zona climática más cercana por Haversine."""
    return min(
        PUNTOS_CLIMA.items(),
        key=lambda item: haversine_km(lat, lon, item[1][0], item[1][1])
    )[0]


def clasificar_wmo(wmo_code: int | None) -> dict[str, str]:
    """Retorna {categoria, descripcion, icono} para un código WMO."""
    if wmo_code is None:
        return {'categoria': 'desconocido', 'descripcion': 'Sin datos', 'icono': 'bi-question-circle'}
    
    c = int(wmo_code)
    if c == 0:   return {'categoria': 'despejado', 'descripcion': 'Despejado', 'icono': 'bi-sun-fill'}
    if c == 1:   return {'categoria': 'despejado', 'descripcion': 'Mayormente despejado', 'icono': 'bi-sun-fill'}
    if c == 2:   return {'categoria': 'nublado', 'descripcion': 'Parcialmente nublado', 'icono': 'bi-cloud-sun-fill'}
    if c == 3:   return {'categoria': 'nublado', 'descripcion': 'Nublado', 'icono': 'bi-cloud-fill'}
    if c in {45, 48}: return {'categoria': 'niebla', 'descripcion': 'Neblina / Niebla', 'icono': 'bi-cloud-fog2-fill'}
    if c in {51, 53, 55}: return {'categoria': 'llovizna', 'descripcion': 'Llovizna', 'icono': 'bi-cloud-drizzle-fill'}
    if c in {56, 57}: return {'categoria': 'llovizna', 'descripcion': 'Llovizna helada', 'icono': 'bi-cloud-sleet-fill'}
    if c in {61, 63}: return {'categoria': 'lluvia', 'descripcion': 'Lluvia ligera a moderada', 'icono': 'bi-cloud-rain-fill'}
    if c == 65:  return {'categoria': 'lluvia_fuerte', 'descripcion': 'Lluvia intensa', 'icono': 'bi-cloud-rain-heavy-fill'}
    if c in {66, 67}: return {'categoria': 'lluvia_fuerte', 'descripcion': 'Lluvia helada', 'icono': 'bi-cloud-sleet-fill'}
    if c in {71, 73, 75, 77}: return {'categoria': 'nieve', 'descripcion': 'Nevada', 'icono': 'bi-cloud-snow-fill'}
    if c in {80, 81}: return {'categoria': 'lluvia', 'descripcion': 'Chubascos', 'icono': 'bi-cloud-rain-fill'}
    if c == 82:  return {'categoria': 'lluvia_fuerte', 'descripcion': 'Chubascos violentos', 'icono': 'bi-cloud-rain-heavy-fill'}
    if c in {85, 86}: return {'categoria': 'nieve', 'descripcion': 'Chubascos de nieve', 'icono': 'bi-cloud-snow-fill'}
    if c in {95}:    return {'categoria': 'tormenta', 'descripcion': 'Tormenta eléctrica', 'icono': 'bi-cloud-lightning-fill'}
    if c in {96, 99}: return {'categoria': 'tormenta', 'descripcion': 'Tormenta con granizo', 'icono': 'bi-cloud-lightning-rain-fill'}
    if c == 97:  return {'categoria': 'tormenta', 'descripcion': 'Tormenta fuerte', 'icono': 'bi-cloud-lightning-rain-fill'}
    return {'categoria': 'variable', 'descripcion': 'Condición variable', 'icono': 'bi-cloud-fill'}


def _es_hora_adversa(hora_data: dict[str, Any]) -> tuple[bool, str | None]:
    """
    Solo retorna True si los datos de ESA hora específica superan los umbrales.
    NO promedia. NO mira el día completo.
    """
    precip = hora_data.get('precipitacion_mm') or 0.0
    if precip > UMBRALES_EXCLUSION['precipitacion_mm_h']:
        return True, f"Lluvia intensa ({precip:.1f} mm/h)"
    
    wmo = hora_data.get('weather_code')
    if wmo is not None and int(wmo) in WMO_EXCLUYENTES:
        return True, f"Condición severa ({clasificar_wmo(wmo)['descripcion']})"
    
    rafagas = hora_data.get('rafagas_kmh') or 0.0
    if rafagas > UMBRALES_EXCLUSION['rafagas_kmh']:
        return True, f"Ráfagas fuertes ({rafagas:.0f} km/h)"
    
    vis = hora_data.get('visibilidad_m')
    if vis is not None and vis < UMBRALES_EXCLUSION['visibilidad_m']:
        return True, f"Visibilidad reducida ({vis:.0f} m)"
    
    return False, None


def _procesar_punto(data_punto: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """
    Retorna: { 'YYYY-MM-DD': { 'HH:MM': { datos específicos de esa hora }, ... } }
    Cada hora tiene datos EXACTOS (temperatura, precipitación, viento, etc.), no promedios.
    """
    resultado: dict[str, dict[str, Any]] = {}
    hourly = data_punto.get('hourly', {})
    times = hourly.get('time', [])
    
    if not times:
        return resultado
    
    temperatures = hourly.get('temperature_2m', [])
    precipitations = hourly.get('precipitation', [])
    precip_probs = hourly.get('precipitation_probability', [])
    weather_codes = hourly.get('weather_code', [])
    wind_speeds = hourly.get('wind_speed_10m', [])
    wind_gusts = hourly.get('wind_gusts_10m', [])
    visibilities = hourly.get('visibility', [])
    humidities = hourly.get('relative_humidity_2m', [])

    for i, t in enumerate(times):
        try:
            fecha_str, hora_str = t.split('T')
        except ValueError:
            continue
        
        hora_data = {
            'hora': hora_str,
            'temperatura': temperatures[i] if i < len(temperatures) else None,
            'precipitacion_mm': float(precipitations[i] or 0.0) if i < len(precipitations) and precipitations[i] is not None else 0.0,
            'probabilidad_precipitacion': precip_probs[i] if i < len(precip_probs) else 0,
            'weather_code': weather_codes[i] if i < len(weather_codes) else None,
            'viento_kmh': float(wind_speeds[i] or 0.0) if i < len(wind_speeds) and wind_speeds[i] is not None else 0.0,
            'rafagas_kmh': float(wind_gusts[i] or 0.0) if i < len(wind_gusts) and wind_gusts[i] is not None else 0.0,
            'visibilidad_m': visibilities[i] if i < len(visibilities) else None,
            'humedad_pct': humidities[i] if i < len(humidities) else None,
        }
        
        wmo_meta = clasificar_wmo(hora_data['weather_code'])
        hora_data['descripcion'] = wmo_meta['descripcion']
        hora_data['icono'] = wmo_meta['icono']
        
        adversa, razon = _es_hora_adversa(hora_data)
        hora_data['es_adversa'] = adversa
        hora_data['razon_adversa'] = razon
        
        if fecha_str not in resultado:
            resultado[fecha_str] = {}
        resultado[fecha_str][hora_str] = hora_data
    
    return resultado


def consultar_clima(
    zonas_requeridas: list[str],
    fecha_inicio: Any,
    num_dias: int
) -> dict[str, dict[str, dict[str, Any]]] | None:
    """
    Consulta Open-Meteo para las zonas requeridas.
    Retorna: { zona_clave: { 'YYYY-MM-DD': { 'HH:MM': {...} } } } o None si falla.
    """
    if not zonas_requeridas:
        return None
    
    if hasattr(fecha_inicio, 'date'):
        fecha_inicio = fecha_inicio.date()
    elif isinstance(fecha_inicio, str):
        try:
            fecha_inicio = datetime.strptime(fecha_inicio.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None
    
    num_dias = max(1, int(num_dias))
    fecha_fin = fecha_inicio + timedelta(days=num_dias - 1)
    fecha_hoy = datetime.now(BOLIVIA_TZ).date()
    
    # Si excede 14 días → no consultar
    if (fecha_fin - fecha_hoy).days > 14:
        logger.info("[CLIMA] Rango fuera de ventana de pronóstico (máx 14 días).")
        return None
    
    zonas_validas = [z for z in zonas_requeridas if z in PUNTOS_CLIMA]
    if not zonas_validas:
        return None
    
    # Caché
    clave_cache = f"{','.join(sorted(zonas_validas))}_{fecha_inicio}_{num_dias}"
    ahora = datetime.now().timestamp()
    if clave_cache in _CACHE_CLIMA:
        ts, data = _CACHE_CLIMA[clave_cache]
        if ahora - ts < _CACHE_TTL_SEGUNDOS:
            return data
    
    lats = [PUNTOS_CLIMA[z][0] for z in zonas_validas]
    lons = [PUNTOS_CLIMA[z][1] for z in zonas_validas]
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': ','.join(str(l) for l in lats),
        'longitude': ','.join(str(l) for l in lons),
        'hourly': 'temperature_2m,precipitation,precipitation_probability,weather_code,wind_speed_10m,wind_gusts_10m,visibility,relative_humidity_2m',
        'timezone': 'America/La_Paz',
        'start_date': fecha_inicio.strftime('%Y-%m-%d'),
        'end_date': fecha_fin.strftime('%Y-%m-%d'),
    }
    
    try:
        response = requests.get(url, params=params, timeout=3.0)
        if response.status_code != 200:
            logger.warning(f"[CLIMA] Open-Meteo status {response.status_code}")
            return None
        
        data = response.json()
        if isinstance(data, dict):
            data = [data]
        
        resultado: dict[str, dict[str, dict[str, Any]]] = {}
        for idx, item in enumerate(data):
            loc_id = item.get('location_id', idx)
            if loc_id < len(zonas_validas):
                zona = zonas_validas[loc_id]
                resultado[zona] = _procesar_punto(item)
        
        _CACHE_CLIMA[clave_cache] = (ahora, resultado)
        return resultado
    
    except Exception as e:
        logger.warning(f"[CLIMA] Error consultando Open-Meteo: {e}")
        return None


def obtener_clima_parada(
    clima_por_zona: dict[str, Any] | None,
    zona: str,
    fecha_str: str,
    hora_llegada_str: str
) -> dict[str, Any] | None:
    """
    Retorna el clima EXACTO en la hora de visita.
    { temperatura, precipitacion_mm, weather_code, descripcion, icono,
      es_adversa, razon_adversa, viento_kmh, visibilidad_m }
    o None si no hay datos.
    """
    if not clima_por_zona or zona not in clima_por_zona:
        return None
    
    dias = clima_por_zona.get(zona)
    if not dias or fecha_str not in dias:
        return None
    
    horas = dias[fecha_str]
    
    hora_key = hora_llegada_str[:5] if hora_llegada_str else '12:00'
    if hora_key in horas:
        return horas[hora_key]
    
    try:
        h_buscada = int(hora_key.split(':')[0])
        mejor_diff = 24
        mejor_hora = None
        for hk, hv in horas.items():
            h_actual = int(hk.split(':')[0])
            diff = abs(h_actual - h_buscada)
            if diff < mejor_diff:
                mejor_diff = diff
                mejor_hora = hv
        return mejor_hora
    except Exception:
        return None
