from typing import Any
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
import io
import uuid
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.models.atractivo import Atractivo
from app.models.subcategoria import Subcategoria
from app.models.transporte import Transporte
from app.models.categoria import Categoria
from app.models.generacion import Generacion
from app.models.consulta_nsga2 import ConsultaNSGA2
from app.models.itinerario import Itinerario
from app.models.itinerario_detalle import ItinerarioDetalle
from app.models.itinerario_detalle_trafico import ItinerarioDetalleTrafico
from app.models.turista import Turista
from app.models.viaje_turista import ViajeTurista
from app.models.usuario import Usuario
from app.services.nsga2_service import ejecutar_nsga2
from app import db


BOLIVIA_TZ = timezone(timedelta(hours=-4))

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
            "dias_cerrado": a.dias_cerrado or "",
            "horario_apertura": a.horario_apertura,
            "horario_cierre": a.horario_cierre,
            "sensible_al_clima": bool(getattr(a, 'sensible_al_clima', False)),
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
    intereses: dict[str, float],
    fecha_inicio_viaje: str | None = None,
    num_dias_disponibles: int = 1,
    hora_inicio_dia: str = '09:00',
    hora_fin_dia: str = '18:00',
    auto_fechas: bool = True,
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
    tiempo_disponible_horas: float | None = None,
    usar_clima: bool = True,
    id_usuario: int | None = None,
    permitir_multiples_vehiculos: bool = False,
    **kwargs: Any
) -> dict[str, Any]:
    """
    Orquesta el flujo de generación de itinerarios turísticos multiobjetivo con NSGA-II:
    1. Validaciones de integridad de entrada (min/max paradas, cantidad de atractivos).
    2. Rate limiting (3 seg) y deduplicación (2 min) por usuario para evitar spam.
    3. Carga y filtro de atractivos y transportes disponibles.
    4. Ejecución del algoritmo NSGA-II multiobjetivo.
    5. Persistencia y auditoría de la consulta en las tablas Generacion y ConsultaNSGA2.
    """
    # 1. VALIDACIÓN DE INTEGRIDAD (Payload)
    if min_paradas is not None and max_paradas is not None and min_paradas > max_paradas:
        raise ValueError("El mínimo de paradas no puede ser mayor al máximo.")
    if atractivos_ids is not None and len(atractivos_ids) == 1:
        raise ValueError("Debes seleccionar al menos 2 atractivos turísticos.")

    # 1.1 Resolver las fechas reales ANTES de calcular el hash
    # Asumiendo que 'fecha_inicio_viaje' puede venir como None si 'auto_fechas' es True
    fecha_hoy = datetime.now(BOLIVIA_TZ).date()

    if auto_fechas or not fecha_inicio_viaje:
        # Regla por defecto: empieza mañana
        fecha_inicio_resuelta = fecha_hoy + timedelta(days=1)
    else:
        # Si el usuario puso una fecha, la usamos (viene como string o date, la convertimos a date)
        if isinstance(fecha_inicio_viaje, str):
            try:
                fecha_inicio_resuelta = datetime.strptime(fecha_inicio_viaje.strip()[:10], '%Y-%m-%d').date()
            except ValueError:
                fecha_inicio_resuelta = fecha_hoy + timedelta(days=1)
        elif isinstance(fecha_inicio_viaje, datetime):
            fecha_inicio_resuelta = fecha_inicio_viaje.date()
        else:
            fecha_inicio_resuelta = fecha_inicio_viaje

    # 1.2 Construir el payload_dict blindado CON LA FECHA RESUELTA
    t_ids = kwargs.get('transportes_ids') or transporte_ids or []
    payload_dict = {
        "atractivos_ids": sorted([int(x) for x in atractivos_ids]) if atractivos_ids else [],
        "transportes_ids": sorted([int(x) for x in t_ids]) if t_ids else [],
        "categorias_activas_ids": sorted([int(x) for x in categorias_activas_ids]) if categorias_activas_ids else [],
        "subcategorias_activas_ids": sorted([int(x) for x in subcategorias_activas_ids]) if subcategorias_activas_ids else [],

        "presupuesto_max": float(presupuesto_max),
        "num_personas": int(num_personas),
        "min_paradas": int(min_paradas),
        "max_paradas": int(max_paradas),

        # ¡AQUÍ ESTÁ LA MAGIA! Usamos la fecha resuelta, no los inputs sueltos
        "fecha_inicio_resuelta": str(fecha_inicio_resuelta),
        "num_dias_disponibles": int(num_dias_disponibles),
        "hora_inicio_dia": str(hora_inicio_dia),
        "hora_fin_dia": str(hora_fin_dia),

        "auto_rango_paradas": bool(auto_rango_paradas),
        "forzar_atractivos": bool(forzar_atractivos),
        "forzar_transporte": bool(forzar_transporte),
        "permitir_multiples_vehiculos": bool(permitir_multiples_vehiculos),
        "usar_clima": bool(usar_clima),
        "tiempo_disponible_horas": float(tiempo_disponible_horas) if tiempo_disponible_horas else 0.0,
        "intereses": {str(k): float(v) for k, v in sorted(intereses.items())} if intereses else {},

        "tamano_poblacion": int(tamano_poblacion),
        "generaciones": int(generaciones),
        "prob_cruce": float(prob_cruce),
        "prob_mutacion": float(prob_mutacion),
    }

    # Serializar el diccionario a un string JSON ordenado
    payload_str = json.dumps(payload_dict, sort_keys=True)
    hash_actual = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()

    # 2. LÓGICA DE CACHÉ Y RATE LIMITING (DESACTIVADO TEMPORALMENTE PARA PRUEBAS Y DESARROLLO)
    # if id_usuario:
    #     # a) Buscar si este usuario ya hizo esta consulta y tiene resultados guardados en caché
    #     consulta_existente = db.session.query(ConsultaNSGA2).join(
    #         Generacion, ConsultaNSGA2.id_generacion == Generacion.id_generacion
    #     ).filter(
    #         Generacion.id_usuario == id_usuario,
    #         ConsultaNSGA2.hash_parametros == hash_actual
    #     ).order_by(ConsultaNSGA2.fecha.desc()).first()
    # 
    #     # Lógica de Caché con Expiración (24 horas)
    #     if consulta_existente and consulta_existente.resultados_json:
    #         fecha_consulta = consulta_existente.fecha
    #         # Usar hora Bolivia local (naive) para que reste bien con la BD
    #         ahora = datetime.now(BOLIVIA_TZ).replace(tzinfo=None)
    # 
    #         tiempo_transcurrido = (ahora - fecha_consulta).total_seconds()
    # 
    #         # Si pasaron menos de 24 horas (ignorando tiempos negativos de datos viejos)
    #         if 0 <= tiempo_transcurrido < 86400:
    #             print("[CACHE HIT] Devolviendo resultados guardados sin ejecutar NSGA-II.")
    #             try:
    #                 resultados_cacheados = json.loads(consulta_existente.resultados_json)
    #                 if isinstance(resultados_cacheados, dict):
    #                     resultados_cacheados['id_generacion'] = consulta_existente.id_generacion
    #                 return resultados_cacheados
    #             except Exception as ex_json:
    #                 print(f"[CACHE ERROR] No se pudo deserializar resultados_json ({ex_json}), ejecutando NSGA-II...")
    #         else:
    #             print("[CACHE EXPIRADO] La consulta tiene más de 24h. Recalculando itinerario...")
    # 
    #     # b) Rate Limiting (esperar 3 segundos entre consultas consecutivas cuando es consulta nueva)
    #     ultima_gen = Generacion.query.filter_by(id_usuario=id_usuario).order_by(Generacion.fecha_generacion.desc()).first()
    # 
    #     if ultima_gen and ultima_gen.fecha_generacion:
    #         # Usar hora Bolivia local (naive)
    #         ahora = datetime.now(BOLIVIA_TZ).replace(tzinfo=None)
    #         fecha_gen = ultima_gen.fecha_generacion
    #         segundos_desde_ultima = (ahora - fecha_gen).total_seconds()
    #         # Si el tiempo es positivo y menor a 3 segundos, bloquea
    #         if 0 <= segundos_desde_ultima < 3:
    #             raise ValueError("Por favor, espera unos segundos antes de volver a generar.")

    print("[DEV MODE] Caché y Rate Limiting desactivados temporalmente. Ejecutando NSGA-II...")

    # 3. Preparar datos desde la base de datos
    atractivos_data, transportes_data = preparar_datos_nsga2(
        atractivos_ids=atractivos_ids,
        transporte_ids=transporte_ids,
        categorias_activas_ids=categorias_activas_ids,
        subcategorias_activas_ids=subcategorias_activas_ids,
    )

    if len(atractivos_data) < 2:
        raise ValueError("Debes seleccionar al menos 2 atractivos turísticos.")

    if len(transportes_data) < 1:
        raise ValueError("No se encontraron medios de transporte disponibles para planificar el viaje.")

    # Contexto K LIBRE cuando:
    #   - auto_rango_paradas == True
    #   Y
    #   - no hay atractivos seleccionados explícitamente
    k_libre = bool(auto_rango_paradas) and (len(atractivos_ids or []) == 0)

    # 4. Ejecutar el motor puro NSGA-II
    resultado = ejecutar_nsga2(
        atractivos=atractivos_data,
        transportes=transportes_data,
        presupuesto_max=float(presupuesto_max),
        fecha_inicio_viaje=fecha_inicio_viaje,
        num_dias_disponibles=int(num_dias_disponibles),
        hora_inicio_dia=hora_inicio_dia,
        hora_fin_dia=hora_fin_dia,
        auto_fechas=bool(auto_fechas),
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
        tiempo_disponible_horas=tiempo_disponible_horas,
        usar_clima=bool(usar_clima),
        k_libre=k_libre,
        atractivos_ids=atractivos_ids,
        atractivos_seleccionados_explicitamente=bool(atractivos_ids and len(atractivos_ids) > 0),
        permitir_multiples_vehiculos=bool(permitir_multiples_vehiculos),
    )

    # 5. GUARDADO EN BD (Generación y ConsultaNSGA2)
    if id_usuario:
        try:
            # Extraer fechas resueltas
            fecha_ini_str = resultado.get('parametros_usados', {}).get('fecha_inicio_viaje')
            if fecha_ini_str and isinstance(fecha_ini_str, str):
                try:
                    fecha_ini_date = datetime.strptime(fecha_ini_str, "%Y-%m-%d").date()
                except ValueError:
                    fecha_ini_date = datetime.now(BOLIVIA_TZ).date() + timedelta(days=1)
            elif hasattr(fecha_ini_str, 'year'):
                fecha_ini_date = fecha_ini_str
            else:
                fecha_ini_date = datetime.now(BOLIVIA_TZ).date() + timedelta(days=1)

            dias_tot = int(resultado.get('parametros_usados', {}).get('num_dias_disponibles', num_dias_disponibles or 1))
            fecha_fin_date = fecha_ini_date + timedelta(days=max(0, dias_tot - 1))

            # Extraer horas diarias
            h_ini_raw = resultado.get('parametros_usados', {}).get('hora_inicio_dia', hora_inicio_dia)
            h_fin_raw = resultado.get('parametros_usados', {}).get('hora_fin_dia', hora_fin_dia)
            hora_ini_obj = None
            hora_fin_obj = None
            if h_ini_raw:
                if hasattr(h_ini_raw, 'hour'):
                    hora_ini_obj = h_ini_raw
                else:
                    try:
                        hora_ini_obj = datetime.strptime(str(h_ini_raw)[:5], "%H:%M").time()
                    except ValueError:
                        pass
            if h_fin_raw:
                if hasattr(h_fin_raw, 'hour'):
                    hora_fin_obj = h_fin_raw
                else:
                    try:
                        hora_fin_obj = datetime.strptime(str(h_fin_raw)[:5], "%H:%M").time()
                    except ValueError:
                        pass

            soluciones = resultado.get('soluciones', [])
            num_sols = len(soluciones)
            mejor_afinidad = max([s.get('afinidad', 0.0) for s in soluciones], default=0.0) if soluciones else 0.0
            mejor_tiempo = min([s.get('tiempo_total_min', 0.0) for s in soluciones], default=0.0) if soluciones else 0.0

            # a) Crear la Generación primero (padre)
            nueva_generacion = Generacion(
                id_usuario=id_usuario,
                fecha_inicio_viaje=fecha_ini_date,
                fecha_fin_viaje=fecha_fin_date,
                presupuesto=presupuesto_max,
                cantidad_soluciones=num_sols,
                observaciones=f"Optimización NSGA-II ({'Viable' if resultado.get('hay_viables') else 'No viable'})",
                hora_inicio_dia=hora_ini_obj,
                hora_fin_dia=hora_fin_obj,
                auto_rango_paradas=bool(auto_rango_paradas),
                min_paradas=int(min_paradas),
                max_paradas=int(max_paradas),
                usar_clima=bool(usar_clima),
                intereses_json=json.dumps(intereses, ensure_ascii=False) if intereses else None,
            )
            db.session.add(nueva_generacion)
            db.session.flush()  # Para obtener el id_generacion generado
            resultado['id_generacion'] = nueva_generacion.id_generacion

            # b) Crear la ConsultaNSGA2 vinculada
            hist_afin = resultado.get('historial_convergencia', {}).get('mejor_afinidad', [])
            convergencia_val = float(hist_afin[-1]) if hist_afin else None

            hist_div = resultado.get('historial_diversidad', {}).get('diversidad', [])
            diversidad_val = float(hist_div[-1]) if hist_div else None

            tiempo_disp = resultado.get('parametros_usados', {}).get('tiempo_disponible_horas')
            if tiempo_disp is None:
                tiempo_disp = float(tiempo_disponible_horas or (dias_tot * 9.0))

            params_usados = resultado.get('parametros_usados', {})
            poblacion_guardar = int(params_usados.get('tamano_poblacion', tamano_poblacion))
            generaciones_guardar = int(params_usados.get('generaciones', generaciones))
            mutacion_guardar = float(params_usados.get('prob_mutacion', prob_mutacion))

            nueva_consulta = ConsultaNSGA2(
                id_generacion=nueva_generacion.id_generacion,  # Relación FK
                num_atractivos=len(atractivos_ids) if atractivos_ids else len(atractivos_data),
                num_transportes=len(transporte_ids) if transporte_ids else len(transportes_data),
                presupuesto=presupuesto_max,
                tiempo_disponible_horas=tiempo_disp,
                intereses=json.dumps(intereses, ensure_ascii=False) if intereses else None,
                tamano_poblacion=poblacion_guardar,
                generaciones=generaciones_guardar,
                prob_cruce=float(params_usados.get('prob_cruce', prob_cruce)),
                prob_mutacion=mutacion_guardar,
                num_soluciones=num_sols,
                mejor_afinidad=mejor_afinidad,
                mejor_tiempo=mejor_tiempo,
                soluciones_viables=resultado.get('total_soluciones_viables', len(resultado.get('soluciones_viables', []))),
                todas_exceden=not bool(resultado.get('hay_viables', False)),
                tiempo_ejecucion_seg=resultado.get('tiempo_ejecucion_seg', 0.0),
                convergencia=convergencia_val,
                diversidad_final=diversidad_val,
                hipervolumen=resultado.get('hipervolumen'),
                generational_distance=resultado.get('gd'),
                spread_spacing=resultado.get('spread'),
                fecha_inicio_viaje=fecha_ini_date,
                fecha_fin_viaje=fecha_fin_date,
                hora_inicio_dia=hora_ini_obj,
                hora_fin_dia=hora_fin_obj,
                auto_rango_paradas=bool(auto_rango_paradas),
                min_paradas=int(min_paradas),
                max_paradas=int(max_paradas),
                usar_clima=bool(usar_clima),
                atractivos_ids_json=json.dumps(atractivos_ids or [a['id'] for a in atractivos_data]),
                transporte_ids_json=json.dumps(transporte_ids or [t['id'] for t in transportes_data]),
                hubo_soluciones_viables=bool(resultado.get('hay_viables', False)),
                vector_instancia_json=resultado.get('vector_instancia_json'),
                id_archivo_pareto=resultado.get('id_archivo_pareto'),
                resultados_json=json.dumps(resultado, default=str, ensure_ascii=False),  # Guardar JSON completo en caché
            )
            db.session.add(nueva_consulta)
            db.session.commit()

            resultado['id_generacion'] = nueva_generacion.id_generacion

        except Exception as e:
            db.session.rollback()
            print(f"[WARNING] No se pudo guardar la auditoría en BD: {e}")
            # No lanzar la excepción. El usuario igual recibe sus itinerarios.

    return resultado


def validar_documento_por_procedencia(doc: str | None, procedencia: str | None) -> tuple[bool, str, str]:
    """
    Valida y formatea el documento de identidad según la procedencia del turista.
    Retorna: (es_valido: bool, doc_limpio: str, mensaje_error: str)
    
    Reglas del mundo real:
    - Bolivia: Cédula de Identidad (C.I.).
      Debe contener entre 5 y 8 dígitos base numéricos.
      Opcionalmente puede tener complemento (ej. -1A) y/o extensión (ej. LP, SC, CB, etc.).
    - Extranjero: Pasaporte o DNI Internacional.
      Debe ser alfanumérico limpio de 6 a 15 caracteres (sin caracteres raros).
    """
    if not doc:
        return True, "", ""
    
    doc_limpio = str(doc).strip().upper()
    proc = str(procedencia or "").strip().lower()
    es_bolivia = (proc == "bolivia" or proc == "bo" or "bolivia" in proc)

    if es_bolivia:
        # Formato C.I. Bolivia:
        # Ejemplos válidos: 4892341, 10923842, 4892341-1A, 4892341 LP, 4892341-1A LP
        # Patrón: ^(\d{5,8})(-[0-9A-Z]{1,2})?(\s*(LP|CB|SC|PT|OR|TJ|CH|BE|PD))?$
        patron_ci = r'^(\d{5,8})(-[0-9A-Z]{1,2})?(\s+(LP|CB|SC|PT|OR|TJ|CH|BE|PD))?$'
        if not re.match(patron_ci, doc_limpio):
            return False, doc_limpio, (
                "Para Bolivia, el Carnet de Identidad (C.I.) debe contener entre 5 y 8 números "
                "(opcionalmente complemento ej. '-1A' y extensión ej. 'LP')."
            )
        return True, doc_limpio, ""
    else:
        # Formato Internacional (Pasaporte / DNI):
        # 6 a 15 caracteres alfanuméricos
        patron_pasaporte = r'^[A-Z0-9-]{6,15}$'
        if not re.match(patron_pasaporte, doc_limpio):
            return False, doc_limpio, (
                "Para turistas extranjeros, el Pasaporte / DNI debe ser alfanumérico de 6 a 15 caracteres."
            )
        # Rechazar si son solo letras o contiene caracteres inválidos
        if doc_limpio.isalpha() and len(doc_limpio) > 10:
            return False, doc_limpio, "El documento extranjero no parece ser válido (solo texto largo)."
        return True, doc_limpio, ""


def buscar_turista(nro_documento: str | None, procedencia: str | None) -> dict:
    """
    Busca un turista existente por combinación de documento y procedencia.
    - Si nro_documento está vacío o es None: {"encontrado": False, "motivo": "sin_documento"}.
    - Si procedencia está vacío o es None: {"encontrado": False, "motivo": "sin_procedencia"}.
    - Si no existe: {"encontrado": False, "motivo": "no_existe"}.
    - Si existe y la procedencia coincide (normalizada): {"encontrado": True, "turista": {...}}.
    - Si existe pero la procedencia difiere: {"encontrado": False, "motivo": "conflicto_procedencia", "procedencia_registrada": ..., "id_turista": ...}.
    """
    if not nro_documento or not str(nro_documento).strip():
        return {"encontrado": False, "motivo": "sin_documento"}

    if not procedencia or not str(procedencia).strip():
        return {"encontrado": False, "motivo": "sin_procedencia"}

    doc = str(nro_documento).strip()
    proc_buscada = str(procedencia).strip().lower()

    turista = Turista.query.filter_by(nro_documento=doc).first()
    if not turista:
        return {"encontrado": False, "motivo": "no_existe"}

    proc_existente = (turista.procedencia or "").strip().lower()
    if proc_existente == proc_buscada:
        return {
            "encontrado": True,
            "turista": {
                "id_turista": turista.id_turista,
                "nombres": turista.nombres,
                "apellidos": turista.apellidos,
                "nro_documento": turista.nro_documento,
                "procedencia": turista.procedencia or "",
                "email": turista.email or "",
                "telefono": turista.telefono or ""
            }
        }
    else:
        return {
            "encontrado": False,
            "motivo": "conflicto_procedencia",
            "procedencia_registrada": turista.procedencia or "",
            "id_turista": turista.id_turista
        }


def buscar_turista_por_documento(nro_documento: str) -> dict:
    """Wrapper de compatibilidad retroactiva."""
    if not nro_documento or not str(nro_documento).strip():
        return {"encontrado": False}
    doc = str(nro_documento).strip()
    turista = Turista.query.filter_by(nro_documento=doc).first()
    if not turista:
        return {"encontrado": False}
    return {
        "encontrado": True,
        "turista": {
            "id_turista": turista.id_turista,
            "nombres": turista.nombres,
            "apellidos": turista.apellidos,
            "nro_documento": turista.nro_documento,
            "procedencia": turista.procedencia or "",
            "email": turista.email or "",
            "telefono": turista.telefono or ""
        }
    }


def guardar_itinerario(
    id_generacion: int,
    numero_solucion: int,
    datos_turista: dict | None = None,
    id_usuario: int | None = None,
    turista_data: dict | None = None,
    forzar_nuevo: bool = False,
    tiempo_consulta_seg: float | None = None,
    iteraciones_optimizacion: int | None = None
) -> dict:
    """
    Toma una solución del JSON de caché y la guarda en las tablas definitivas de itinerario.
    Incluye validación de viabilidad, deduplicación según rol, guardado de Turista y ViajeTurista,
    snapshot_json, id_transporte real no nulo y advertencia de acompañantes.
    """
    turista_data = turista_data or datos_turista
    # 1. Buscar la generación y su consulta (caché JSON)
    generacion = Generacion.query.get(id_generacion)
    if not generacion:
        raise ValueError("Generación no encontrada.")

    consulta = ConsultaNSGA2.query.filter_by(id_generacion=id_generacion).first()
    if not consulta or not consulta.resultados_json:
        raise ValueError("No se encontraron los resultados en caché para guardar.")

    usuario = Usuario.query.get(id_usuario)
    rol_nombre = (usuario.rol.nombre if usuario and usuario.rol else '').lower()

    # BLOQUE 5: Manejo de Duplicados
    if rol_nombre == 'turista':
        # Para Turistas: Si intenta guardar el mismo itinerario, buscar en ViajeTurista uniendo con Turista (donde id_usuario = current_user.id_usuario)
        ya_guardado_turista = db.session.query(Itinerario).join(
            ViajeTurista, Itinerario.id_itinerario == ViajeTurista.id_itinerario
        ).join(
            Turista, ViajeTurista.id_turista == Turista.id_turista
        ).filter(
            Itinerario.id_generacion == id_generacion,
            Itinerario.numero_solucion == int(numero_solucion),
            Itinerario.deleted_at.is_(None),
            Turista.id_usuario == id_usuario
        ).first()

        if ya_guardado_turista:
            raise ValueError("Ya has guardado este itinerario. Puedes verlo en tu lista de cotizaciones.")
    elif rol_nombre in ['admin', 'agente']:
        # Para Admin/Agente: Si ya existe, preguntar si desea crear nueva cotización
        existente = Itinerario.query.filter_by(
            id_generacion=id_generacion,
            numero_solucion=int(numero_solucion),
            deleted_at=None
        ).first()
        if existente and not forzar_nuevo:
            return {
                "duplicado_admin": True,
                "mensaje": "Este itinerario ya fue guardado antes. ¿Deseas crear una nueva cotización para un nuevo grupo?"
            }

    resultados = json.loads(consulta.resultados_json)

    # Buscar la solución específica
    soluciones = resultados.get('soluciones_viables', []) + resultados.get('soluciones_no_viables', [])
    if not soluciones:
        soluciones = resultados.get('soluciones', [])

    sol = next((s for s in soluciones if s.get('numero') == int(numero_solucion) or s.get('numero_solucion') == int(numero_solucion)), None)
    if not sol:
        try:
            sol = soluciones[int(numero_solucion) - 1]
        except (IndexError, ValueError):
            raise ValueError("Número de solución no válido.")

    # BLOQUE 1: Bloqueo de No Viables en Backend
    es_viable = sol.get('cumple_restricciones', True)
    if not es_viable:
        raise ValueError("No se pueden guardar itinerarios no viables.")

    # BLOQUE 2: Buscar o crear Turista (validación estricta de procedencia y doc)
    turista = None
    if turista_data and isinstance(turista_data, dict):
        procedencia = str(turista_data.get('procedencia') or '').strip()
        if not procedencia:
            raise ValueError("La procedencia es obligatoria.")

        nombres = str(turista_data.get('nombres') or '').strip()
        apellidos = str(turista_data.get('apellidos') or '').strip()
        if not nombres or not apellidos:
            raise ValueError("Nombres y Apellidos del turista son campos obligatorios.")

        doc = str(turista_data.get('nro_documento') or '').strip()
        if doc:
            valido_doc, doc_formateado, err_doc = validar_documento_por_procedencia(doc, procedencia)
            if not valido_doc:
                raise ValueError(err_doc)
            doc = doc_formateado

            resultado_busqueda = buscar_turista(doc, procedencia)
            if resultado_busqueda.get("motivo") == "conflicto_procedencia":
                raise ValueError(
                    f"El documento {doc} ya está registrado con procedencia '{resultado_busqueda.get('procedencia_registrada')}'. "
                    f"Verifica el país o usa otro documento."
                )
            if resultado_busqueda.get("encontrado"):
                turista = Turista.query.get(resultado_busqueda["turista"]["id_turista"])
                if nombres:
                    turista.nombres = nombres
                if apellidos:
                    turista.apellidos = apellidos
                if turista_data.get('email'):
                    turista.email = turista_data.get('email')
                if turista_data.get('telefono'):
                    turista.telefono = turista_data.get('telefono')
                if rol_nombre == 'turista' and not turista.id_usuario:
                    turista.id_usuario = id_usuario
                db.session.flush()

        if not turista:
            turista = Turista(
                nombres=nombres,
                apellidos=apellidos,
                nro_documento=doc or None,
                procedencia=procedencia,
                email=turista_data.get('email') or None,
                telefono=turista_data.get('telefono') or None,
                id_usuario=id_usuario if rol_nombre == 'turista' else None
            )
            db.session.add(turista)
            db.session.flush()
    else:
        # Fallback si no vinieron datos de modal
        turista = Turista.query.filter_by(id_usuario=id_usuario).first()
        if not turista:
            turista = Turista(
                id_usuario=id_usuario,
                nombres=usuario.nombres if hasattr(usuario, 'nombres') and usuario.nombres else "Turista",
                apellidos=usuario.apellidos if hasattr(usuario, 'apellidos') and usuario.apellidos else "Titular"
            )
            db.session.add(turista)
            db.session.flush()

    # Resolver fechas
    f_inicio_raw = sol.get('fecha_inicio') or generacion.fecha_inicio_viaje
    f_fin_raw = sol.get('fecha_fin') or generacion.fecha_fin_viaje

    f_inicio = datetime.strptime(f_inicio_raw, '%Y-%m-%d').date() if isinstance(f_inicio_raw, str) else f_inicio_raw
    f_fin = datetime.strptime(f_fin_raw, '%Y-%m-%d').date() if isinstance(f_fin_raw, str) else f_fin_raw

    # Parámetros y regla de acompañantes
    parametros_usados = resultados.get('parametros_usados', {})
    num_personas = int(parametros_usados.get('num_personas', 1) or 1)

    # Auditoría de consulta e interacción (Alcance 1.7.1 y Postest de Tesis)
    LIMITE_INACTIVIDAD_SEG = 900.0  # Límite máximo de inactividad: 15 minutos
    t_seg = None
    if tiempo_consulta_seg is not None:
        try:
            t_seg = float(tiempo_consulta_seg)
        except (ValueError, TypeError):
            t_seg = None

    if t_seg is None or t_seg < 0:
        try:
            delta = (datetime.now() - generacion.fecha_generacion).total_seconds()
            t_seg = max(0.0, delta)
        except Exception:
            t_seg = 0.0

    inactividad = bool(t_seg > LIMITE_INACTIVIDAD_SEG)
    minutos = int(t_seg // 60)
    segundos = int(t_seg % 60)
    if inactividad:
        tiempo_texto = f">15 min ({minutos}m {segundos}s)"
    elif minutos > 0:
        tiempo_texto = f"{minutos}m {segundos:02d}s"
    else:
        tiempo_texto = f"{segundos}s"

    num_iter = 1
    if iteraciones_optimizacion is not None:
        try:
            num_iter = max(1, int(iteraciones_optimizacion))
        except (ValueError, TypeError):
            num_iter = 1

    tiempo_computo = None
    if consulta and consulta.tiempo_ejecucion_seg is not None:
        try:
            tiempo_computo = round(float(consulta.tiempo_ejecucion_seg), 3)
        except Exception:
            tiempo_computo = None

    auditoria_data = {
        'tiempo_consulta_seg': round(t_seg, 2),
        'tiempo_consulta_formato': tiempo_texto,
        'tiempo_computo_algoritmo_seg': tiempo_computo,
        'iteraciones_optimizacion': num_iter,
        'inactividad_detectada': inactividad
    }

    # Inyectar auditoría en el snapshot de la solución
    sol['auditoria_consulta'] = auditoria_data

    # Registrar en generacion.observaciones sin sobreescribir texto previo
    try:
        texto_obs = f"[Consulta: {tiempo_texto} | {num_iter} optimización(es)]"
        if generacion.observaciones:
            if "[Consulta:" not in generacion.observaciones:
                generacion.observaciones = f"{generacion.observaciones} | {texto_obs}"
        else:
            generacion.observaciones = texto_obs
    except Exception:
        pass

    # BLOQUE 4: Crear Itinerario con snapshot_json
    nuevo_itinerario = Itinerario(
        id_generacion=id_generacion,
        numero_solucion=int(numero_solucion),
        estado='Borrador',
        afinidad=sol.get('afinidad'),
        costo_total_bob=sol.get('costo_total_bob'),
        costo_entradas_bob=sol.get('costo_entradas_bob'),
        costo_transporte_bob=sol.get('costo_traslados_bob'),
        distancia_total_km=sol.get('distancia_total_km'),
        fecha_inicio=f_inicio,
        fecha_fin=f_fin,
        dias_totales=sol.get('dias_totales', 1),
        num_personas=int(num_personas),
        tiempo_total_estimado=sol.get('tiempo_total_min'),
        es_viable=True,
        snapshot_json=json.dumps(sol, ensure_ascii=False)
    )
    db.session.add(nuevo_itinerario)
    db.session.flush()  # Para obtener el id_itinerario y el UUID generado

    # Crear ViajeTurista enlazando Itinerario y Turista
    viaje_turista = ViajeTurista(
        id_itinerario=nuevo_itinerario.id_itinerario,
        id_turista=turista.id_turista
    )
    db.session.add(viaje_turista)

    # Primer transporte de BD como respaldo de seguridad
    primer_transporte = Transporte.query.filter(Transporte.deleted_at.is_(None)).first()
    id_transporte_default = primer_transporte.id_transporte if primer_transporte else 1

    # Guardar los Detalles
    for parada in sol.get('paradas', []):
        h_lleg_raw = parada.get('hora_llegada')
        h_sal_raw = parada.get('hora_salida')

        h_llegada = None
        h_salida = None
        if h_lleg_raw:
            try:
                h_llegada = datetime.strptime(str(h_lleg_raw).strip()[:5], '%H:%M').time()
            except ValueError:
                pass
        if h_sal_raw:
            try:
                h_salida = datetime.strptime(str(h_sal_raw).strip()[:5], '%H:%M').time()
            except ValueError:
                pass

        clima_data = parada.get('clima') or {}

        # id_transporte real del tramo / parada: NUNCA será NULL
        id_trans = parada.get('id_transporte')
        tiempo_tras = parada.get('tiempo_traslado_desde_anterior')
        if tiempo_tras is None:
            tiempo_tras = parada.get('tiempo_traslado_min')

        if not id_trans:
            for tramo in sol.get('tramos', []):
                if tramo.get('destino_id') == parada['id'] and tramo.get('dia') == parada.get('dia', 1):
                    id_trans = tramo.get('id_transporte')
                    if tiempo_tras is None:
                        tiempo_tras = tramo.get('tiempo_traslado_min')
                    break

        if not id_trans:
            for tramo in sol.get('tramos', []):
                if tramo.get('id_transporte'):
                    id_trans = tramo.get('id_transporte')
                    break

        if not id_trans:
            id_trans = id_transporte_default

        if tiempo_tras is None or tiempo_tras == 0:
            tiempo_tras = 15 if parada.get('numero', 1) == 1 else 10
        else:
            try:
                tiempo_tras = max(1, int(round(float(tiempo_tras))))
            except (ValueError, TypeError):
                tiempo_tras = 15 if parada.get('numero', 1) == 1 else 10

        detalle = ItinerarioDetalle(
            id_itinerario=nuevo_itinerario.id_itinerario,
            id_atractivo=parada['id'],
            id_transporte=id_trans,
            dia=parada['dia'],
            orden=parada.get('numero', 1),
            hora_llegada_estimada=h_llegada,
            hora_salida_estimada=h_salida,
            tiempo_traslado_desde_anterior=int(tiempo_tras),
            costo_entrada_bob=parada.get('costo_entrada_bob'),
            clima_temperatura=clima_data.get('temperatura'),
            clima_lluvia_mm=clima_data.get('precipitacion_mm'),
            clima_descripcion=clima_data.get('descripcion')
        )
        db.session.add(detalle)
        db.session.flush()

        # Guardar Tráfico (si hay avisos en la parada)
        for aviso in parada.get('avisos_trafico', []):
            id_patron = aviso.get('id_patron')
            if id_patron:
                try:
                    trafico = ItinerarioDetalleTrafico(
                        id_detalle=detalle.id_detalle,
                        id_patron=int(id_patron)
                    )
                    db.session.add(trafico)
                except Exception:
                    pass

    # Regla de Acompañantes: Si num_personas > 1
    advertencia_acompanantes = None
    if num_personas > 1:
        faltantes = num_personas - 1
        advertencia_acompanantes = f"Faltan {faltantes} acompañantes por registrar. El itinerario no podrá cambiar de estado hasta que se completen."

    db.session.commit()

    return {
        "id_itinerario": nuevo_itinerario.id_itinerario,
        "success": True,
        "codigo_confirmacion": str(nuevo_itinerario.codigo_confirmacion),
        "advertencia_acompanantes": advertencia_acompanantes,
        "num_personas": int(num_personas),
        "auditoria_consulta": auditoria_data
    }


def listar_itinerarios_guardados(usuario_actual):
    """
    Lista los itinerarios guardados con separación estricta de roles:
    - Admin y Agente ven todos los itinerarios no eliminados.
    - Turista ve únicamente los que le pertenecen a través de ViajeTurista -> Turista
      o a través de su generacion.id_usuario.
    """
    rol_nombre = (usuario_actual.rol.nombre if usuario_actual.rol else '').lower()
    if rol_nombre in ['admin', 'agente']:
        return Itinerario.query.filter(
            Itinerario.deleted_at.is_(None)
        ).order_by(Itinerario.id_itinerario.desc()).all()
    else:
        return Itinerario.query.outerjoin(
            ViajeTurista, Itinerario.id_itinerario == ViajeTurista.id_itinerario
        ).outerjoin(
            Turista, ViajeTurista.id_turista == Turista.id_turista
        ).outerjoin(
            Generacion, Itinerario.id_generacion == Generacion.id_generacion
        ).filter(
            Itinerario.deleted_at.is_(None),
            db.or_(
                Turista.id_usuario == usuario_actual.id_usuario,
                Generacion.id_usuario == usuario_actual.id_usuario
            )
        ).distinct().order_by(Itinerario.id_itinerario.desc()).all()


def obtener_detalle_itinerario(id_itinerario: int) -> dict | None:
    """
    Reconstruye el JSON completo de un itinerario guardado para mostrarlo con el mismo
    nivel de detalle (mapas, timeline, clima, transportes) que en el generador.
    Prioriza el snapshot_json guardado en la columna de Itinerario.
    """
    itinerario = Itinerario.query.get(id_itinerario)
    if not itinerario or itinerario.is_deleted:
        return None

    def _adjuntar_turista(s_dict):
        if itinerario.viajes_turistas and len(itinerario.viajes_turistas) > 0:
            t = itinerario.viajes_turistas[0].turista
            if t:
                s_dict['turista_contacto'] = {
                    'nombres': t.nombres,
                    'apellidos': t.apellidos,
                    'nro_documento': t.nro_documento,
                    'procedencia': t.procedencia,
                    'email': t.email,
                    'telefono': t.telefono
                }
        return s_dict

    # 1. Prioridad: cargar directamente desde snapshot_json
    if itinerario.snapshot_json:
        try:
            sol_dict = json.loads(itinerario.snapshot_json)
            if isinstance(sol_dict, dict):
                sol_dict['id_itinerario'] = itinerario.id_itinerario
                sol_dict['id_generacion'] = itinerario.id_generacion
                sol_dict['estado'] = itinerario.estado
                sol_dict['codigo_confirmacion'] = str(itinerario.codigo_confirmacion) if itinerario.codigo_confirmacion else None
                sol_dict['voucher_generado'] = itinerario.voucher_generado
                sol_dict['num_personas'] = int(itinerario.num_personas or 1)
                return _adjuntar_turista(sol_dict)
        except Exception as e:
            print(f"[WARNING] Error cargando snapshot_json de itinerario #{id_itinerario}: {e}")

    # 2. Intentar cargar desde el JSON en ConsultaNSGA2
    consulta = ConsultaNSGA2.query.filter_by(id_generacion=itinerario.id_generacion).first()
    if consulta and consulta.resultados_json:
        try:
            resultados = json.loads(consulta.resultados_json)
            soluciones = resultados.get('soluciones_viables', []) + resultados.get('soluciones_no_viables', [])
            if not soluciones:
                soluciones = resultados.get('soluciones', [])

            sol = next((s for s in soluciones if s.get('numero') == itinerario.numero_solucion or s.get('numero_solucion') == itinerario.numero_solucion), None)
            if not sol and 0 < itinerario.numero_solucion <= len(soluciones):
                sol = soluciones[itinerario.numero_solucion - 1]

            if sol:
                sol_dict = dict(sol)
                sol_dict['id_itinerario'] = itinerario.id_itinerario
                sol_dict['id_generacion'] = itinerario.id_generacion
                sol_dict['estado'] = itinerario.estado
                sol_dict['codigo_confirmacion'] = str(itinerario.codigo_confirmacion) if itinerario.codigo_confirmacion else None
                sol_dict['voucher_generado'] = itinerario.voucher_generado
                sol_dict['num_personas'] = int(itinerario.num_personas or 1)
                return _adjuntar_turista(sol_dict)
        except Exception as e:
            print(f"[WARNING] Error cargando JSON de itinerario desde ConsultaNSGA2: {e}")

    # 3. Reconstrucción manual desde las tablas de la BD si no existe o falló el JSON
    detalles = ItinerarioDetalle.query.filter_by(
        id_itinerario=id_itinerario
    ).order_by(ItinerarioDetalle.dia, ItinerarioDetalle.orden).all()

    paradas = []
    atractivos_nombres = []
    for d in detalles:
        atr = d.atractivo
        nombre_atr = atr.nombre if atr else f"Atractivo #{d.id_atractivo}"
        atractivos_nombres.append(nombre_atr)
        paradas.append({
            "numero": d.orden,
            "dia": d.dia,
            "id": d.id_atractivo,
            "nombre": nombre_atr,
            "lat": float(atr.latitud) if atr and atr.latitud is not None else 0.0,
            "lon": float(atr.longitud) if atr and atr.longitud is not None else 0.0,
            "categoria": atr.categoria.nombre if atr and atr.categoria else "General",
            "subcategoria": atr.subcategoria.nombre if atr and atr.subcategoria else "General",
            "costo_entrada_bob": float(d.costo_entrada_bob or 0.0),
            "hora_llegada": d.hora_llegada_estimada.strftime("%H:%M") if d.hora_llegada_estimada else "09:00",
            "hora_salida": d.hora_salida_estimada.strftime("%H:%M") if d.hora_salida_estimada else "10:00",
            "tiempo_visita_min": int((d.hora_salida_estimada.hour * 60 + d.hora_salida_estimada.minute) - (d.hora_llegada_estimada.hour * 60 + d.hora_llegada_estimada.minute)) if (d.hora_salida_estimada and d.hora_llegada_estimada) else 60,
            "id_transporte": d.id_transporte,
            "tiempo_traslado_desde_anterior": int(d.tiempo_traslado_desde_anterior or 15),
            "clima": {
                "temperatura": float(d.clima_temperatura) if d.clima_temperatura is not None else None,
                "precipitacion_mm": float(d.clima_lluvia_mm) if d.clima_lluvia_mm is not None else None,
                "descripcion": d.clima_descripcion,
                "icono": "bi-cloud-sun",
                "estado": "bueno"
            } if (d.clima_temperatura is not None or d.clima_descripcion) else None
        })

    return {
        "id_itinerario": itinerario.id_itinerario,
        "id_generacion": itinerario.id_generacion,
        "numero_solucion": itinerario.numero_solucion,
        "estado": itinerario.estado,
        "afinidad": float(itinerario.afinidad or 0.0),
        "costo_total_bob": float(itinerario.costo_total_bob or 0.0),
        "costo_entradas_bob": float(itinerario.costo_entradas_bob or 0.0),
        "costo_traslados_bob": float(itinerario.costo_transporte_bob or 0.0),
        "distancia_total_km": float(itinerario.distancia_total_km or 0.0),
        "tiempo_total_min": float(itinerario.tiempo_total_estimado or 0.0),
        "fecha_inicio": itinerario.fecha_inicio.strftime("%Y-%m-%d") if itinerario.fecha_inicio else "",
        "fecha_fin": itinerario.fecha_fin.strftime("%Y-%m-%d") if itinerario.fecha_fin else "",
        "dias_totales": itinerario.dias_totales or 1,
        "num_personas": int(itinerario.num_personas or 1),
        "cumple_restricciones": itinerario.es_viable,
        "num_atractivos": len(paradas),
        "atractivos_nombres": atractivos_nombres,
        "paradas": paradas,
        "tramos": [],
        "clima_por_dia": {},
        "avisos_trafico": [],
        "transporte_asignado": {"nombre": "Vehículo / Estándar", "es_mixto": False},
        "codigo_confirmacion": str(itinerario.codigo_confirmacion) if itinerario.codigo_confirmacion else None,
        "voucher_generado": itinerario.voucher_generado
    }


def obtener_titular(id_itinerario: int) -> Turista | None:
    """Retorna el turista titular del itinerario (el de menor id_viaje_turista)."""
    return Turista.query.join(
        ViajeTurista, ViajeTurista.id_turista == Turista.id_turista
    ).filter(
        ViajeTurista.id_itinerario == id_itinerario
    ).order_by(ViajeTurista.id_viaje_turista.asc()).first()


def contar_turistas_itinerario(id_itinerario: int) -> int:
    """Cuenta el número de turistas vinculados a un itinerario."""
    return ViajeTurista.query.filter_by(id_itinerario=id_itinerario).count()


def calcular_faltantes(id_itinerario: int) -> dict:
    """Calcula cuántos turistas faltan por registrar según el num_personas declarado."""
    itin = Itinerario.query.get(id_itinerario)
    if not itin:
        raise ValueError("Itinerario no encontrado.")
    total = contar_turistas_itinerario(id_itinerario)
    esperado = int(itin.num_personas or 1)
    return {
        "total_registrados": total,
        "esperado": esperado,
        "faltantes": max(0, esperado - total),
        "completo": total >= esperado,
    }


def listar_turistas_itinerario(id_itinerario: int) -> list[dict]:
    """Lista todos los turistas vinculados (titular primero, luego acompañantes)."""
    itin = Itinerario.query.get(id_itinerario)
    if not itin:
        raise ValueError("Itinerario no encontrado.")

    viajes = ViajeTurista.query.filter_by(
        id_itinerario=id_itinerario
    ).order_by(ViajeTurista.id_viaje_turista.asc()).all()

    lista = []
    for idx, vt in enumerate(viajes):
        t = vt.turista
        if not t:
            continue
        lista.append({
            "id_turista": t.id_turista,
            "nombres": t.nombres,
            "apellidos": t.apellidos,
            "nro_documento": t.nro_documento,
            "procedencia": t.procedencia,
            "email": t.email,
            "telefono": t.telefono,
            "rol": "titular" if idx == 0 else "acompanante",
            "id_viaje_turista": vt.id_viaje_turista,
        })
    return lista


def agregar_acompanante(
    id_itinerario: int,
    datos: dict,
    id_usuario_actual: int | None = None
) -> dict:
    """
    Registra un acompañante a un itinerario en estado Borrador respetando el cupo num_personas.
    """
    # 7.1. Validar que el itinerario existe
    itinerario = Itinerario.query.get(id_itinerario)
    if not itinerario:
        raise ValueError("Itinerario no encontrado.")

    # 7.2. Validar que no está eliminado
    if itinerario.is_deleted:
        raise ValueError("El itinerario no está disponible.")

    # 7.3. Validar estado Borrador
    if itinerario.estado != 'Borrador':
        raise ValueError("Solo se pueden añadir acompañantes a itinerarios en estado Borrador.")

    # 7.4. Validar espacio
    conteo = contar_turistas_itinerario(id_itinerario)
    esperado = int(itinerario.num_personas or 1)
    if conteo >= esperado:
        raise ValueError(f"El itinerario ya tiene registradas {conteo} personas (máximo {itinerario.num_personas}). No se pueden añadir más.")

    # 7.5. Validar datos de entrada
    nombres = str(datos.get('nombres') or '').strip()
    apellidos = str(datos.get('apellidos') or '').strip()
    procedencia = str(datos.get('procedencia') or '').strip()
    doc = str(datos.get('nro_documento') or '').strip() or None
    email = str(datos.get('email') or '').strip() or None
    telefono = str(datos.get('telefono') or '').strip() or None

    if not nombres or not apellidos:
        raise ValueError("Nombres y apellidos son obligatorios.")
    if not procedencia:
        raise ValueError("La procedencia es obligatoria.")
    if any(c.isdigit() for c in nombres + apellidos):
        raise ValueError("Los nombres y apellidos no pueden contener números.")
    if doc:
        valido_doc, doc_formateado, err_doc = validar_documento_por_procedencia(doc, procedencia)
        if not valido_doc:
            raise ValueError(err_doc)
        doc = doc_formateado

    # 7.6. Resolver el Turista
    if doc:
        resultado_busqueda = buscar_turista(doc, procedencia)
        if resultado_busqueda.get("motivo") == "conflicto_procedencia":
            raise ValueError(
                f"El documento {doc} ya está registrado con procedencia "
                f"'{resultado_busqueda.get('procedencia_registrada')}'. "
                f"Verifica el país o usa otro documento."
            )
        if resultado_busqueda.get("encontrado"):
            turista = Turista.query.get(resultado_busqueda["turista"]["id_turista"])
        else:
            turista = Turista(
                nombres=nombres,
                apellidos=apellidos,
                nro_documento=doc,
                procedencia=procedencia,
                email=email,
                telefono=telefono,
                id_usuario=None  # los acompañantes no se ligan a Usuario
            )
            db.session.add(turista)
            db.session.flush()
    else:
        turista = Turista(
            nombres=nombres,
            apellidos=apellidos,
            nro_documento=None,
            procedencia=procedencia,
            email=email,
            telefono=telefono,
            id_usuario=None
        )
        db.session.add(turista)
        db.session.flush()

    # 7.7. Validar que el turista no esté ya en este itinerario
    existe = ViajeTurista.query.filter_by(
        id_itinerario=id_itinerario,
        id_turista=turista.id_turista
    ).first()
    if existe:
        raise ValueError("Esta persona ya está registrada en este itinerario.")

    # 7.8. Crear ViajeTurista
    nuevo_viaje = ViajeTurista(
        id_itinerario=id_itinerario,
        id_turista=turista.id_turista
    )
    db.session.add(nuevo_viaje)

    # TODO: cuando se implemente el cambio de estado a 'Confirmado',
    # validar calcular_faltantes(id_itinerario).get("completo") == True antes de permitirlo.

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Error al guardar acompañante: {str(e)}")

    # 7.9. Retornar resumen actualizado
    datos_finales = calcular_faltantes(id_itinerario)
    return {
        "success": True,
        "turista": {
            "id_turista": turista.id_turista,
            "nombres": turista.nombres,
            "apellidos": turista.apellidos,
            "nro_documento": turista.nro_documento,
            "procedencia": turista.procedencia,
            "email": turista.email,
            "telefono": turista.telefono,
        },
        "total_registrados": datos_finales["total_registrados"],
        "esperado": datos_finales["esperado"],
        "faltantes": datos_finales["faltantes"],
        "completo": datos_finales["completo"],
    }


def cambiar_estado_itinerario(id_itinerario: int, nuevo_estado: str, usuario_actual) -> dict:
    """
    Permite a Administradores y Agentes cambiar el estado de un itinerario.
    Estados válidos: 'Borrador', 'Confirmado', 'En curso', 'Completado', 'Cancelado'.
    
    Regla de negocio estricta:
    Para pasar a 'Confirmado', es OBLIGATORIO que todos los turistas acompañantes
    estén registrados (calcular_faltantes(id_itinerario).get("completo") == True).
    """
    rol_nombre = getattr(usuario_actual.rol, 'nombre', '') if getattr(usuario_actual, 'rol', None) else ''
    if rol_nombre not in ['admin', 'agente']:
        raise ValueError("No tienes permisos de Administrador o Agente para cambiar el estado de este itinerario.")

    itinerario = Itinerario.query.get(id_itinerario)
    if not itinerario or itinerario.is_deleted:
        raise ValueError("Itinerario no encontrado.")

    estados_validos = ['Borrador', 'Confirmado', 'En curso', 'Completado', 'Cancelado']
    if nuevo_estado not in estados_validos:
        raise ValueError(f"Estado '{nuevo_estado}' no válido. Opciones: {', '.join(estados_validos)}")

    estado_actual = itinerario.estado or 'Borrador'

    if estado_actual == nuevo_estado:
        return {
            "success": True,
            "id_itinerario": itinerario.id_itinerario,
            "estado": itinerario.estado,
            "codigo_confirmacion": str(itinerario.codigo_confirmacion) if itinerario.codigo_confirmacion else None,
            "voucher_generado": itinerario.voucher_generado,
            "mensaje": f"El itinerario ya se encuentra en estado '{nuevo_estado}'."
        }

    # Transiciones secuenciales permitidas en el ciclo de vida del itinerario:
    # Borrador   -> Confirmado (requiere acompañantes completos), Cancelado
    # Confirmado -> En curso, Cancelado
    # En curso   -> Completado, Cancelado
    # Completado -> (Terminal, no se puede cambiar)
    # Cancelado  -> (Terminal, no se puede cambiar)
    transiciones_permitidas = {
        'Borrador': ['Confirmado', 'Cancelado'],
        'Confirmado': ['En curso', 'Cancelado'],
        'En curso': ['Completado', 'Cancelado'],
        'Completado': [],
        'Cancelado': []
    }

    permitidos = transiciones_permitidas.get(estado_actual, [])
    if nuevo_estado not in permitidos:
        if not permitidos:
            raise ValueError(f"No se puede cambiar el estado de un itinerario '{estado_actual}', es un estado final cerrado.")
        raise ValueError(
            f"Transición de estado no permitida: no se puede pasar directamente de '{estado_actual}' a '{nuevo_estado}'. "
            f"Transiciones válidas desde '{estado_actual}': {', '.join(permitidos)}."
        )

    # Validar grupo completo antes de confirmar
    if nuevo_estado == 'Confirmado':
        conteo = calcular_faltantes(id_itinerario)
        if not conteo.get("completo"):
            faltantes = conteo.get("faltantes", 1)
            esperado = conteo.get("esperado", 1)
            registrados = conteo.get("total_registrados", 0)
            raise ValueError(
                f"No se puede confirmar el itinerario. Faltan {faltantes} turista(s) por registrar "
                f"({registrados} de {esperado} registrados). Registra a todos los acompañantes primero."
            )

        if not itinerario.codigo_confirmacion:
            itinerario.codigo_confirmacion = uuid.uuid4()
        itinerario.voucher_generado = True

        # Intentar enviar notificación de cortesía
        try:
            from app.services.email_service import enviar_itinerario_confirmado
            if itinerario.generacion and itinerario.generacion.usuario and itinerario.generacion.usuario.email:
                enviar_itinerario_confirmado(itinerario.generacion.usuario, itinerario)
        except Exception as ex_mail:
            print(f"[WARNING] No se pudo enviar correo de confirmación: {ex_mail}")

    itinerario.estado = nuevo_estado
    db.session.commit()

    return {
        "success": True,
        "id_itinerario": itinerario.id_itinerario,
        "estado": itinerario.estado,
        "codigo_confirmacion": str(itinerario.codigo_confirmacion) if itinerario.codigo_confirmacion else None,
        "voucher_generado": itinerario.voucher_generado,
        "mensaje": f"Estado del itinerario #{itinerario.id_itinerario} actualizado a '{nuevo_estado}' exitosamente."
    }


def generar_voucher_pdf(id_itinerario: int) -> bytes:
    """
    Genera en memoria el documento PDF oficial del Comprobante / Voucher de Itinerario
    con código QR embebido generado con qrcode y PIL para verificación rápida.
    """
    itinerario = Itinerario.query.get(id_itinerario)
    if not itinerario or itinerario.is_deleted:
        raise ValueError(f"Itinerario #{id_itinerario} no encontrado.")

    # Generar código de confirmación si no lo tiene
    if not itinerario.codigo_confirmacion:
        itinerario.codigo_confirmacion = uuid.uuid4()
        db.session.commit()

    turistas = listar_turistas_itinerario(id_itinerario)
    detalles = ItinerarioDetalle.query.filter_by(
        id_itinerario=id_itinerario
    ).order_by(ItinerarioDetalle.dia, ItinerarioDetalle.orden).all()

    turista_titular = turistas[0] if turistas else None
    nombre_titular = f"{turista_titular['nombres']} {turista_titular['apellidos']}" if turista_titular else "Cliente General"
    
    # Formateo profesional de documento según procedencia
    if turista_titular and turista_titular.get('nro_documento'):
        proc_tit = (turista_titular.get('procedencia') or '').strip().lower()
        if 'bolivia' in proc_tit or proc_tit == 'bo':
            doc_titular = f"C.I. {turista_titular['nro_documento']} (Bolivia)"
        else:
            doc_titular = f"Pasaporte {turista_titular['nro_documento']} ({turista_titular.get('procedencia') or 'Extranjero'})"
    else:
        doc_titular = "S/D"

    # Generar Código QR
    tc = 6.96
    c_bob = float(itinerario.costo_total_bob or 0.0)
    c_usd = round(c_bob / tc, 2)
    f_ini = itinerario.fecha_inicio.strftime('%d/%m/%Y') if itinerario.fecha_inicio else "Por definir"
    f_fin = itinerario.fecha_fin.strftime('%d/%m/%Y') if itinerario.fecha_fin else "Por definir"

    qr_payload = (
        f"BUHOS TOURS - VOUCHER OFICIAL\n"
        f"Itinerario: #{itinerario.id_itinerario}\n"
        f"Confirmacion: {itinerario.codigo_confirmacion}\n"
        f"Titular: {nombre_titular} (Doc: {doc_titular})\n"
        f"Fechas: {f_ini} al {f_fin}\n"
        f"Grupo: {itinerario.num_personas} personas\n"
        f"Total: Bs. {c_bob:.2f} (~${c_usd:.2f} USD)\n"
        f"Estado: {itinerario.estado}"
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=2,
    )
    qr.add_data(qr_payload)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0f172a", back_color="white")
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    # Configuración del documento PDF
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        'VoucherTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0369a1'),
        spaceAfter=2,
    )
    style_subtitle = ParagraphStyle(
        'VoucherSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=4,
    )
    style_voucher_header = ParagraphStyle(
        'VoucherHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#0f172a'),
    )
    style_section = ParagraphStyle(
        'VoucherSection',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0369a1'),
        spaceBefore=8,
        spaceAfter=4,
    )
    style_cell = ParagraphStyle(
        'VoucherCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#1e293b'),
    )
    style_cell_header = ParagraphStyle(
        'VoucherCellHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
    )
    style_cell_center = ParagraphStyle(
        'VoucherCellCenter',
        parent=style_cell,
        alignment=1,
    )
    style_notes = ParagraphStyle(
        'VoucherNotes',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#475569'),
    )

    story = []

    # 1. Cabecera y Marca
    header_left = [
        Paragraph("BUHOS TOURS", style_title),
        Paragraph("OPERADORA DE TURISMO &amp; SERVICIOS DE VIAJE", style_subtitle),
        Paragraph("COMPROBANTE DE COTIZACIÓN Y VOUCHER DE ITINERARIO", style_voucher_header),
    ]

    badge_color = "#16a34a" if itinerario.estado == "Confirmado" else ("#d97706" if itinerario.estado == "Borrador" else "#2563eb")
    header_right = [
        Paragraph(f"<font color='{badge_color}'><b>ESTADO: {itinerario.estado.upper()}</b></font>", style_voucher_header),
        Paragraph(f"Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}", style_subtitle),
        Paragraph(f"Código: <font face='Courier'><b>{str(itinerario.codigo_confirmacion)[:18]}...</b></font>", style_notes),
    ]

    header_table = Table([[header_left, header_right]], colWidths=[360, 180])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))

    # 2. Resumen General y Código QR
    resumen_datos = [
        [
            Paragraph("<b>Identificador de Itinerario:</b>", style_cell),
            Paragraph(f"#ITIN-{itinerario.id_itinerario:04d}", style_cell),
        ],
        [
            Paragraph("<b>Código de Confirmación (UUID):</b>", style_cell),
            Paragraph(f"<font face='Courier'>{itinerario.codigo_confirmacion}</font>", style_cell),
        ],
        [
            Paragraph("<b>Turista Titular:</b>", style_cell),
            Paragraph(f"{nombre_titular} (Doc: {doc_titular})", style_cell),
        ],
        [
            Paragraph("<b>Fechas del Viaje:</b>", style_cell),
            Paragraph(f"{f_ini} al {f_fin} ({itinerario.dias_totales or 1} días programados)", style_cell),
        ],
        [
            Paragraph("<b>Cantidad de Pasajeros:</b>", style_cell),
            Paragraph(f"{itinerario.num_personas} persona(s) registradas", style_cell),
        ],
        [
            Paragraph("<b>Costo Total Estimado:</b>", style_cell),
            Paragraph(f"<b>Bs. {c_bob:.2f}</b> (~ ${c_usd:.2f} USD, T.C. Oficial {tc})", style_cell),
        ],
    ]
    tabla_resumen_datos = Table(resumen_datos, colWidths=[150, 240])
    tabla_resumen_datos.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
    ]))

    qr_image = RLImage(qr_buffer, width=95, height=95)
    qr_block = [
        qr_image,
        Spacer(1, 2),
        Paragraph("<font size='6' color='#64748b'>Escanear para validación en agencia</font>", style_cell_center),
    ]

    bloque_superior = Table([[tabla_resumen_datos, qr_block]], colWidths=[400, 140])
    bloque_superior.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('LEFTPADDING', (1, 0), (1, 0), 10),
    ]))
    story.append(bloque_superior)
    story.append(Spacer(1, 8))

    # 3. Nómina de Turistas
    story.append(Paragraph("1. NÓMINA DE PASAJEROS / TURISTAS REGISTRADOS", style_section))
    filas_turistas = [
        [
            Paragraph("Tipo", style_cell_header),
            Paragraph("Nombres y Apellidos", style_cell_header),
            Paragraph("Documento", style_cell_header),
            Paragraph("Procedencia", style_cell_header),
            Paragraph("Contacto (Email / Teléfono)", style_cell_header),
        ]
    ]

    for t_item in turistas:
        tipo_lbl = "Titular" if t_item.get("rol") == "titular" else "Acompañante"
        tipo_str = f"<b>{tipo_lbl}</b>"
        nombre_str = f"{t_item.get('nombres', '')} {t_item.get('apellidos', '')}"
        
        proc_t = (t_item.get("procedencia") or "").strip()
        doc_raw = t_item.get("nro_documento")
        if doc_raw:
            if 'bolivia' in proc_t.lower() or proc_t.lower() == 'bo':
                doc_str = f"<b>C.I.</b> {doc_raw}"
            else:
                doc_str = f"<b>Pasaporte:</b> {doc_raw}"
        else:
            doc_str = "S/D"

        proc_str = proc_t or "No especificada"
        contacto_parts = []
        if t_item.get("email"):
            contacto_parts.append(t_item["email"])
        if t_item.get("telefono"):
            contacto_parts.append(t_item["telefono"])
        contacto_str = " · ".join(contacto_parts) if contacto_parts else "S/D"

        filas_turistas.append([
            Paragraph(tipo_str, style_cell),
            Paragraph(nombre_str, style_cell),
            Paragraph(doc_str, style_cell),
            Paragraph(proc_str, style_cell),
            Paragraph(contacto_str, style_cell),
        ])

    tabla_turistas = Table(filas_turistas, colWidths=[70, 140, 80, 100, 150])
    tabla_turistas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0369a1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))
    story.append(tabla_turistas)
    story.append(Spacer(1, 8))

    # 4. Cronograma Detallado
    story.append(Paragraph("2. CRONOGRAMA DETALLADO Y TRANSPORTE", style_section))
    filas_paradas = [
        [
            Paragraph("Día", style_cell_header),
            Paragraph("N°", style_cell_header),
            Paragraph("Atractivo Turístico", style_cell_header),
            Paragraph("Llegada", style_cell_header),
            Paragraph("Salida", style_cell_header),
            Paragraph("Visita", style_cell_header),
            Paragraph("Traslado", style_cell_header),
            Paragraph("Transporte Asignado", style_cell_header),
        ]
    ]

    for d in detalles:
        atr = d.atractivo
        nom_atr = atr.nombre if atr else f"Atractivo #{d.id_atractivo}"
        h_lleg = d.hora_llegada_estimada.strftime("%H:%M") if d.hora_llegada_estimada else "--:--"
        h_sal = d.hora_salida_estimada.strftime("%H:%M") if d.hora_salida_estimada else "--:--"

        t_vis = 60
        if d.hora_salida_estimada and d.hora_llegada_estimada:
            t_vis = (d.hora_salida_estimada.hour * 60 + d.hora_salida_estimada.minute) - (d.hora_llegada_estimada.hour * 60 + d.hora_llegada_estimada.minute)
            t_vis = max(1, t_vis)

        try:
            t_tras = int(d.tiempo_traslado_desde_anterior or 0)
        except (TypeError, ValueError):
            t_tras = 0
        nom_trans = d.transporte.nombre if (d.transporte and d.transporte.nombre) else "Vehículo"

        filas_paradas.append([
            Paragraph(f"Día {d.dia}", style_cell_center),
            Paragraph(str(d.orden), style_cell_center),
            Paragraph(nom_atr, style_cell),
            Paragraph(h_lleg, style_cell_center),
            Paragraph(h_sal, style_cell_center),
            Paragraph(f"{t_vis} min", style_cell_center),
            Paragraph(f"{t_tras} min" if t_tras > 0 else "Inicio", style_cell_center),
            Paragraph(nom_trans, style_cell),
        ])

    tabla_paradas = Table(filas_paradas, colWidths=[38, 22, 160, 45, 45, 40, 45, 145])
    tabla_paradas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0369a1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))
    story.append(tabla_paradas)
    story.append(Spacer(1, 8))

    # 5. Resumen Económico y Términos
    c_ent = float(itinerario.costo_entradas_bob or 0.0)
    c_trans = float(itinerario.costo_transporte_bob or 0.0)
    filas_costos = [
        [
            Paragraph("<b>Concepto</b>", style_cell_header),
            Paragraph("<b>Importe (BOB)</b>", style_cell_header),
        ],
        [
            Paragraph("Entradas a Atractivos Turísticos", style_cell),
            Paragraph(f"Bs. {c_ent:.2f}", style_cell),
        ],
        [
            Paragraph("Servicio de Transporte y Traslados", style_cell),
            Paragraph(f"Bs. {c_trans:.2f}", style_cell),
        ],
        [
            Paragraph("<b>TOTAL COTIZADO:</b>", style_cell),
            Paragraph(f"<b>Bs. {c_bob:.2f}</b> (~ ${c_usd:.2f} USD)", style_cell),
        ],
    ]
    tabla_costos = Table(filas_costos, colWidths=[380, 160])
    tabla_costos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0f2fe')),
    ]))

    story.append(KeepTogether([
        Paragraph("3. RESUMEN ECONÓMICO ESTIMADO", style_section),
        tabla_costos,
        Spacer(1, 8),
        Paragraph(
            "<b>NOTAS Y TÉRMINOS OPERATIVOS:</b><br/>"
            "1. Este voucher certifica la planificación y cotización formal generada a través de la plataforma de Buhos Tours.<br/>"
            "2. Para la confirmación de salidas, pago final y asignación de guía certificado, presente este documento con su código QR en nuestras oficinas o contáctese con su agente asignado.<br/>"
            "3. Los horarios y traslados han sido optimizados considerando factores de congestión vehicular y tiempos de visita reglamentarios.<br/>"
            "<b>Buhos Tours</b> · Av. 16 de Julio (El Prado), Edif. Cosmos · La Paz, Bolivia · Tel: +591 2 2444444 · info@buhostours.com",
            style_notes
        )
    ]))

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
