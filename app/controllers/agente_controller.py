from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.decorators import agente_required

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
