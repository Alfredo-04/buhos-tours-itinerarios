from typing import Any
from datetime import datetime, timedelta
import hashlib
import json
from app.models.atractivo import Atractivo
from app.models.subcategoria import Subcategoria
from app.models.transporte import Transporte
from app.models.categoria import Categoria
from app.models.generacion import Generacion
from app.models.consulta_nsga2 import ConsultaNSGA2
from app.models.itinerario import Itinerario
from app.models.itinerario_detalle import ItinerarioDetalle
from app.models.itinerario_detalle_trafico import ItinerarioDetalleTrafico
from app.services.nsga2_service import ejecutar_nsga2
from app import db


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
    fecha_hoy = datetime.utcnow().date()

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

    # 2. LÓGICA DE CACHÉ Y RATE LIMITING
    if id_usuario:
        # a) Buscar si este usuario ya hizo esta consulta y tiene resultados guardados en caché
        consulta_existente = db.session.query(ConsultaNSGA2).join(
            Generacion, ConsultaNSGA2.id_generacion == Generacion.id_generacion
        ).filter(
            Generacion.id_usuario == id_usuario,
            ConsultaNSGA2.hash_parametros == hash_actual
        ).order_by(ConsultaNSGA2.fecha.desc()).first()

        # Lógica de Caché con Expiración (24 horas)
        if consulta_existente and consulta_existente.resultados_json:
            fecha_consulta = consulta_existente.fecha
            ahora = datetime.utcnow()
            if hasattr(fecha_consulta, 'tzinfo') and fecha_consulta.tzinfo is not None:
                from datetime import timezone
                ahora = datetime.now(timezone.utc)

            tiempo_transcurrido = ahora - fecha_consulta

            # Si pasaron menos de 24 horas, usamos la caché
            if tiempo_transcurrido.total_seconds() < 86400:
                print("[CACHE HIT] Devolviendo resultados guardados sin ejecutar NSGA-II.")
                try:
                    resultados_cacheados = json.loads(consulta_existente.resultados_json)
                    if isinstance(resultados_cacheados, dict):
                        resultados_cacheados['id_generacion'] = consulta_existente.id_generacion
                    return resultados_cacheados
                except Exception as ex_json:
                    print(f"[CACHE ERROR] No se pudo deserializar resultados_json ({ex_json}), ejecutando NSGA-II...")
            else:
                print("[CACHE EXPIRADO] La consulta tiene más de 24h. Recalculando itinerario...")

        # b) Rate Limiting (esperar 3 segundos entre consultas consecutivas cuando es consulta nueva)
        ultima_gen = Generacion.query.filter_by(id_usuario=id_usuario).order_by(Generacion.fecha_generacion.desc()).first()

        if ultima_gen and ultima_gen.fecha_generacion:
            ahora = datetime.utcnow()
            fecha_gen = ultima_gen.fecha_generacion
            if hasattr(fecha_gen, 'tzinfo') and fecha_gen.tzinfo is not None:
                from datetime import timezone
                ahora = datetime.now(timezone.utc)

            segundos_desde_ultima = (ahora - fecha_gen).total_seconds()
            if segundos_desde_ultima < 3:
                raise ValueError("Por favor, espera unos segundos antes de volver a generar.")

    print("[CACHE MISS] Ejecutando NSGA-II (esto tomará unos segundos)...")

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
                    fecha_ini_date = datetime.utcnow().date() + timedelta(days=1)
            elif hasattr(fecha_ini_str, 'year'):
                fecha_ini_date = fecha_ini_str
            else:
                fecha_ini_date = datetime.utcnow().date() + timedelta(days=1)

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

            nueva_consulta = ConsultaNSGA2(
                id_generacion=nueva_generacion.id_generacion,  # Relación FK
                num_atractivos=len(atractivos_ids) if atractivos_ids else len(atractivos_data),
                num_transportes=len(transporte_ids) if transporte_ids else len(transportes_data),
                presupuesto=presupuesto_max,
                tiempo_disponible_horas=tiempo_disp,
                intereses=json.dumps(intereses, ensure_ascii=False) if intereses else None,
                tamano_poblacion=tamano_poblacion,
                generaciones=generaciones,
                prob_cruce=prob_cruce,
                prob_mutacion=prob_mutacion,
                num_soluciones=num_sols,
                mejor_afinidad=mejor_afinidad,
                mejor_tiempo=mejor_tiempo,
                soluciones_viables=resultado.get('total_soluciones_viables', len(resultado.get('soluciones_viables', []))),
                todas_exceden=not bool(resultado.get('hay_viables', False)),
                tiempo_ejecucion_seg=resultado.get('tiempo_ejecucion_seg', 0.0),
                convergencia=convergencia_val,
                diversidad_final=diversidad_val,
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
                hash_parametros=hash_actual,  # Guardar hash para deduplicar a futuro
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


def guardar_itinerario(id_generacion: int, numero_solucion: int, id_usuario: int) -> dict:
    """
    Toma una solución del JSON de caché y la guarda en las tablas definitivas de itinerario.
    """
    # 1. Buscar la generación y su consulta (caché JSON)
    generacion = Generacion.query.get(id_generacion)
    if not generacion:
        raise ValueError("Generación no encontrada.")

    consulta = ConsultaNSGA2.query.filter_by(id_generacion=id_generacion).first()
    if not consulta or not consulta.resultados_json:
        raise ValueError("No se encontraron los resultados en caché para guardar.")

    # Verificar si ya fue guardado previamente para evitar duplicados
    existente = Itinerario.query.filter_by(
        id_generacion=id_generacion,
        numero_solucion=int(numero_solucion),
        deleted_at=None
    ).first()
    if existente:
        return {"id_itinerario": existente.id_itinerario, "ya_guardado": True}

    resultados = json.loads(consulta.resultados_json)

    # Buscar la solución específica
    soluciones = resultados.get('soluciones_viables', []) + resultados.get('soluciones_no_viables', [])
    if not soluciones:
        soluciones = resultados.get('soluciones', [])

    sol = next((s for s in soluciones if s.get('numero') == int(numero_solucion) or s.get('numero_solucion') == int(numero_solucion)), None)
    # Si no encuentra por 'numero', usa el índice
    if not sol:
        try:
            sol = soluciones[int(numero_solucion) - 1]
        except (IndexError, ValueError):
            raise ValueError("Número de solución no válido.")

    # Resolver fechas
    f_inicio_raw = sol.get('fecha_inicio') or generacion.fecha_inicio_viaje
    f_fin_raw = sol.get('fecha_fin') or generacion.fecha_fin_viaje

    f_inicio = datetime.strptime(f_inicio_raw, '%Y-%m-%d').date() if isinstance(f_inicio_raw, str) else f_inicio_raw
    f_fin = datetime.strptime(f_fin_raw, '%Y-%m-%d').date() if isinstance(f_fin_raw, str) else f_fin_raw

    # 2. Crear el Itinerario
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
        tiempo_total_estimado=sol.get('tiempo_total_min'),
        es_viable=sol.get('cumple_restricciones', True)
    )
    db.session.add(nuevo_itinerario)
    db.session.flush()  # Para obtener el id_itinerario

    # 3. Guardar los Detalles
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

        detalle = ItinerarioDetalle(
            id_itinerario=nuevo_itinerario.id_itinerario,
            id_atractivo=parada['id'],
            dia=parada['dia'],
            orden=parada.get('numero', 1),
            hora_llegada_estimada=h_llegada,
            hora_salida_estimada=h_salida,
            tiempo_traslado_desde_anterior=0,
            costo_entrada_bob=parada.get('costo_entrada_bob'),
            clima_temperatura=clima_data.get('temperatura'),
            clima_lluvia_mm=clima_data.get('precipitacion_mm'),
            clima_descripcion=clima_data.get('descripcion')
        )
        db.session.add(detalle)
        db.session.flush()

        # 4. Guardar Tráfico (si hay avisos en la parada)
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

    db.session.commit()
    return {"id_itinerario": nuevo_itinerario.id_itinerario}


def listar_itinerarios_guardados(usuario_actual):
    """
    Lista los itinerarios guardados. Preparado para separación de roles.
    Admin y Agente ven todos los itinerarios no eliminados.
    Turista ve únicamente los vinculados a sus generaciones.
    """
    rol_nombre = (usuario_actual.rol.nombre if usuario_actual.rol else '').lower()
    if rol_nombre in ['admin', 'agente']:
        return Itinerario.query.filter(
            Itinerario.deleted_at.is_(None)
        ).order_by(Itinerario.id_itinerario.desc()).all()
    else:
        return Itinerario.query.join(Generacion).filter(
            Generacion.id_usuario == usuario_actual.id_usuario,
            Itinerario.deleted_at.is_(None)
        ).order_by(Itinerario.id_itinerario.desc()).all()


def obtener_detalle_itinerario(id_itinerario: int) -> dict | None:
    """
    Reconstruye el JSON completo de un itinerario guardado para mostrarlo con el mismo
    nivel de detalle (mapas, timeline, clima, transportes) que en el generador.
    """
    itinerario = Itinerario.query.get(id_itinerario)
    if not itinerario or itinerario.is_deleted:
        return None

    # 1. Intentar cargar desde el JSON en ConsultaNSGA2 (máxima fidelidad de polilíneas, tráfico y tramos)
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
                return sol_dict
        except Exception as e:
            print(f"[WARNING] Error cargando JSON de itinerario desde ConsultaNSGA2: {e}")

    # 2. Reconstrucción manual desde las tablas de la BD si no existe o falló el JSON
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
            "tiempo_visita_min": int(d.tiempo_traslado_desde_anterior or 60),
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
