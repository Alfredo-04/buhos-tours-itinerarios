from flask import Blueprint, render_template, request, jsonify, flash, abort
from flask_login import login_required, current_user
from app.utils.decorators import role_required
from app.models.atractivo import Atractivo
from app.models.transporte import Transporte
from app.models.categoria import Categoria
from app.services import itinerario_service
from app.services.itinerario_service import generar_itinerarios
from app.services.exchange_service import obtener_tc_oficial

itinerarios_bp = Blueprint('itinerarios', __name__, url_prefix='/itinerarios')
turistas_api_bp = Blueprint('turistas_api', __name__, url_prefix='/turistas')


@itinerarios_bp.route('/generar', methods=['GET'])
@login_required
@role_required('admin')
def generar_view():
    """
    Renderiza la interfaz principal para la generación y optimización de itinerarios turísticos.
    Carga atractivos agrupados por categoría y transportes activos desde la base de datos real.
    Acceso exclusivo para el Administrador.
    """
    # Categorías activas con sus atractivos no eliminados
    categorias = Categoria.query.filter_by(deleted_at=None).order_by(Categoria.nombre.asc()).all()
    
    # Atractivos activos
    atractivos_activos = Atractivo.query.filter_by(deleted_at=None).order_by(Atractivo.nombre.asc()).all()
    
    # Transportes activos
    transportes_activos = Transporte.query.filter_by(deleted_at=None).order_by(Transporte.velocidad_promedio_kmh.desc()).all()
    
    # Tipo de cambio oficial BCB
    tc = obtener_tc_oficial()

    return render_template(
        'itinerarios/generar.html',
        categorias=categorias,
        atractivos=atractivos_activos,
        transportes=transportes_activos,
        tc_oficial=tc
    )


@itinerarios_bp.route('/generar', methods=['POST'])
@login_required
@role_required('admin')
def generar_action():
    """
    Endpoint asíncrono (JSON) para procesar la optimización de itinerarios con NSGA-II.
    Recibe parámetros de preferencias, ejecuta el algoritmo y retorna soluciones y métricas.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                "success": False,
                "error": "No se recibieron datos en formato JSON válido."
            }), 400

        atractivos_ids = data.get('atractivos_ids', [])
        transporte_ids = data.get('transporte_ids', [])
        presupuesto_max = data.get('presupuesto_max')
        fecha_inicio_viaje = data.get('fecha_inicio_viaje')
        num_dias_disponibles = data.get('num_dias_disponibles', 1)
        hora_inicio_dia = data.get('hora_inicio_dia', '09:00')
        hora_fin_dia = data.get('hora_fin_dia', '18:00')
        auto_fechas = bool(data.get('auto_fechas', True))
        intereses = data.get('intereses', {})
        num_personas = data.get('num_personas', 1)
        forzar_atractivos = bool(data.get('forzar_atractivos', False))
        forzar_transporte = bool(data.get('forzar_transporte', False))
        usar_clima = bool(data.get('usar_clima', True))
        
        # Parámetros avanzados con valores por defecto
        tamano_poblacion = data.get('tamano_poblacion', 50)
        generaciones = data.get('generaciones', 40)
        prob_cruce = data.get('prob_cruce', 0.9)
        prob_mutacion = data.get('prob_mutacion', 0.2)

        # Validaciones de entrada (si el usuario seleccionó atractivos, deben ser al menos 2; si no seleccionó ninguno, se usa todo el catálogo)
        if atractivos_ids and isinstance(atractivos_ids, list) and len(atractivos_ids) < 2:
            return jsonify({
                "success": False,
                "error": "Debes seleccionar al menos 2 atractivos turísticos."
            }), 400

        try:
            num_personas = max(1, int(num_personas))
        except (TypeError, ValueError):
            num_personas = 1

        try:
            presupuesto_max = float(presupuesto_max)
            if presupuesto_max <= 0:
                raise ValueError()
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "error": "El presupuesto máximo debe ser un número positivo mayor a 0."
            }), 400

        try:
            num_dias_disponibles = int(num_dias_disponibles)
            if num_dias_disponibles < 1 or num_dias_disponibles > 14:
                return jsonify({
                    "success": False,
                    "error": "El número de días disponibles debe ser un valor entre 1 y 14."
                }), 400
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "error": "El número de días disponibles debe ser un número entero válido."
            }), 400

        from datetime import datetime, time as dtime, timezone, timedelta
        bolivia_tz = timezone(timedelta(hours=-4))

        if not auto_fechas:
            if not fecha_inicio_viaje:
                return jsonify({
                    "success": False,
                    "error": "Debes seleccionar la fecha de inicio del viaje si no usas fechas automáticas."
                }), 400
            try:
                fecha_parsed = datetime.strptime(str(fecha_inicio_viaje).strip(), "%Y-%m-%d").date()
                hoy_bolivia = datetime.now(bolivia_tz).date()
                if fecha_parsed < hoy_bolivia:
                    return jsonify({
                        "success": False,
                        "error": "La fecha de inicio del viaje no puede ser una fecha pasada."
                    }), 400
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Formato de fecha de inicio inválido (se esperaba AAAA-MM-DD)."
                }), 400

            try:
                h_ini = datetime.strptime(str(hora_inicio_dia).strip(), "%H:%M").time()
                h_fin = datetime.strptime(str(hora_fin_dia).strip(), "%H:%M").time()
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Formato de hora inválido (se esperaba HH:MM)."
                }), 400

            if h_ini < dtime(6, 0) or h_fin > dtime(19, 59):
                return jsonify({
                    "success": False,
                    "error": "El horario diario solo se permite entre las 06:00 y las 19:59."
                }), 400

            if h_fin <= h_ini:
                return jsonify({
                    "success": False,
                    "error": "La hora de fin del día debe ser posterior a la hora de inicio."
                }), 400

        try:
            tamano_poblacion = int(tamano_poblacion)
            generaciones = int(generaciones)
            prob_cruce = float(prob_cruce)
            prob_mutacion = float(prob_mutacion)

            if tamano_poblacion < 10 or tamano_poblacion > 250:
                tamano_poblacion = 100
            if generaciones < 5 or generaciones > 200:
                generaciones = 100
            if not (0.1 <= prob_cruce <= 1.0):
                prob_cruce = 0.85
            if not (0.01 <= prob_mutacion <= 0.9):
                prob_mutacion = 0.15
        except (TypeError, ValueError):
            tamano_poblacion = 100
            generaciones = 100
            prob_cruce = 0.85
            prob_mutacion = 0.15

        auto_rango_paradas = bool(data.get('auto_rango_paradas', True))
        categorias_activas_ids = data.get('categorias_activas_ids')
        subcategorias_activas_ids = data.get('subcategorias_activas_ids')
        if categorias_activas_ids is not None and isinstance(categorias_activas_ids, list):
            categorias_activas_ids = [int(cid) for cid in categorias_activas_ids]
        if subcategorias_activas_ids is not None and isinstance(subcategorias_activas_ids, list):
            subcategorias_activas_ids = [int(scid) for scid in subcategorias_activas_ids]

        min_paradas = data.get('min_paradas', 2)
        max_paradas = data.get('max_paradas', 15)
        try:
            min_paradas = int(min_paradas)
        except (TypeError, ValueError):
            min_paradas = 2

        try:
            max_paradas = int(max_paradas)
        except (TypeError, ValueError):
            max_paradas = 15

        permitir_multiples_vehiculos = bool(data.get('permitir_multiples_vehiculos', False))

        # Ejecutar orquestador
        resultado = generar_itinerarios(
            atractivos_ids=[int(aid) for aid in atractivos_ids] if atractivos_ids else [],
            transporte_ids=[int(tid) for tid in transporte_ids] if transporte_ids else [],
            presupuesto_max=presupuesto_max,
            fecha_inicio_viaje=fecha_inicio_viaje,
            num_dias_disponibles=num_dias_disponibles,
            hora_inicio_dia=hora_inicio_dia,
            hora_fin_dia=hora_fin_dia,
            auto_fechas=auto_fechas,
            intereses=intereses,
            tamano_poblacion=tamano_poblacion,
            generaciones=generaciones,
            prob_cruce=prob_cruce,
            prob_mutacion=prob_mutacion,
            num_personas=num_personas,
            forzar_atractivos=forzar_atractivos,
            forzar_transporte=forzar_transporte,
            min_paradas=min_paradas,
            max_paradas=max_paradas,
            auto_rango_paradas=auto_rango_paradas,
            categorias_activas_ids=categorias_activas_ids,
            subcategorias_activas_ids=subcategorias_activas_ids,
            usar_clima=usar_clima,
            id_usuario=current_user.id_usuario,
            permitir_multiples_vehiculos=permitir_multiples_vehiculos,
        )

        return jsonify({
            "success": True,
            "data": resultado
        }), 200

    except ValueError as ve:
        return jsonify({
            "success": False,
            "error": str(ve)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error interno en la ejecución de la optimización: {str(e)}"
        }), 500


@turistas_api_bp.route('/buscar', methods=['GET'])
@itinerarios_bp.route('/turistas/buscar', methods=['GET'])
@itinerarios_bp.route('/turista/buscar', methods=['GET'])
@login_required
def buscar_turista_endpoint():
    """
    Busca si un turista ya existe por su documento y procedencia para autocompletar el formulario.
    Soporta nro_documento + procedencia, o documento solo por compatibilidad retroactiva.
    """
    documento = request.args.get('nro_documento') or request.args.get('documento', '')
    procedencia = request.args.get('procedencia')
    if procedencia is not None:
        resultado = itinerario_service.buscar_turista(documento, procedencia)
    else:
        resultado = itinerario_service.buscar_turista_por_documento(documento)
    return jsonify(resultado), 200


@itinerarios_bp.route('/guardar', methods=['POST'])
@login_required
def guardar():
    """
    Guarda en base de datos un itinerario seleccionado de la consulta actual.
    Valida viabilidad, gestiona duplicados por rol y asocia al turista titular.
    """
    payload = request.get_json(silent=True) or {}
    id_generacion = payload.get('id_generacion')
    numero_solucion = payload.get('numero_solucion')
    turista_data = payload.get('turista')
    forzar_nuevo = bool(payload.get('forzar_nuevo', False))

    if not id_generacion or numero_solucion is None:
        return jsonify({
            "success": False,
            "error": "Parámetros insuficientes: 'id_generacion' y 'numero_solucion' son obligatorios."
        }), 400

    try:
        res = itinerario_service.guardar_itinerario(
            id_generacion=int(id_generacion),
            numero_solucion=int(numero_solucion),
            id_usuario=current_user.id_usuario,
            turista_data=turista_data,
            forzar_nuevo=forzar_nuevo
        )

        if res.get("duplicado_admin"):
            return jsonify({
                "success": False,
                "duplicado_admin": True,
                "mensaje": res.get("mensaje", "Este itinerario ya fue guardado antes. ¿Deseas crear una nueva reserva para un nuevo grupo?")
            }), 200

        return jsonify({
            "success": True,
            "id_itinerario": res['id_itinerario'],
            "codigo_confirmacion": res.get("codigo_confirmacion"),
            "advertencia_acompanantes": res.get("advertencia_acompanantes")
        }), 200
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al guardar itinerario: {str(e)}"}), 500


@itinerarios_bp.route('/<int:id_itinerario>/acompanantes', methods=['POST'])
@login_required
def agregar_acompanante_endpoint(id_itinerario):
    """
    Añade un acompañante a un itinerario en estado Borrador.
    """
    payload = request.get_json(silent=True) or {}
    try:
        resultado = itinerario_service.agregar_acompanante(
            id_itinerario=id_itinerario,
            datos=payload,
            id_usuario_actual=current_user.id_usuario
        )
        return jsonify(resultado), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@itinerarios_bp.route('/<int:id_itinerario>/turistas', methods=['GET'])
@login_required
def listar_turistas_endpoint(id_itinerario):
    """
    Retorna la lista de turistas vinculados a un itinerario y su conteo de cupos.
    """
    try:
        it = itinerario_service.Itinerario.query.get(id_itinerario)
        if not it or it.is_deleted:
            abort(404)
        turistas = itinerario_service.listar_turistas_itinerario(id_itinerario)
        conteo = itinerario_service.calcular_faltantes(id_itinerario)
        return jsonify({
            "itinerario": {
                "id": it.id_itinerario,
                "num_personas": it.num_personas,
                "estado": it.estado
            },
            "turistas": turistas,
            "conteo": conteo
        }), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@itinerarios_bp.route('/lista', methods=['GET'])
@login_required
def lista():
    """
    Vista de lista de itinerarios guardados.
    Admin y Agente ven todos los itinerarios; Turista ve únicamente los propios.
    """
    itinerarios = itinerario_service.listar_itinerarios_guardados(current_user)
    tc = obtener_tc_oficial()
    return render_template('itinerarios/lista.html', itinerarios=itinerarios, tc_oficial=tc)


@itinerarios_bp.route('/<int:id_itinerario>', methods=['GET'])
@login_required
def detalle(id_itinerario):
    """
    Vista detallada de un itinerario guardado con visualización idéntica al generador
    (mapa interactivo, desglose secuencial, pronóstico de clima, transporte y KPIs).
    """
    data = itinerario_service.obtener_detalle_itinerario(id_itinerario)
    if not data:
        abort(404)
    tc = obtener_tc_oficial()
    conteo = itinerario_service.calcular_faltantes(id_itinerario)
    listado_turistas = itinerario_service.listar_turistas_itinerario(id_itinerario)
    return render_template(
        'itinerarios/detalle.html',
        itinerario=data,
        conteo=conteo,
        listado_turistas=listado_turistas,
        tc_oficial=tc
    )

