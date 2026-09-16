from flask import Blueprint, redirect, url_for
from flask_login import login_required
from app.utils.decorators import admin_required

usuario_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@usuario_bp.route('/', methods=['GET'])
@login_required
@admin_required
def index():
    """Redirige al listado oficial de usuarios bajo el blueprint de administración"""
    return redirect(url_for('admin.usuarios'))
