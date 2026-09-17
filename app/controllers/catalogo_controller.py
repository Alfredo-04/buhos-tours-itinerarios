from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services import atractivo_service, transporte_service, categoria_service

catalogo_bp = Blueprint('catalogo', __name__, url_prefix='/catalogo')

@catalogo_bp.route('/atractivos')
@login_required
def atractivos_list():
    """
    Catálogo de Atractivos Turísticos accesible para todos los roles autenticados.
    Permite búsqueda, filtrado por categoría y ordenamiento con paginación.
    """
    search_query = request.args.get('q', '').strip()
    categoria_id = request.args.get('categoria', '').strip()
    sort_by = request.args.get('sort', 'nombre_asc').strip()
    page = request.args.get('page', 1, type=int)

    categoria_id_int = int(categoria_id) if categoria_id.isdigit() else None

    pagination = atractivo_service.listar_atractivos(
        search_query=search_query,
        categoria_id=categoria_id_int,
        estado='activos',
        sort_by=sort_by,
        page=page,
        per_page=9
    )

    categorias = categoria_service.obtener_todas_activas()

    return render_template(
        'catalogo/atractivos_list.html',
        pagination=pagination,
        atractivos=pagination.items,
        categorias=categorias,
        search_query=search_query,
        categoria_id=categoria_id,
        sort_by=sort_by,
        user=current_user
    )

@catalogo_bp.route('/atractivos/<int:id_atractivo>')
@login_required
def atractivo_detail(id_atractivo):
    """
    Detalle completo de un atractivo turístico adaptado según el rol del usuario:
    - Turista: Información turística, visualización amigable, oculta datos de proveedor/costo interno.
    - Agente: Información técnica y operativa, enlace a edición parcial.
    - Admin: Información completa y enlace a edición administrativa/eliminación.
    """
    atractivo = atractivo_service.obtener_atractivo(id_atractivo, include_deleted=(current_user.rol.nombre == 'admin'))
    if not atractivo:
        flash('El atractivo turístico solicitado no existe o no se encuentra disponible.', 'warning')
        return redirect(url_for('catalogo.atractivos_list'))

    return render_template(
        'catalogo/atractivo_detail.html',
        atractivo=atractivo,
        user=current_user
    )

@catalogo_bp.route('/transportes')
@login_required
def transportes_list():
    """
    Catálogo de Medios de Transporte accesible para todos los roles autenticados.
    Permite búsqueda y filtrado por tipo ('Privado' / 'Público').
    """
    search_query = request.args.get('q', '').strip()
    tipo_filtro = request.args.get('tipo', '').strip()
    sort_by = request.args.get('sort', 'nombre_asc').strip()
    page = request.args.get('page', 1, type=int)

    pagination = transporte_service.listar_transportes(
        search_query=search_query,
        tipo_filtro=tipo_filtro,
        estado='activos',
        sort_by=sort_by,
        page=page,
        per_page=9
    )

    return render_template(
        'catalogo/transportes_list.html',
        pagination=pagination,
        transportes=pagination.items,
        search_query=search_query,
        tipo_filtro=tipo_filtro,
        sort_by=sort_by,
        user=current_user
    )

@catalogo_bp.route('/transportes/<int:id_transporte>')
@login_required
def transporte_detail(id_transporte):
    """
    Detalle de un medio de transporte adaptado por rol.
    """
    transporte = transporte_service.obtener_transporte(id_transporte, include_deleted=(current_user.rol.nombre == 'admin'))
    if not transporte:
        flash('El medio de transporte solicitado no existe o no se encuentra disponible.', 'warning')
        return redirect(url_for('catalogo.transportes_list'))

    return render_template(
        'catalogo/transporte_detail.html',
        transporte=transporte,
        user=current_user
    )
