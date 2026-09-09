from flask import Blueprint, render_template, request
from flask_login import login_required
from app.utils.decorators import admin_required
from app.services.usuario_service import get_usuarios_filtrados, get_total_estadisticas

usuario_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@usuario_bp.route('/', methods=['GET'])
@login_required
@admin_required
def index():
    search_query = request.args.get('q', '').strip()
    rol_filtro = request.args.get('rol', '').strip()
    sort_by = request.args.get('sort', 'id_asc').strip()

    usuarios = get_usuarios_filtrados(
        search_query=search_query,
        rol_filtro=rol_filtro,
        sort_by=sort_by
    )
    stats = get_total_estadisticas()

    return render_template(
        'usuarios/index.html',
        usuarios=usuarios,
        stats=stats,
        search_query=search_query,
        rol_filtro=rol_filtro,
        sort_by=sort_by
    )
