from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.utils.decorators import turista_required

turista_bp = Blueprint('turista', __name__, url_prefix='/turista')

@turista_bp.route('/dashboard')
@login_required
@turista_required
def dashboard():
    return render_template('dashboards/turista.html', user=current_user)

@turista_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
@turista_required
def perfil():
    if request.method == 'POST':
        nombres = request.form.get('nombres', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        telefono = request.form.get('telefono', '').strip()

        if len(nombres) < 2 or len(apellidos) < 2:
            flash('Nombres y apellidos deben tener al menos 2 caracteres.', 'danger')
        else:
            current_user.nombres = nombres
            current_user.apellidos = apellidos
            if current_user.turista:
                current_user.turista.nombres = nombres
                current_user.turista.apellidos = apellidos
                current_user.turista.telefono = telefono
            db.session.commit()
            flash('Perfil actualizado con éxito.', 'success')
            return redirect(url_for('turista.perfil'))

    return render_template('perfil/turista.html', user=current_user)

@turista_bp.route('/desactivar-2fa', methods=['POST'])
@login_required
@turista_required
def desactivar_2fa():
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    current_user.two_factor_confirmed_at = None
    db.session.commit()
    flash('Autenticación de dos factores (2FA) desactivada correctamente.', 'info')
    return redirect(url_for('turista.perfil'))
