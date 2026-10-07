import time
import logging
from datetime import datetime
import requests
from app import db
from app.models.tipo_cambio import TipoCambio

logger = logging.getLogger(__name__)

# Caché en memoria para evitar saturar el endpoint (TTL: 1 hora)
_TC_CACHE = {
    'datos': None,  # dict con {compra, venta, fecha, fuente, conectado, mensaje}
    'timestamp': 0,
    'ttl': 3600  # 1 hora en segundos
}

BCB_API_URL = "https://apibcb.cucu.bo/api/v1/tc/oficial"

def obtener_tc_api() -> dict:
    """
    Consulta la API del BCB: GET https://apibcb.cucu.bo/api/v1/tc/oficial
    Retorna dict: {compra: float, venta: float, fecha: str, fuente: str, conectado: bool, mensaje: str}
    """
    try:
        response = requests.get(BCB_API_URL, timeout=4)
        if response.status_code == 200:
            data = response.json()
            tc_data = data.get('tc_oficial', {})
            compra_raw = tc_data.get('compra')
            venta_raw = tc_data.get('venta') or tc_data.get('valor')
            fecha_raw = tc_data.get('fecha') or datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

            if compra_raw is not None and venta_raw is not None:
                compra = float(compra_raw)
                venta = float(venta_raw)
                return {
                    'compra': compra,
                    'venta': venta,
                    'fecha': str(fecha_raw),
                    'fuente': 'api',
                    'conectado': True,
                    'mensaje': 'Conexión exitosa con la API del BCB.'
                }
            else:
                return {
                    'compra': 6.96,
                    'venta': 7.06,
                    'fecha': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    'fuente': 'default',
                    'conectado': False,
                    'mensaje': 'La API del BCB respondió pero los campos de compra/venta no están completos.'
                }
        else:
            return {
                'compra': 6.96,
                'venta': 7.06,
                'fecha': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'fuente': 'default',
                'conectado': False,
                'mensaje': f'La API del BCB respondió con código HTTP {response.status_code}.'
            }
    except Exception as e:
        logger.warning(f"Error consultando API del BCB: {e}")
        return {
            'compra': 6.96,
            'venta': 7.06,
            'fecha': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'fuente': 'default',
            'conectado': False,
            'mensaje': f'No se pudo conectar a la API del BCB: {str(e)}'
        }

def obtener_tc_actual(forzar_refresco: bool = False) -> dict:
    """
    Obtiene el tipo de cambio actual según la jerarquía requerida:
    1. Intenta obtener de la API (con caché en memoria de 1 hora si no se fuerza).
    2. Si falla la API, busca el último registro en la base de datos (tabla TIPO_CAMBIO).
    3. Si no hay ninguno en BD, retorna valores por defecto (compra=6.96, venta=7.06).
    Retorna un dict con: {compra, venta, fecha, fuente, conectado: True/False, mensaje: "..."}
    """
    ahora = time.time()
    if not forzar_refresco and _TC_CACHE['datos'] is not None and (ahora - _TC_CACHE['timestamp'] < _TC_CACHE['ttl']):
        return _TC_CACHE['datos']

    # 1. Intentar API
    res_api = obtener_tc_api()
    if res_api.get('conectado'):
        _TC_CACHE['datos'] = res_api
        _TC_CACHE['timestamp'] = ahora
        return res_api

    # 2. Si falla la API, buscar último registro en la base de datos
    try:
        ultimo_tc = TipoCambio.query.order_by(TipoCambio.fecha.desc()).first()
        if ultimo_tc:
            res_bd = {
                'compra': float(ultimo_tc.valor_compra),
                'venta': float(ultimo_tc.valor_venta),
                'fecha': ultimo_tc.fecha.strftime('%Y-%m-%d %H:%M:%S') if ultimo_tc.fecha else datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'fuente': ultimo_tc.fuente or 'bd',
                'conectado': False,
                'mensaje': f"API no disponible. Usando último registro en BD ({ultimo_tc.fuente}) del {ultimo_tc.fecha.strftime('%d/%m/%Y %H:%M') if ultimo_tc.fecha else ''}."
            }
            _TC_CACHE['datos'] = res_bd
            _TC_CACHE['timestamp'] = ahora
            return res_bd
    except Exception as e:
        logger.error(f"Error consultando último TipoCambio en base de datos: {e}")

    # 3. Valores por defecto
    res_default = {
        'compra': 6.96,
        'venta': 7.06,
        'fecha': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        'fuente': 'default',
        'conectado': False,
        'mensaje': 'API y BD no disponibles o vacías. Usando valores oficiales por defecto (6.96 / 7.06).'
    }
    _TC_CACHE['datos'] = res_default
    _TC_CACHE['timestamp'] = ahora
    return res_default

def guardar_tc_desde_api() -> tuple[bool, str, TipoCambio | None]:
    """
    Llama a la API del BCB y si es exitosa, guarda el nuevo registro en TIPO_CAMBIO.
    Retorna (éxito, mensaje, objeto_guardado)
    """
    res_api = obtener_tc_api()
    if not res_api.get('conectado'):
        return False, f"No se pudo obtener datos de la API: {res_api.get('mensaje')}", None

    try:
        nuevo_tc = TipoCambio(
            fecha=datetime.utcnow(),
            valor_compra=res_api['compra'],
            valor_venta=res_api['venta'],
            fuente='api',
            id_usuario=None
        )
        db.session.add(nuevo_tc)
        db.session.commit()

        # Actualizar caché
        _TC_CACHE['datos'] = res_api
        _TC_CACHE['timestamp'] = time.time()
        return True, "Tipo de cambio sincronizado y guardado exitosamente desde la API del BCB.", nuevo_tc
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al guardar TipoCambio desde API: {e}")
        return False, f"Error al guardar en la base de datos: {str(e)}", None

def guardar_tc_manual(valor_compra: float, valor_venta: float, id_usuario: int | None = None) -> tuple[bool, str, TipoCambio | None]:
    """
    Guarda un registro manual en la tabla TIPO_CAMBIO.
    Retorna (éxito, mensaje, objeto_guardado)
    """
    try:
        if valor_compra <= 0 or valor_venta <= 0:
            return False, "Los valores de compra y venta deben ser mayores a cero.", None

        nuevo_tc = TipoCambio(
            fecha=datetime.utcnow(),
            valor_compra=valor_compra,
            valor_venta=valor_venta,
            fuente='manual',
            id_usuario=id_usuario
        )
        db.session.add(nuevo_tc)
        db.session.commit()

        # Actualizar caché para reflejar este nuevo valor manual de inmediato
        _TC_CACHE['datos'] = {
            'compra': float(valor_compra),
            'venta': float(valor_venta),
            'fecha': nuevo_tc.fecha.strftime('%Y-%m-%d %H:%M:%S'),
            'fuente': 'manual',
            'conectado': True,
            'mensaje': 'Tipo de cambio manual registrado exitosamente.'
        }
        _TC_CACHE['timestamp'] = time.time()

        return True, "Tipo de cambio manual registrado con éxito.", nuevo_tc
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al guardar TipoCambio manual: {e}")
        return False, f"Error al guardar registro manual: {str(e)}", None

def listar_tc(page: int = 1, per_page: int = 10):
    """
    Lista los registros de TIPO_CAMBIO ordenados por fecha descendente de forma paginada.
    """
    return TipoCambio.query.order_by(TipoCambio.fecha.desc()).paginate(page=page, per_page=per_page, error_out=False)

def eliminar_tc(id_tipo_cambio: int) -> tuple[bool, str]:
    """
    Elimina un registro de TIPO_CAMBIO por ID (solo admin).
    """
    try:
        tc = TipoCambio.query.get(id_tipo_cambio)
        if not tc:
            return False, "El registro de tipo de cambio no existe."
        db.session.delete(tc)
        db.session.commit()

        # Invalidar caché para forzar recálculo
        _TC_CACHE['timestamp'] = 0

        return True, "Registro de tipo de cambio eliminado correctamente."
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error eliminando TipoCambio #{id_tipo_cambio}: {e}")
        return False, f"Error al eliminar el registro: {str(e)}"

# Funciones de compatibilidad global para vistas, filtros y plantillas
def obtener_tc_oficial(forzar_refresco: bool = False) -> float:
    """
    Retorna el valor de venta oficial actual (float) para ser usado en conversiones a USD en todo el sistema.
    """
    datos = obtener_tc_actual(forzar_refresco=forzar_refresco)
    return float(datos.get('venta', 7.06))

def obtener_info_tc() -> dict:
    """
    Retorna el dict completo de estado actual del tipo de cambio.
    """
    return obtener_tc_actual()

def convertir_bs_a_usd(monto_bs: float | int | None, tc: float | None = None) -> float | None:
    """
    Convierte un monto en Bolivianos a Dólares Americanos usando el TC oficial provisto o consultado.
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
