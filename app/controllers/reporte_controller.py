import io
import csv
from datetime import datetime
from flask import Blueprint, render_template, Response, abort, request
from flask_login import login_required
from app.services.reporte_service import (
    obtener_metricas_negocio,
    obtener_metricas_algoritmo,
    obtener_metricas_entrenamiento,
    obtener_resumen_consultas_produccion,
    obtener_auditoria_lista_cotejo,
)

# Configuración no interactiva para Matplotlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ReportLab Platypus
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

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')


@reportes_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard_view():
    """
    Renderiza el Dashboard ejecutivo con métricas de negocio, académicas del NSGA-II
    y la Lista de Cotejo de Viabilidad Operativa.
    """
    fuente_cotejo = request.args.get('fuente_cotejo', 'auto')
    fecha_cotejo = request.args.get('fecha_cotejo')
    id_consulta_raw = request.args.get('id_consulta_cotejo')
    id_consulta_cotejo = int(id_consulta_raw) if (id_consulta_raw and id_consulta_raw.isdigit()) else None

    metricas_negocio = obtener_metricas_negocio()
    metricas_algoritmo = obtener_metricas_algoritmo(limit=20)
    metricas_entrenamiento = obtener_metricas_entrenamiento()
    resumen_consultas = obtener_resumen_consultas_produccion()
    auditoria_cotejo = obtener_auditoria_lista_cotejo(
        fuente=fuente_cotejo,
        fecha_filtro=fecha_cotejo,
        id_consulta=id_consulta_cotejo,
    )
    return render_template(
        'reportes/dashboard.html',
        metricas_negocio=metricas_negocio,
        metricas_algoritmo=metricas_algoritmo,
        metricas_entrenamiento=metricas_entrenamiento,
        resumen_consultas=resumen_consultas,
        auditoria_cotejo=auditoria_cotejo,
        fuente_cotejo=fuente_cotejo,
        fecha_cotejo=auditoria_cotejo['resumen'].get('fecha_filtro'),
        id_consulta_cotejo=id_consulta_cotejo,
    )


@reportes_bp.route('/exportar/csv', methods=['GET'])
@login_required
def exportar_csv():
    """
    Genera y descarga un reporte consolidado en formato CSV con secciones delimitadas.
    """
    metricas_negocio = obtener_metricas_negocio()
    metricas_algoritmo = obtener_metricas_algoritmo(limit=50)

    output = io.StringIO()
    writer = csv.writer(output, delimiter=',', quoting=csv.QUOTE_MINIMAL)

    # 1. Encabezado principal
    writer.writerow(["BUHOS TOURS - REPORTE GENERAL DEL SISTEMA"])
    writer.writerow(["Fecha de Emision", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])

    # 2. Métricas de Negocio
    writer.writerow(["--- METRICAS DE NEGOCIO ---"])
    writer.writerow(["Metrica", "Valor"])
    writer.writerow(["Total Itinerarios Guardados", metricas_negocio["total_itinerarios"]])
    writer.writerow(["Presupuesto Promedio (BOB)", metricas_negocio["presupuesto_promedio"]])
    writer.writerow(["Duracion Promedio (Dias)", metricas_negocio["duracion_promedio"]])
    writer.writerow(["Tiempo Proceso Promedio Algoritmo (seg)", metricas_negocio["tiempo_proceso_promedio"]])
    writer.writerow(["Porcentaje de Viabilidad (%)", f"{metricas_negocio['porcentaje_viabilidad']}%"])
    writer.writerow([])

    # 3. Top Atractivos
    writer.writerow(["--- TOP ATRACTIVOS MAS SOLICITADOS ---"])
    writer.writerow(["Posicion", "Nombre del Atractivo", "Total Visitas Registradas"])
    if metricas_negocio["top_atractivos"]:
        for idx, at in enumerate(metricas_negocio["top_atractivos"], 1):
            writer.writerow([idx, at["nombre"], at["visitas"]])
    else:
        writer.writerow(["-", "Sin itinerarios registrados aún", 0])
    writer.writerow([])

    # 4. Métricas Académicas NSGA-II
    writer.writerow(["--- METRICAS ACADEMICAS DE OPTIMIZACION (NSGA-II) ---"])
    writer.writerow([
        "ID Consulta",
        "Fecha",
        "Poblacion",
        "Generaciones",
        "Tiempo Ejecucion (seg)",
        "N Soluciones",
        "Hipervolumen (HV)",
        "Generational Distance (GD)",
        "Spread / Spacing",
        "Puntos Ref Archivo",
    ])
    if metricas_algoritmo:
        for reg in metricas_algoritmo:
            writer.writerow([
                reg["id_consulta"],
                reg["fecha"],
                reg["tamano_poblacion"],
                reg["generaciones"],
                reg["tiempo_ejecucion_seg"],
                reg["num_soluciones"],
                reg["hipervolumen"],
                reg["gd"],
                reg["spread"],
                reg["num_soluciones_archivo_ref"],
            ])
    else:
        writer.writerow(["-", "Sin ejecuciones registradas", "-", "-", "-", "-", "-", "-", "-", 0])

    csv_data = "\ufeff" + output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=reporte_buhos_tours.csv"},
    )


@reportes_bp.route('/exportar/pdf', methods=['GET'])
@login_required
def exportar_pdf():
    """
    Genera y descarga un reporte formal en PDF utilizando ReportLab y gráficos generados con Matplotlib.
    """
    metricas_negocio = obtener_metricas_negocio()
    metricas_algoritmo = obtener_metricas_algoritmo(limit=10)

    # 1. Generación de Gráfico 1: Top Atractivos con Matplotlib
    buf_grafico_atractivos = io.BytesIO()
    fig1, ax1 = plt.subplots(figsize=(7, 3.2), dpi=150)
    top_at = metricas_negocio.get("top_atractivos", [])
    if top_at:
        nombres = [item["nombre"][:22] + "..." if len(item["nombre"]) > 22 else item["nombre"] for item in top_at[::-1]]
        visitas = [item["visitas"] for item in top_at[::-1]]
        bars = ax1.barh(nombres, visitas, color="#0284c7", edgecolor="#0369a1", height=0.6)
        ax1.set_title("Top Atractivos más Solicitados", fontsize=11, fontweight="bold", color="#1e293b", pad=10)
        ax1.set_xlabel("Visitas en Itinerarios Guardados", fontsize=9, color="#475569")
        ax1.grid(axis="x", linestyle="--", alpha=0.5)
        ax1.tick_params(axis="both", labelsize=8)
        # Añadir valores sobre las barras
        for bar in bars:
            width = bar.get_width()
            ax1.text(width + 0.1, bar.get_y() + bar.get_height() / 2, f"{int(width)}",
                     ha="left", va="center", fontsize=8, color="#0f172a", fontweight="bold")
    else:
        ax1.text(0.5, 0.5, "Sin datos de atractivos registrados aún", ha="center", va="center", color="#94a3b8", fontsize=10)
        ax1.set_axis_off()

    fig1.tight_layout()
    fig1.savefig(buf_grafico_atractivos, format="png")
    plt.close(fig1)
    buf_grafico_atractivos.seek(0)

    # 2. Generación de Gráfico 2: Itinerarios por Mes con Matplotlib
    buf_grafico_mes = io.BytesIO()
    fig2, ax2 = plt.subplots(figsize=(7, 2.8), dpi=150)
    it_mes = metricas_negocio.get("itinerarios_por_mes", [])
    if it_mes:
        meses = [item["mes"] for item in it_mes]
        cantidades = [item["cantidad"] for item in it_mes]
        ax2.plot(meses, cantidades, marker="o", color="#0d9488", linewidth=2.2, markersize=6, label="Itinerarios")
        ax2.fill_between(meses, cantidades, color="#99f6e4", alpha=0.35)
        ax2.set_title("Evolución de Itinerarios Guardados por Mes", fontsize=11, fontweight="bold", color="#1e293b", pad=10)
        ax2.set_ylabel("Cantidad", fontsize=9, color="#475569")
        ax2.grid(True, linestyle="--", alpha=0.5)
        ax2.tick_params(axis="both", labelsize=8)
    else:
        ax2.text(0.5, 0.5, "Sin datos de itinerarios guardados por mes", ha="center", va="center", color="#94a3b8", fontsize=10)
        ax2.set_axis_off()

    fig2.tight_layout()
    fig2.savefig(buf_grafico_mes, format="png")
    plt.close(fig2)
    buf_grafico_mes.seek(0)

    # 3. Construcción del PDF con ReportLab
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

    # Estilos personalizados
    titulo_principal = ParagraphStyle(
        'TituloPrincipal',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold',
        spaceAfter=4,
    )
    subtitulo = ParagraphStyle(
        'Subtitulo',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=14,
    )
    seccion_heading = ParagraphStyle(
        'SeccionHeading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0369a1'),
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=8,
    )
    estilo_celda = ParagraphStyle(
        'EstiloCelda',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b'),
    )
    estilo_celda_header = ParagraphStyle(
        'EstiloCeldaHeader',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.white,
        fontName='Helvetica-Bold',
    )

    story = []

    # Cabecera Institucional
    story.append(Paragraph("BUHOS TOURS", titulo_principal))
    story.append(Paragraph(
        f"Reporte General del Sistema | Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        subtitulo
    ))
    story.append(Spacer(1, 4))

    # Sección 1: Métricas de Negocio
    story.append(Paragraph("1. Métricas de Negocio", seccion_heading))
    data_negocio = [
        [
            Paragraph("Total Itinerarios", estilo_celda_header),
            Paragraph("Presupuesto Promedio", estilo_celda_header),
            Paragraph("Duración Promedio", estilo_celda_header),
            Paragraph("Tiempo Algoritmo", estilo_celda_header),
            Paragraph("Viabilidad", estilo_celda_header),
        ],
        [
            Paragraph(f"<b>{metricas_negocio['total_itinerarios']}</b>", estilo_celda),
            Paragraph(f"<b>Bs. {metricas_negocio['presupuesto_promedio']:.2f}</b>", estilo_celda),
            Paragraph(f"<b>{metricas_negocio['duracion_promedio']:.1f} días</b>", estilo_celda),
            Paragraph(f"<b>{metricas_negocio['tiempo_proceso_promedio']:.2f} s</b>", estilo_celda),
            Paragraph(f"<b>{metricas_negocio['porcentaje_viabilidad']}%</b>", estilo_celda),
        ]
    ]
    tabla_negocio = Table(data_negocio, colWidths=[108, 110, 108, 108, 106])
    tabla_negocio.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f8fafc')),
    ]))
    story.append(tabla_negocio)
    story.append(Spacer(1, 12))

    # Sección 2: Gráficos Estadísticos
    story.append(Paragraph("2. Estadísticas Visuales", seccion_heading))
    story.append(RLImage(buf_grafico_atractivos, width=540, height=210))
    story.append(Spacer(1, 8))
    story.append(RLImage(buf_grafico_mes, width=540, height=170))
    story.append(Spacer(1, 12))

    # Sección 3: Métricas Académicas NSGA-II
    story.append(KeepTogether([
        Paragraph("3. Métricas Académicas Multiobjetivo (Últimas Ejecuciones NSGA-II)", seccion_heading),
        Paragraph(
            "<font color='#64748b' size='7'>Indicadores calculados con biblioteca estándar pymoo: Hipervolumen (HV), Generational Distance (GD) y Spacing.</font>",
            subtitulo
        )
    ]))

    header_academicas = [
        Paragraph("Fecha", estilo_celda_header),
        Paragraph("Pob.", estilo_celda_header),
        Paragraph("Gen.", estilo_celda_header),
        Paragraph("Tiempo", estilo_celda_header),
        Paragraph("Sol.", estilo_celda_header),
        Paragraph("HV", estilo_celda_header),
        Paragraph("GD", estilo_celda_header),
        Paragraph("Spread", estilo_celda_header),
        Paragraph("Ref N", estilo_celda_header),
    ]

    filas_academicas = [header_academicas]
    if metricas_algoritmo:
        for reg in metricas_algoritmo:
            filas_academicas.append([
                Paragraph(str(reg["fecha"]), estilo_celda),
                Paragraph(str(reg["tamano_poblacion"]), estilo_celda),
                Paragraph(str(reg["generaciones"]), estilo_celda),
                Paragraph(f"{reg['tiempo_ejecucion_seg']}s" if reg["tiempo_ejecucion_seg"] != "-" else "-", estilo_celda),
                Paragraph(str(reg["num_soluciones"]), estilo_celda),
                Paragraph(str(reg["hipervolumen"]), estilo_celda),
                Paragraph(str(reg["gd"]), estilo_celda),
                Paragraph(str(reg["spread"]), estilo_celda),
                Paragraph(str(reg["num_soluciones_archivo_ref"]), estilo_celda),
            ])
    else:
        filas_academicas.append([
            Paragraph("Sin registros de optimización", estilo_celda),
            Paragraph("-", estilo_celda),
            Paragraph("-", estilo_celda),
            Paragraph("-", estilo_celda),
            Paragraph("-", estilo_celda),
            Paragraph("-", estilo_celda),
            Paragraph("-", estilo_celda),
            Paragraph("-", estilo_celda),
            Paragraph("-", estilo_celda),
        ])

    tabla_acad = Table(filas_academicas, colWidths=[100, 45, 45, 55, 45, 65, 65, 65, 55])
    tabla_acad.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0369a1')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
    ]))
    story.append(tabla_acad)

    doc.build(story)
    pdf_buffer.seek(0)

    return Response(
        pdf_buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reporte_buhos_tours.pdf"},
    )


@reportes_bp.route('/exportar/cotejo/csv', methods=['GET'])
@login_required
def exportar_cotejo_csv():
    """
    Exporta la Lista de Cotejo de Viabilidad Operativa en formato CSV respetando los filtros activos.
    """
    fuente = request.args.get('fuente', 'auto')
    fecha_cotejo = request.args.get('fecha_cotejo')
    id_consulta_raw = request.args.get('id_consulta_cotejo')
    id_consulta = int(id_consulta_raw) if (id_consulta_raw and id_consulta_raw.isdigit()) else None

    cotejo_data = obtener_auditoria_lista_cotejo(
        fuente=fuente,
        fecha_filtro=fecha_cotejo,
        id_consulta=id_consulta,
    )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=',', quoting=csv.QUOTE_MINIMAL)

    # Encabezado
    writer.writerow(["BUHOS TOURS - LISTA DE COTEJO DE VIABILIDAD OPERATIVA"])
    writer.writerow(["Fecha de Emision", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow(["Filtro Fecha Ejecucion", cotejo_data["resumen"].get("fecha_filtro", "Todas")])
    writer.writerow(["Fuente de Evaluacion", cotejo_data["resumen"]["fuente_utilizada"]])
    writer.writerow(["Total Itinerarios Evaluados", cotejo_data["resumen"]["total_evaluados"]])
    writer.writerow(["Itinerarios Viables (Sin conflictos)", cotejo_data["resumen"]["viables"]])
    writer.writerow(["Itinerarios Con Conflicto", cotejo_data["resumen"]["con_conflictos"]])
    writer.writerow(["Porcentaje de Viabilidad (%)", f"{cotejo_data['resumen']['porcentaje_viabilidad']}%"])
    writer.writerow([])

    # Resumen por criterio
    writer.writerow(["--- CUMPLIMIENTO POR CRITERIO DICOTOMICO ---"])
    writer.writerow(["Codigo", "Criterio", "Cumple (Si)", "% Si", "No Cumple (No)", "% No"])
    for crit in cotejo_data["tabla_criterios"]:
        writer.writerow([
            crit["codigo"],
            crit["criterio"],
            crit["si_count"],
            f"{crit['si_pct']}%",
            crit["no_count"],
            f"{crit['no_pct']}%",
        ])
    writer.writerow([])

    # Detalle de cada itinerario
    writer.writerow(["--- EVALUACION DETALLADA POR ITINERARIO ---"])
    writer.writerow([
        "Codigo / ID",
        "Origen",
        "Fecha Ejecucion",
        "Fecha Visita",
        "Dias",
        "N Paradas",
        "Personas",
        "Costo Total (BOB)",
        "C1 Apertura",
        "C2 Cierre",
        "C3 Traslados",
        "C4 Transporte",
        "Estado Global",
        "Observaciones / Conflictos",
    ])

    for it in cotejo_data["itinerarios"]:
        writer.writerow([
            it["id_codigo"],
            it["origen"],
            it.get("fecha_ejecucion", it["fecha"]),
            it.get("fecha_visita", it["fecha"]),
            it["dias"],
            it["paradas_count"],
            it["num_personas"],
            f"{it['costo_bob']:.2f}",
            "SI" if it["c1"] else "NO",
            "SI" if it["c2"] else "NO",
            "SI" if it["c3"] else "NO",
            "SI" if it["c4"] else "NO",
            it["estado"],
            it["observaciones"],
        ])

    csv_data = "\ufeff" + output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=lista_cotejo_viabilidad.csv"},
    )


@reportes_bp.route('/exportar/cotejo/pdf', methods=['GET'])
@login_required
def exportar_cotejo_pdf():
    """
    Genera y descarga el Reporte Formal de la Lista de Cotejo de Viabilidad Operativa en PDF respetando los filtros activos.
    """
    fuente = request.args.get('fuente', 'auto')
    fecha_cotejo = request.args.get('fecha_cotejo')
    id_consulta_raw = request.args.get('id_consulta_cotejo')
    id_consulta = int(id_consulta_raw) if (id_consulta_raw and id_consulta_raw.isdigit()) else None

    cotejo_data = obtener_auditoria_lista_cotejo(
        fuente=fuente,
        fecha_filtro=fecha_cotejo,
        id_consulta=id_consulta,
    )

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
    titulo_principal = ParagraphStyle(
        'TituloPrincipalCotejo',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold',
        spaceAfter=4,
    )
    subtitulo = ParagraphStyle(
        'SubtituloCotejo',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=12,
    )
    seccion_heading = ParagraphStyle(
        'SeccionHeadingCotejo',
        parent=styles['Heading2'],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0369a1'),
        fontName='Helvetica-Bold',
        spaceBefore=8,
        spaceAfter=6,
    )
    estilo_celda = ParagraphStyle(
        'EstiloCeldaCotejo',
        parent=styles['Normal'],
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#1e293b'),
    )
    estilo_celda_header = ParagraphStyle(
        'EstiloCeldaHeaderCotejo',
        parent=styles['Normal'],
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
        fontName='Helvetica-Bold',
    )

    story = []

    # Cabecera
    story.append(Paragraph("BUHOS TOURS", titulo_principal))
    story.append(Paragraph(
        f"Auditoría Metodológica: Lista de Cotejo de Viabilidad Operativa | Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        subtitulo
    ))

    # Resumen Ejecutivo
    story.append(Paragraph("1. RESUMEN DE VIABILIDAD OPERATIVA", seccion_heading))
    res = cotejo_data["resumen"]
    filas_resumen = [
        [
            Paragraph("<b>Métrica Metodológica</b>", estilo_celda_header),
            Paragraph("<b>Resultado</b>", estilo_celda_header),
            Paragraph("<b>Métrica Metodológica</b>", estilo_celda_header),
            Paragraph("<b>Resultado</b>", estilo_celda_header),
        ],
        [
            Paragraph("Total Itinerarios Evaluados", estilo_celda),
            Paragraph(str(res["total_evaluados"]), estilo_celda),
            Paragraph("Tiempo Promedio Motor (NSGA-II)", estilo_celda),
            Paragraph(f"{res['tiempo_promedio_nsga2']} s", estilo_celda),
        ],
        [
            Paragraph("Itinerarios Sin Conflictos", estilo_celda),
            Paragraph(str(res["viables"]), estilo_celda),
            Paragraph("Hipervolumen Promedio (HV)", estilo_celda),
            Paragraph(str(res["hipervolumen_promedio"]), estilo_celda),
        ],
        [
            Paragraph("Itinerarios Con Conflictos", estilo_celda),
            Paragraph(str(res["con_conflictos"]), estilo_celda),
            Paragraph("Generational Distance (GD)", estilo_celda),
            Paragraph(str(res["gd_promedio"]), estilo_celda),
        ],
        [
            Paragraph("<b>Porcentaje de Viabilidad Operativa</b>", estilo_celda),
            Paragraph(f"<b>{res['porcentaje_viabilidad']}%</b>", estilo_celda),
            Paragraph("Spread / Spacing Promedio", estilo_celda),
            Paragraph(str(res["spread_promedio"]), estilo_celda),
        ],
    ]
    tabla_resumen = Table(filas_resumen, colWidths=[150, 120, 150, 120])
    tabla_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))
    story.append(tabla_resumen)
    story.append(Spacer(1, 10))

    # Cumplimiento por Criterio C1-C4
    story.append(Paragraph("2. CONSOLIDADO DE CUMPLIMIENTO POR CRITERIO DICOTÓMICO", seccion_heading))
    filas_crit = [
        [
            Paragraph("Cód.", estilo_celda_header),
            Paragraph("Criterio Operativo", estilo_celda_header),
            Paragraph("Descripción de Validación", estilo_celda_header),
            Paragraph("Cumple (Sí)", estilo_celda_header),
            Paragraph("% Sí", estilo_celda_header),
            Paragraph("Falla (No)", estilo_celda_header),
            Paragraph("% No", estilo_celda_header),
        ]
    ]
    for c in cotejo_data["tabla_criterios"]:
        filas_crit.append([
            Paragraph(f"<b>{c['codigo']}</b>", estilo_celda),
            Paragraph(c["criterio"], estilo_celda),
            Paragraph(c["descripcion"], estilo_celda),
            Paragraph(str(c["si_count"]), estilo_celda),
            Paragraph(f"{c['si_pct']}%", estilo_celda),
            Paragraph(str(c["no_count"]), estilo_celda),
            Paragraph(f"{c['no_pct']}%", estilo_celda),
        ])
    tabla_crit = Table(filas_crit, colWidths=[30, 120, 190, 50, 50, 50, 50])
    tabla_crit.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (3, 1), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))
    story.append(tabla_crit)
    story.append(Spacer(1, 10))

    # Tabla de Itinerarios
    story.append(Paragraph("3. MATRIZ DETALLADA DE LA LISTA DE COTEJO POR ITINERARIO", seccion_heading))
    filas_itin = [
        [
            Paragraph("Código", estilo_celda_header),
            Paragraph("F. Ejecución", estilo_celda_header),
            Paragraph("F. Visita", estilo_celda_header),
            Paragraph("Paradas", estilo_celda_header),
            Paragraph("C1", estilo_celda_header),
            Paragraph("C2", estilo_celda_header),
            Paragraph("C3", estilo_celda_header),
            Paragraph("C4", estilo_celda_header),
            Paragraph("Estado", estilo_celda_header),
            Paragraph("Observaciones", estilo_celda_header),
        ]
    ]

    for it in cotejo_data["itinerarios"][:50]:  # Muestra hasta 50 itinerarios
        c1_str = "<font color='green'><b>SÍ</b></font>" if it["c1"] else "<font color='red'><b>NO</b></font>"
        c2_str = "<font color='green'><b>SÍ</b></font>" if it["c2"] else "<font color='red'><b>NO</b></font>"
        c3_str = "<font color='green'><b>SÍ</b></font>" if it["c3"] else "<font color='red'><b>NO</b></font>"
        c4_str = "<font color='green'><b>SÍ</b></font>" if it["c4"] else "<font color='red'><b>NO</b></font>"
        est_str = "<font color='#0284c7'><b>Viable</b></font>" if it["es_viable"] else "<font color='#dc2626'><b>Conflicto</b></font>"

        f_ejec_corta = str(it.get("fecha_ejecucion", it["fecha"]))
        f_vis_corta = str(it.get("fecha_visita", it["fecha"]))

        filas_itin.append([
            Paragraph(it["id_codigo"], estilo_celda),
            Paragraph(f_ejec_corta, estilo_celda),
            Paragraph(f_vis_corta, estilo_celda),
            Paragraph(str(it["paradas_count"]), estilo_celda),
            Paragraph(c1_str, estilo_celda),
            Paragraph(c2_str, estilo_celda),
            Paragraph(c3_str, estilo_celda),
            Paragraph(c4_str, estilo_celda),
            Paragraph(est_str, estilo_celda),
            Paragraph(it["observaciones"][:95] + ("..." if len(it["observaciones"]) > 95 else ""), estilo_celda),
        ])

    tabla_itin = Table(filas_itin, colWidths=[55, 65, 50, 32, 22, 22, 22, 22, 45, 205])
    tabla_itin.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0369a1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ALIGN', (2, 1), (7, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
    ]))
    story.append(tabla_itin)

    doc.build(story)
    pdf_buffer.seek(0)

    return Response(
        pdf_buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=lista_cotejo_viabilidad.pdf"},
    )
