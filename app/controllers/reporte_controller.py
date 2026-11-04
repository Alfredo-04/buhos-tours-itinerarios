import io
import csv
from datetime import datetime
from flask import Blueprint, render_template, Response, abort
from flask_login import login_required
from app.services.reporte_service import (
    obtener_metricas_negocio,
    obtener_metricas_algoritmo,
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
    Renderiza el Dashboard ejecutivo con métricas de negocio y académicas del NSGA-II.
    """
    metricas_negocio = obtener_metricas_negocio()
    metricas_algoritmo = obtener_metricas_algoritmo(limit=20)
    return render_template(
        'reportes/dashboard.html',
        metricas_negocio=metricas_negocio,
        metricas_algoritmo=metricas_algoritmo,
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
