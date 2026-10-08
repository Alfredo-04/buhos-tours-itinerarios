from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user
from app.utils.decorators import role_required
from app.models.atractivo import Atractivo
from app.models.transporte import Transporte
from app.models.categoria import Categoria
from app.services.itinerario_service import generar_itinerarios
from app.services.exchange_service import obtener_tc_oficial

itinerarios_bp = Blueprint('itinerarios', __name__, url_prefix='/itinerarios')


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
        tiempo_disponible_horas = data.get('tiempo_disponible_horas')
        intereses = data.get('intereses', {})
        num_personas = data.get('num_personas', 1)
        forzar_atractivos = bool(data.get('forzar_atractivos', False))
        forzar_transporte = bool(data.get('forzar_transporte', False))
        
        # Parámetros avanzados con valores por defecto
        tamano_poblacion = data.get('tamano_poblacion', 50)
        generaciones = data.get('generaciones', 40)
        prob_cruce = data.get('prob_cruce', 0.9)
        prob_mutacion = data.get('prob_mutacion', 0.2)

        # Validaciones de entrada (si el usuario seleccionó atractivos, deben ser al menos 2; si no seleccionó ninguno, se usa todo el catálogo)
        if atractivos_ids and isinstance(atractivos_ids, list) and len(atractivos_ids) == 1:
            return jsonify({
                "success": False,
                "error": "Si especificas atractivos, debes seleccionar al menos 2 para formar una ruta de viaje."
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
            tiempo_disponible_horas = float(tiempo_disponible_horas)
            if tiempo_disponible_horas <= 0 or tiempo_disponible_horas > 48:
                return jsonify({
                    "success": False,
                    "error": "El tiempo disponible debe ser un valor válido entre 0.5 y 48 horas."
                }), 400
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "error": "El tiempo disponible debe ser un número válido."
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
            min_paradas = max(1, int(min_paradas))
        except (TypeError, ValueError):
            min_paradas = 2

        try:
            max_paradas = max(min_paradas, int(max_paradas))
        except (TypeError, ValueError):
            max_paradas = 15

        # Ejecutar orquestador
        resultado = generar_itinerarios(
            atractivos_ids=[int(aid) for aid in atractivos_ids] if atractivos_ids else [],
            transporte_ids=[int(tid) for tid in transporte_ids] if transporte_ids else [],
            presupuesto_max=presupuesto_max,
            tiempo_disponible_horas=tiempo_disponible_horas,
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
