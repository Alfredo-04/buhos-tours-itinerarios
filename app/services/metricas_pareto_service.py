import json
import hashlib
import numpy as np
from app import db
from app.models.archivo_pareto import ArchivoPareto

PYMOO_INDICADORES_DISPONIBLES = True
try:
    from pymoo.indicators.hv import HV
    from pymoo.indicators.gd import GD
    from pymoo.indicators.spacing import SpacingIndicator
except ImportError:
    PYMOO_INDICADORES_DISPONIBLES = False


def calcular_hash_problema(contexto: dict) -> str:
    """
    Genera un hash SHA-256 representativo del problema multiobjetivo.
    NO incluye parámetros del algoritmo (población, generaciones, etc.)
    para que ejecuciones del mismo problema compartan el archivo de referencia de Pareto.
    """
    try:
        cadena_serializada = json.dumps(contexto, sort_keys=True, default=str)
        return hashlib.sha256(cadena_serializada.encode('utf-8')).hexdigest()
    except Exception as e:
        print(f"[WARN METRICAS] Error calculando hash del problema: {e}")
        return hashlib.sha256(str(contexto).encode('utf-8')).hexdigest()


def _filtrar_no_dominados(puntos: np.ndarray) -> np.ndarray:
    """
    Filtra y retorna el subconjunto de puntos no dominados (frente de Pareto)
    asumiendo minimización en todos los objetivos.
    """
    if puntos is None or len(puntos) <= 1:
        return puntos

    puntos = np.asarray(puntos, dtype=float)
    n_puntos = len(puntos)
    es_no_dominado = np.ones(n_puntos, dtype=bool)

    for i in range(n_puntos):
        if not es_no_dominado[i]:
            continue
        for j in range(n_puntos):
            if i != j and es_no_dominado[j]:
                # j domina a i si: todas las coord de j <= i y al menos una < i
                if np.all(puntos[j] <= puntos[i]) and np.any(puntos[j] < puntos[i]):
                    es_no_dominado[i] = False
                    break

    # Conservar puntos no dominados únicos
    indices_conservados = []
    vistos = set()
    for idx in range(n_puntos):
        if es_no_dominado[idx]:
            pt_tuple = tuple(np.round(puntos[idx], 6))
            if pt_tuple not in vistos:
                vistos.add(pt_tuple)
                indices_conservados.append(idx)

    return puntos[indices_conservados]


def calcular_y_actualizar_metricas_pareto(F_crudo, hash_problema: str) -> dict:
    """
    Calcula y persiste las métricas de calidad de Pareto (Hipervolumen, GD y Spacing/Spread).
    Contrato estricto: NUNCA lanza excepciones hacia arriba. En caso de fallo
    retorna valores por defecto (None o 0) y hace rollback de sesión.
    """
    resultado = {
        "hipervolumen": None,
        "gd": None,
        "spread": None,
        "num_soluciones_archivo_ref": 0,
    }

    if F_crudo is None or len(F_crudo) == 0:
        return resultado

    if not PYMOO_INDICADORES_DISPONIBLES:
        print("[WARN METRICAS] pymoo.indicators no disponible en el entorno")
        return resultado

    try:
        F_crudo = np.array(F_crudo, dtype=float)
        if F_crudo.ndim == 1:
            F_crudo = F_crudo.reshape(1, -1)

        # 1. Consultar archivo de referencia de Pareto existente
        archivo = ArchivoPareto.query.filter_by(hash_problema=hash_problema).first()
        ref_point = None
        valores_previos = None

        if archivo is not None:
            try:
                ref_point = np.array(json.loads(archivo.ref_point_json), dtype=float)
                valores_previos = np.array(json.loads(archivo.valores_json), dtype=float)
            except Exception as e_parse:
                print(f"[WARN METRICAS] Error deserializando archivo pareto: {e_parse}")

        # 2. Establecer punto de referencia si no existe
        if ref_point is None:
            offset = np.full(F_crudo.shape[1], 0.1)
            ref_point = F_crudo.max(axis=0) + offset

        # 3. Cálculo de Hipervolumen (HV)
        try:
            ind_hv = HV(ref_point=ref_point)
            hv_valor = ind_hv(F_crudo)
            resultado["hipervolumen"] = round(float(hv_valor), 6)
        except Exception as e_hv:
            print(f"[WARN METRICAS] Error calculando Hipervolumen: {e_hv}")

        # 4. Cálculo de GD y Spread (Spacing) si se cuenta con >= 5 puntos de referencia
        if valores_previos is not None and len(valores_previos) >= 5:
            resultado["num_soluciones_archivo_ref"] = int(len(valores_previos))
            # Generational Distance (GD)
            try:
                ind_gd = GD(pf=valores_previos)
                gd_valor = ind_gd(F_crudo)
                resultado["gd"] = round(float(gd_valor), 6)
            except Exception as e_gd:
                print(f"[WARN METRICAS] Error calculando GD: {e_gd}")

            # Spread (SpacingIndicator de pymoo)
            try:
                ind_spread = SpacingIndicator()
                spread_valor = ind_spread(F_crudo)
                resultado["spread"] = round(float(spread_valor), 6)
            except Exception as e_sp:
                print(f"[WARN METRICAS] Error calculando Spread/Spacing: {e_sp}")
        else:
            # En la primera corrida, si hay suficientes puntos en F_crudo, también podemos medir Spacing
            if len(F_crudo) > 1:
                try:
                    ind_spread = SpacingIndicator()
                    spread_valor = ind_spread(F_crudo)
                    resultado["spread"] = round(float(spread_valor), 6)
                except Exception:
                    pass

        # 5. Actualizar archivo acumulado con soluciones no dominadas
        combinar = F_crudo if valores_previos is None else np.vstack([valores_previos, F_crudo])
        nuevos_no_dom = _filtrar_no_dominados(combinar)

        if archivo is None:
            archivo = ArchivoPareto(
                hash_problema=hash_problema,
                ref_point_json=json.dumps(ref_point.tolist()),
                valores_json=json.dumps(nuevos_no_dom.tolist()),
                num_puntos=int(len(nuevos_no_dom))
            )
            db.session.add(archivo)
        else:
            archivo.valores_json = json.dumps(nuevos_no_dom.tolist())
            archivo.num_puntos = int(len(nuevos_no_dom))

        db.session.commit()

        print(f"[METRICAS] HV={resultado['hipervolumen']} GD={resultado['gd']} Spread={resultado['spread']} RefN={resultado['num_soluciones_archivo_ref']}")

    except Exception as e_general:
        print(f"[WARN METRICAS] Excepción en metricas pareto: {e_general}")
        try:
            db.session.rollback()
        except Exception:
            pass

    return resultado
