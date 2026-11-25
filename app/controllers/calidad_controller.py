# -*- coding: utf-8 -*-
"""
Controlador: Control de Calidad Metodológico
Módulo dedicado a la evaluación de calidad de software y efectividad del algoritmo NSGA-II
conforme a la metodología de investigación de la tesis (Operacionalización de Variables V2):
1. Viabilidad Operativa (Técnica: Revisión técnica | Instrumento: Lista de cotejo)
2. Tiempo de Proceso (Técnica: Medición directa | Instrumento: Cronómetro)
3. Variedad de Itinerarios (Técnica: Conteo | Instrumento: Matriz de registro de itinerarios)
4. Pertinencia del Itinerario (Técnica: Cálculo técnico | Instrumento: Ficha de registro de intereses)
"""

from datetime import datetime
from flask import Blueprint, render_template, request, Response, jsonify, redirect, url_for
from flask_login import login_required
from app.utils.decorators import role_required

from app.services.reporte_service import (
    obtener_auditoria_lista_cotejo,
    obtener_resumen_consultas_produccion,
    obtener_metricas_algoritmo,
    obtener_metricas_negocio,
)
from app.controllers.reporte_controller import (
    exportar_cotejo_csv as _generar_csv_cotejo,
    exportar_cotejo_pdf as _generar_pdf_cotejo,
)
from app.services.calidad_service import (
    obtener_fechas_consultas_disponibles,
    obtener_auditoria_tiempo_proceso,
    obtener_auditoria_variedad_itinerarios,
    obtener_auditoria_pertinencia_intereses,
    obtener_detalle_consulta_completo,
    generar_csv_tiempo,
    generar_pdf_tiempo,
    generar_csv_variedad,
    generar_pdf_variedad,
    generar_csv_pertinencia,
    generar_pdf_pertinencia,
)

calidad_bp = Blueprint('calidad', __name__, url_prefix='/calidad')


@calidad_bp.route('/', methods=['GET'])
@login_required
@role_required('admin')
def index():
    """
    Vista principal del Módulo de Control de Calidad Metodológico.
    Conecta las 4 dimensiones de la tesis con sus datos reales de la BD,
    filtros independientes por fecha/consulta y soporte de exportación independiente.
    """
    fuente_cotejo = request.args.get('fuente_cotejo', 'auto')
    fecha_filtro = request.args.get('fecha') or request.args.get('fecha_cotejo')
    if not fecha_filtro or fecha_filtro == 'todas':
        fecha_filtro = 'todas'
    id_consulta_raw = request.args.get('id_consulta') or request.args.get('id_consulta_cotejo')
    id_consulta = int(id_consulta_raw) if (id_consulta_raw and id_consulta_raw.isdigit()) else None

    tab_activa = request.args.get('tab', 'viabilidad')

    # Dimensión 1: Viabilidad (Lista de Cotejo)
    auditoria_cotejo = obtener_auditoria_lista_cotejo(
        fuente=fuente_cotejo,
        fecha_filtro=fecha_filtro,
        id_consulta=id_consulta,
    )

    # Dimensión 2: Tiempo de Proceso (Cronómetro)
    auditoria_tiempo = obtener_auditoria_tiempo_proceso(
        fecha_filtro=fecha_filtro,
        id_consulta=id_consulta,
    )

    # Dimensión 3: Variedad (Matriz de Registro de Itinerarios)
    auditoria_variedad = obtener_auditoria_variedad_itinerarios(
        fecha_filtro=fecha_filtro,
        id_consulta=id_consulta,
    )

    # Dimensión 4: Pertinencia (Ficha de Registro de Intereses)
    auditoria_pertinencia = obtener_auditoria_pertinencia_intereses(
        fecha_filtro=fecha_filtro,
        id_consulta=id_consulta,
    )

    fechas_disponibles = obtener_fechas_consultas_disponibles()

    # Métricas complementarias para contexto
    resumen_consultas = obtener_resumen_consultas_produccion()
    metricas_algoritmo = obtener_metricas_algoritmo(limit=15)
    metricas_negocio = obtener_metricas_negocio()

    return render_template(
        'calidad/index.html',
        auditoria_cotejo=auditoria_cotejo,
        auditoria_tiempo=auditoria_tiempo,
        auditoria_variedad=auditoria_variedad,
        auditoria_pertinencia=auditoria_pertinencia,
        fuente_cotejo=fuente_cotejo,
        fecha_filtro=fecha_filtro,
        fecha_cotejo=fecha_filtro,
        fechas_disponibles=fechas_disponibles,
        id_consulta=id_consulta,
        id_consulta_cotejo=id_consulta,
        tab_activa=tab_activa,
        resumen_consultas=resumen_consultas,
        metricas_algoritmo=metricas_algoritmo,
        metricas_negocio=metricas_negocio,
    )


# ==============================================================================
# API DE DETALLE MODAL (DESGLOSE DE LAS 3 DIMENSIONES)
# ==============================================================================

@calidad_bp.route('/api/consulta/<int:id_consulta>/detalle', methods=['GET'])
@login_required
@role_required('admin')
def api_detalle_consulta(id_consulta: int):
    """
    Retorna el desglose analítico de las 3 dimensiones para una consulta específica:
    - Dimensión 1: Tiempo de proceso (apertura, cierre, ventanilla, cómputo motor, origen)
    - Dimensión 2: Variedad (total opciones en el frente, tabla dinámica de opciones)
    - Dimensión 3: Pertinencia (I_C, I_E, I_T, I_P, N y pertinencia final)
    """
    detalle = obtener_detalle_consulta_completo(id_consulta)
    if "error" in detalle:
        return jsonify({"success": False, "error": detalle["error"]}), 404
    return jsonify({"success": True, "data": detalle}), 200


# ==============================================================================
# RUTAS DE EXPORTACIÓN INDEPENDIENTE CSV
# ==============================================================================

@calidad_bp.route('/exportar/cotejo/csv', methods=['GET'])
@login_required
@role_required('admin')
def exportar_cotejo_csv():
    """Exporta la Lista de Cotejo de Viabilidad Operativa en CSV."""
    return _generar_csv_cotejo()


@calidad_bp.route('/exportar/tiempo/csv', methods=['GET'])
@login_required
@role_required('admin')
def exportar_tiempo_csv():
    """Exporta los registros del Cronómetro (Tiempo de Proceso) en CSV."""
    fecha = request.args.get('fecha') or request.args.get('fecha_cotejo') or 'todas'
    id_c_raw = request.args.get('id_consulta')
    id_c = int(id_c_raw) if (id_c_raw and id_c_raw.isdigit()) else None

    data = obtener_auditoria_tiempo_proceso(fecha_filtro=fecha, id_consulta=id_c)
    csv_content = generar_csv_tiempo(data)

    nombre = f"BuhosTours_Cronometro_TiempoProceso_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={nombre}"}
    )


@calidad_bp.route('/exportar/variedad/csv', methods=['GET'])
@login_required
@role_required('admin')
def exportar_variedad_csv():
    """Exporta la Matriz de Registro de Itinerarios (Variedad) en CSV."""
    fecha = request.args.get('fecha') or request.args.get('fecha_cotejo') or 'todas'
    id_c_raw = request.args.get('id_consulta')
    id_c = int(id_c_raw) if (id_c_raw and id_c_raw.isdigit()) else None

    data = obtener_auditoria_variedad_itinerarios(fecha_filtro=fecha, id_consulta=id_c)
    csv_content = generar_csv_variedad(data)

    nombre = f"BuhosTours_Matriz_VariedadItinerarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={nombre}"}
    )


@calidad_bp.route('/exportar/pertinencia/csv', methods=['GET'])
@login_required
@role_required('admin')
def exportar_pertinencia_csv():
    """Exporta la Ficha de Registro de Intereses (Pertinencia) en CSV."""
    fecha = request.args.get('fecha') or request.args.get('fecha_cotejo') or 'todas'
    id_c_raw = request.args.get('id_consulta')
    id_c = int(id_c_raw) if (id_c_raw and id_c_raw.isdigit()) else None

    data = obtener_auditoria_pertinencia_intereses(fecha_filtro=fecha, id_consulta=id_c)
    csv_content = generar_csv_pertinencia(data)

    nombre = f"BuhosTours_Ficha_PertinenciaIntereses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={nombre}"}
    )


# ==============================================================================
# RUTAS DE EXPORTACIÓN INDEPENDIENTE PDF
# ==============================================================================

@calidad_bp.route('/exportar/cotejo/pdf', methods=['GET'])
@login_required
@role_required('admin')
def exportar_cotejo_pdf():
    """Exporta la Lista de Cotejo de Viabilidad Operativa en PDF."""
    return _generar_pdf_cotejo()


@calidad_bp.route('/exportar/tiempo/pdf', methods=['GET'])
@login_required
@role_required('admin')
def exportar_tiempo_pdf():
    """Exporta el Reporte Metodológico de Cronómetro (Tiempo de Proceso) en PDF."""
    fecha = request.args.get('fecha') or request.args.get('fecha_cotejo') or 'todas'
    id_c_raw = request.args.get('id_consulta')
    id_c = int(id_c_raw) if (id_c_raw and id_c_raw.isdigit()) else None

    data = obtener_auditoria_tiempo_proceso(fecha_filtro=fecha, id_consulta=id_c)
    pdf_buffer = generar_pdf_tiempo(data)

    nombre = f"BuhosTours_Cronometro_TiempoProceso_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return Response(
        pdf_buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nombre}"}
    )


@calidad_bp.route('/exportar/variedad/pdf', methods=['GET'])
@login_required
@role_required('admin')
def exportar_variedad_pdf():
    """Exporta el Reporte Metodológico de Matriz de Registro (Variedad) en PDF."""
    fecha = request.args.get('fecha') or request.args.get('fecha_cotejo') or 'todas'
    id_c_raw = request.args.get('id_consulta')
    id_c = int(id_c_raw) if (id_c_raw and id_c_raw.isdigit()) else None

    data = obtener_auditoria_variedad_itinerarios(fecha_filtro=fecha, id_consulta=id_c)
    pdf_buffer = generar_pdf_variedad(data)

    nombre = f"BuhosTours_Matriz_VariedadItinerarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return Response(
        pdf_buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nombre}"}
    )


@calidad_bp.route('/exportar/pertinencia/pdf', methods=['GET'])
@login_required
@role_required('admin')
def exportar_pertinencia_pdf():
    """Exporta el Reporte Metodológico de Ficha de Registro (Pertinencia) en PDF."""
    fecha = request.args.get('fecha') or request.args.get('fecha_cotejo') or 'todas'
    id_c_raw = request.args.get('id_consulta')
    id_c = int(id_c_raw) if (id_c_raw and id_c_raw.isdigit()) else None

    data = obtener_auditoria_pertinencia_intereses(fecha_filtro=fecha, id_consulta=id_c)
    pdf_buffer = generar_pdf_pertinencia(data)

    nombre = f"BuhosTours_Ficha_PertinenciaIntereses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return Response(
        pdf_buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nombre}"}
    )
