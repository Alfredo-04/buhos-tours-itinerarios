from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.decorators import agente_required
from app.services import atractivo_service, transporte_service

agente_bp = Blueprint('agente', __name__, url_prefix='/agente')

@agente_bp.route('/dashboard')
@login_required
@agente_required
def dashboard():
    return render_template('dashboards/agente.html', user=current_user)

@agente_bp.route('/perfil')
@login_required
@agente_required
def perfil():
    return render_template('perfil/agente.html', user=current_user)

# ==============================================================================
# EDICIÓN PARCIAL DE ATRACTIVOS (SOLO CAMPOS OPERATIVOS)
# ==============================================================================
@agente_bp.route('/atractivos/<int:id_atractivo>/editar', methods=['GET', 'POST'])
@login_required
@agente_required
def atractivo_editar_parcial(id_atractivo):
    atractivo = atractivo_service.obtener_atractivo(id_atractivo, include_deleted=False)
    if not atractivo:
        flash('Atractivo turístico no encontrado o se encuentra inactivo.', 'warning')
        return redirect(url_for('catalogo.atractivos_list'))

    if request.method == 'POST':
        success, message, _ = atractivo_service.actualizar_atractivo(id_atractivo, request.form, rol='agente')
        if success:
            flash(message, 'success')
            return redirect(url_for('catalogo.atractivo_detail', id_atractivo=id_atractivo))
        else:
            flash(message, 'danger')
            return render_template(
                'agente/atractivos/edit.html',
                atractivo=atractivo,
                form_data=request.form
            )

    return render_template(
        'agente/atractivos/edit.html',
        atractivo=atractivo,
        form_data={
            'descripcion': atractivo.descripcion or '',
            'direccion': atractivo.direccion or '',
            'latitud': str(atractivo.latitud) if atractivo.latitud is not None else '',
            'longitud': str(atractivo.longitud) if atractivo.longitud is not None else '',
            'horario_apertura': atractivo.horario_apertura.strftime('%H:%M') if atractivo.horario_apertura else '',
            'horario_cierre': atractivo.horario_cierre.strftime('%H:%M') if atractivo.horario_cierre else '',
            'tiempo_visita_estimado': str(atractivo.tiempo_visita_estimado) if atractivo.tiempo_visita_estimado else '',
            'dias_cerrado': atractivo.dias_cerrado or ''
        }
    )

# ==============================================================================
# EDICIÓN PARCIAL DE TRANSPORTES (SOLO CAMPOS OPERATIVOS)
# ==============================================================================
@agente_bp.route('/transportes/<int:id_transporte>/editar', methods=['GET', 'POST'])
@login_required
@agente_required
def transporte_editar_parcial(id_transporte):
    transporte = transporte_service.obtener_transporte(id_transporte, include_deleted=False)
    if not transporte:
        flash('Medio de transporte no encontrado o se encuentra inactivo.', 'warning')
        return redirect(url_for('catalogo.transportes_list'))

    if request.method == 'POST':
        success, message, _ = transporte_service.actualizar_transporte(id_transporte, request.form, rol='agente')
        if success:
            flash(message, 'success')
            return redirect(url_for('catalogo.transporte_detail', id_transporte=id_transporte))
        else:
            flash(message, 'danger')
            return render_template(
                'agente/transportes/edit.html',
                transporte=transporte,
                form_data=request.form
            )

    return render_template(
        'agente/transportes/edit.html',
        transporte=transporte,
        form_data={
            'capacidad': str(transporte.capacidad) if transporte.capacidad else '',
            'horario_inicio': transporte.horario_inicio.strftime('%H:%M') if transporte.horario_inicio else '',
            'horario_fin': transporte.horario_fin.strftime('%H:%M') if transporte.horario_fin else '',
            'tiempo_recorrido_base': str(transporte.tiempo_recorrido_base) if transporte.tiempo_recorrido_base else ''
        }
    )
