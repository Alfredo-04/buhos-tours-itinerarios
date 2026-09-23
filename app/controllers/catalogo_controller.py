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

@catalogo_bp.route('/atractivos/mapa')
@login_required
def atractivos_mapa():
    """
    Vista geográfica interactiva con Leaflet de todos los atractivos turísticos activos.
    Accesible para todos los roles autenticados.
    """
    from app.models.atractivo import Atractivo
    import json

    atractivos_query = Atractivo.query.filter(
        Atractivo.deleted_at.is_(None),
        Atractivo.latitud.isnot(None),
        Atractivo.longitud.isnot(None)
    ).all()

    atractivos_data = []
    for a in atractivos_query:
        atractivos_data.append({
            'id_atractivo': a.id_atractivo,
            'nombre': a.nombre,
            'latitud': float(a.latitud),
            'longitud': float(a.longitud),
            'categoria': a.categoria.nombre if a.categoria else 'General',
            'costo_entrada': float(a.costo_entrada) if a.costo_entrada is not None else 0.0,
            'direccion': a.direccion or '',
            'imagen_url': a.imagen_url or ''
        })

    return render_template(
        'catalogo/atractivos_mapa.html',
        atractivos=atractivos_query,
        atractivos_json=json.dumps(atractivos_data),
        user=current_user
    )

@catalogo_bp.route('/atractivos/<int:id_atractivo>/mapa')
@login_required
def atractivo_mapa(id_atractivo):
    """
    Vista geográfica interactiva con Leaflet enfocada en un solo atractivo turístico.
    Accesible para todos los roles autenticados.
    """
    import json

    atractivo = atractivo_service.obtener_atractivo(id_atractivo, include_deleted=(current_user.rol.nombre == 'admin'))
    if not atractivo:
        flash('El atractivo turístico solicitado no existe o no se encuentra disponible.', 'warning')
        return redirect(url_for('catalogo.atractivos_list'))

    if not atractivo.latitud or not atractivo.longitud:
        flash(f"El atractivo '{atractivo.nombre}' no tiene coordenadas geográficas registradas para visualizar en el mapa.", 'info')
        return redirect(url_for('catalogo.atractivo_detail', id_atractivo=id_atractivo))

    atractivo_data = {
        'id_atractivo': atractivo.id_atractivo,
        'nombre': atractivo.nombre,
        'latitud': float(atractivo.latitud),
        'longitud': float(atractivo.longitud),
        'categoria': atractivo.categoria.nombre if atractivo.categoria else 'General',
        'costo_entrada': float(atractivo.costo_entrada) if atractivo.costo_entrada is not None else 0.0,
        'direccion': atractivo.direccion or '',
        'imagen_url': atractivo.imagen_url or ''
    }

    return render_template(
        'catalogo/atractivo_mapa.html',
        atractivo=atractivo,
        atractivo_json=json.dumps(atractivo_data),
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
