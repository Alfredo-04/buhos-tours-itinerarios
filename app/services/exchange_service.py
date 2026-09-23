import time
import logging
import requests

logger = logging.getLogger(__name__)

# Caché en memoria para evitar saturar el endpoint (límite 120 req/h)
_TC_CACHE = {
    'valor': None,
    'datos_completos': None,
    'timestamp': 0,
    'ttl': 3600  # 1 hora en segundos
}

BCB_API_URL = "https://apibcb.cucu.bo/api/v1/tc/oficial"

def obtener_tc_oficial(forzar_refresco: bool = False) -> float:
    """
    Obtiene el Tipo de Cambio Oficial (venta referencial BCB) desde la API del BCB.
    Mantiene un caché en memoria con TTL de 1 hora (3600s).
    
    Fallback: Si la API falla, utiliza el último valor en caché o 6.96 BOB/USD.
    """
    ahora = time.time()
    if not forzar_refresco and _TC_CACHE['valor'] is not None and (ahora - _TC_CACHE['timestamp'] < _TC_CACHE['ttl']):
        return _TC_CACHE['valor']

    try:
        response = requests.get(BCB_API_URL, timeout=4)
        if response.status_code == 200:
            data = response.json()
            tc_data = data.get('tc_oficial', {})
            # Priorizar tipo de cambio venta oficial del BCB
            valor_raw = tc_data.get('venta') or tc_data.get('valor') or tc_data.get('compra')
            if valor_raw is not None:
                valor_float = float(valor_raw)
                _TC_CACHE['valor'] = valor_float
                _TC_CACHE['datos_completos'] = tc_data
                _TC_CACHE['timestamp'] = ahora
                logger.info(f"Tipo de cambio oficial actualizado desde BCB: {valor_float} BOB/USD (Venta)")
                return valor_float
            else:
                logger.warning("Respuesta de API BCB no contiene un valor numérico de tipo de cambio válido.")
        else:
            logger.warning(f"API BCB respondió con código de estado HTTP {response.status_code}.")
    except Exception as e:
        logger.error(f"Error al consultar el tipo de cambio oficial en la API del BCB: {str(e)}")

    if forzar_refresco:
        _TC_CACHE['valor'] = None
        _TC_CACHE['datos_completos'] = None
        _TC_CACHE['timestamp'] = 0

    # Fallback: último valor cacheado o valor referencial oficial 6.96
    return _TC_CACHE['valor'] if _TC_CACHE['valor'] is not None else 6.96

def obtener_info_tc() -> dict | None:
    """
    Retorna la información completa del tipo de cambio si está disponible.
    """
    obtener_tc_oficial()
    return _TC_CACHE.get('datos_completos')

def convertir_bs_a_usd(monto_bs: float | int | None, tc: float | None = None) -> float | None:
    """
    Convierte un monto en Bolivianos a Dólares Americanos usando el TC oficial provisto o consultado.
    Retorna None si no hay cotización disponible o el monto es nulo.
    """
    if monto_bs is None:
        return None
    try:
        monto_float = float(monto_bs)
    except (ValueError, TypeError):
        return None

    tipo_cambio = tc if tc is not None else obtener_tc_oficial()
    if not tipo_cambio or tipo_cambio <= 0:
        return None

    return round(monto_float / tipo_cambio, 2)
