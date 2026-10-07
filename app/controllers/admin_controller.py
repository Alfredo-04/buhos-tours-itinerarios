from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from app.utils.decorators import admin_required
from app.services import (
    usuario_service, atractivo_service, transporte_service,
    categoria_service, subcategoria_service, proveedor_service
)
from app.models.rol import Rol

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ==============================================================================
# DASHBOARD
# ==============================================================================
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats_usuarios = usuario_service.get_total_estadisticas()
    stats_atractivos = atractivo_service.get_estadisticas_atractivos()
    stats_transportes = transporte_service.get_estadisticas_transportes()
    return render_template(
        'dashboards/admin.html',
        user=current_user,
        stats=stats_usuarios,
        stats_atractivos=stats_atractivos,
        stats_transportes=stats_transportes
    )

# ==============================================================================
# GESTIÓN DE USUARIOS
# ==============================================================================
@admin_bp.route('/usuarios')
@login_required
@admin_required
def usuarios():
    search_query = request.args.get('q', '').strip()
    rol_filtro = request.args.get('rol', '').strip()
    estado_filtro = request.args.get('estado', 'activos').strip()
    sort_by = request.args.get('sort', 'id_asc').strip()
    page = request.args.get('page', 1, type=int)

    pagination = usuario_service.get_usuarios_paginados(
        search_query=search_query,
        rol_filtro=rol_filtro,
        estado_filtro=estado_filtro,
        sort_by=sort_by,
        page=page,
        per_page=10
    )
    stats = usuario_service.get_total_estadisticas()
    roles = Rol.query.all()

    temp_password = session.pop('last_temp_password', None)
    temp_user_email = session.pop('last_temp_user_email', None)

    return render_template(
        'admin/usuarios/list.html',
        pagination=pagination,
        usuarios=pagination.items,
        stats=stats,
        roles=roles,
        search_query=search_query,
        rol_filtro=rol_filtro,
        estado_filtro=estado_filtro,
        sort_by=sort_by,
        temp_password=temp_password,
        temp_user_email=temp_user_email
    )

@admin_bp.route('/usuarios/<int:id_usuario>')
@login_required
@admin_required
def usuario_detalle(id_usuario):
    usuario = usuario_service.get_usuario_by_id(id_usuario)
    if not usuario:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('admin.usuarios'))
    return render_template('admin/usuarios/detail.html', usuario=usuario)

@admin_bp.route('/usuarios/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def usuario_crear():
    roles = Rol.query.all()
    if request.method == 'POST':
        success, message, nuevo_usuario, temp_pass = usuario_service.create_user_by_admin(request.form)
        if success:
            flash(f"Usuario {nuevo_usuario.nombre_completo} creado exitosamente.", 'success')
            if temp_pass:
                session['last_temp_password'] = temp_pass
                session['last_temp_user_email'] = nuevo_usuario.email
            return redirect(url_for('admin.usuarios'))
        else:
            flash(message, 'danger')
            return render_template('admin/usuarios/create.html', roles=roles, form_data=request.form)

    return render_template('admin/usuarios/create.html', roles=roles, form_data={})

@admin_bp.route('/usuarios/<int:id_usuario>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def usuario_editar(id_usuario):
    usuario = usuario_service.get_usuario_by_id(id_usuario)
    if not usuario:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('admin.usuarios'))

    roles = Rol.query.all()
    if request.method == 'POST':
        success, message, _ = usuario_service.update_user_by_admin(id_usuario, request.form)
        if success:
            flash(message, 'success')
            return redirect(url_for('admin.usuarios'))
        else:
            flash(message, 'danger')
            return render_template('admin/usuarios/edit.html', usuario=usuario, roles=roles, form_data=request.form)

    return render_template('admin/usuarios/edit.html', usuario=usuario, roles=roles, form_data={
        'nombres': usuario.nombres,
        'apellidos': usuario.apellidos,
        'email': usuario.email,
        'rol': usuario.rol.nombre if usuario.rol else ''
    })

@admin_bp.route('/usuarios/<int:id_usuario>/eliminar', methods=['POST'])
@login_required
@admin_required
def usuario_eliminar(id_usuario):
    if current_user.id_usuario == id_usuario:
        flash('No puedes desactivar tu propia cuenta de administrador.', 'danger')
        return redirect(url_for('admin.usuarios'))

    success, message = usuario_service.soft_delete_user(id_usuario)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/<int:id_usuario>/restaurar', methods=['POST'])
@login_required
@admin_required
def usuario_restaurar(id_usuario):
    success, message = usuario_service.restore_user(id_usuario)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.usuarios', estado='activos'))

@admin_bp.route('/usuarios/<int:id_usuario>/reset-password', methods=['POST'])
@login_required
@admin_required
def usuario_reset_password(id_usuario):
    success, message, temp_pass = usuario_service.reset_password_by_admin(id_usuario)
    if success:
        usuario = usuario_service.get_usuario_by_id(id_usuario)
        flash(message, 'success')
        session['last_temp_password'] = temp_pass
        session['last_temp_user_email'] = usuario.email if usuario else ''
    else:
        flash(message, 'danger')
    return redirect(url_for('admin.usuarios'))


# ==============================================================================
# GESTIÓN DE ATRACTIVOS TURÍSTICOS
# ==============================================================================
@admin_bp.route('/atractivos')
@login_required
@admin_required
def atractivos():
    search_query = request.args.get('q', '').strip()
    categoria_filtro = request.args.get('categoria', '').strip()
    subcategoria_filtro = request.args.get('subcategoria', '').strip()
    estado_filtro = request.args.get('estado', 'activos').strip()
    sort_by = request.args.get('sort', 'id_asc').strip()
    page = request.args.get('page', 1, type=int)

    cat_id = int(categoria_filtro) if categoria_filtro.isdigit() else None
    subcat_id = int(subcategoria_filtro) if subcategoria_filtro.isdigit() else None

    pagination = atractivo_service.listar_atractivos(
        search_query=search_query,
        subcategoria_id=subcat_id,
        categoria_id=cat_id,
        estado=estado_filtro,
        sort_by=sort_by,
        page=page,
        per_page=10
    )
    categorias = categoria_service.obtener_todas_activas()
    subcategorias = subcategoria_service.obtener_todas_activas()
    stats = atractivo_service.get_estadisticas_atractivos()

    return render_template(
        'admin/atractivos/list.html',
        pagination=pagination,
        atractivos=pagination.items,
        categorias=categorias,
        subcategorias=subcategorias,
        stats=stats,
        search_query=search_query,
        categoria_filtro=categoria_filtro,
        subcategoria_filtro=subcategoria_filtro,
        estado_filtro=estado_filtro,
        sort_by=sort_by
    )

@admin_bp.route('/atractivos/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def atractivo_crear():
    categorias = categoria_service.obtener_todas_activas()
    subcategorias = subcategoria_service.obtener_todas_activas()
    proveedores = proveedor_service.obtener_todos_activos()

    if request.method == 'POST':
        imagen_file = request.files.get('imagen')
        success, message, nuevo = atractivo_service.crear_atractivo(request.form, imagen_file=imagen_file)
        if success:
            flash(message, 'success')
            return redirect(url_for('admin.atractivos'))
        else:
            flash(message, 'danger')
            return render_template(
                'admin/atractivos/create.html',
                categorias=categorias,
                subcategorias=subcategorias,
                proveedores=proveedores,
                form_data=request.form
            )

    return render_template(
        'admin/atractivos/create.html',
        categorias=categorias,
        subcategorias=subcategorias,
        proveedores=proveedores,
        form_data={}
    )

@admin_bp.route('/atractivos/<int:id_atractivo>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def atractivo_editar(id_atractivo):
    atractivo = atractivo_service.obtener_atractivo(id_atractivo, include_deleted=True)
    if not atractivo:
        flash('Atractivo turístico no encontrado.', 'danger')
        return redirect(url_for('admin.atractivos'))

    categorias = categoria_service.obtener_todas_activas()
    subcategorias = subcategoria_service.obtener_todas_activas()
    proveedores = proveedor_service.obtener_todos_activos()

    if request.method == 'POST':
        imagen_file = request.files.get('imagen')
        success, message, _ = atractivo_service.actualizar_atractivo(id_atractivo, request.form, rol='admin', imagen_file=imagen_file)
        if success:
            flash(message, 'success')
            return redirect(url_for('admin.atractivos'))
        else:
            flash(message, 'danger')
            return render_template(
                'admin/atractivos/edit.html',
                atractivo=atractivo,
                categorias=categorias,
                subcategorias=subcategorias,
                proveedores=proveedores,
                form_data=request.form
            )

    return render_template(
        'admin/atractivos/edit.html',
        atractivo=atractivo,
        categorias=categorias,
        subcategorias=subcategorias,
        proveedores=proveedores,
        form_data={
            'nombre': atractivo.nombre,
            'descripcion': atractivo.descripcion,
            'direccion': atractivo.direccion,
            'latitud': str(atractivo.latitud) if atractivo.latitud is not None else '',
            'longitud': str(atractivo.longitud) if atractivo.longitud is not None else '',
            'horario_apertura': atractivo.horario_apertura.strftime('%H:%M') if atractivo.horario_apertura else '',
            'horario_cierre': atractivo.horario_cierre.strftime('%H:%M') if atractivo.horario_cierre else '',
            'costo_entrada': str(atractivo.costo_entrada) if atractivo.costo_entrada is not None else '0.00',
            'tiempo_visita_estimado': str(atractivo.tiempo_visita_estimado) if atractivo.tiempo_visita_estimado else '',
            'dias_cerrado': atractivo.dias_cerrado or '',
            'id_subcategoria': atractivo.id_subcategoria,
            'id_categoria': atractivo.id_categoria,
            'id_proveedor': atractivo.id_proveedor,
            'imagen_url': atractivo.imagen_url or '',
            'fecha_inicio': atractivo.fecha_inicio.strftime('%Y-%m-%d') if atractivo.fecha_inicio else '',
            'fecha_fin': atractivo.fecha_fin.strftime('%Y-%m-%d') if atractivo.fecha_fin else '',
            'afecta_rutas': atractivo.afecta_rutas,
            'sensible_al_clima': atractivo.sensible_al_clima,
            'tipo_clima_ideal': atractivo.tipo_clima_ideal or ''
        }
    )

@admin_bp.route('/atractivos/<int:id_atractivo>')
@login_required
@admin_required
def atractivo_detalle(id_atractivo):
    atractivo = atractivo_service.obtener_atractivo(id_atractivo, include_deleted=True)
    if not atractivo:
        flash('Atractivo turístico no encontrado.', 'danger')
        return redirect(url_for('admin.atractivos'))
    return render_template('admin/atractivos/detail.html', atractivo=atractivo)

@admin_bp.route('/atractivos/<int:id_atractivo>/eliminar', methods=['POST'])
@login_required
@admin_required
def atractivo_eliminar(id_atractivo):
    success, message = atractivo_service.eliminar_atractivo(id_atractivo)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.atractivos'))

@admin_bp.route('/atractivos/<int:id_atractivo>/restaurar', methods=['POST'])
@login_required
@admin_required
def atractivo_restaurar(id_atractivo):
    success, message = atractivo_service.restaurar_atractivo(id_atractivo)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.atractivos', estado='activos'))


# ==============================================================================
# GESTIÓN DE CATEGORÍAS
# ==============================================================================
@admin_bp.route('/categorias')
@login_required
@admin_required
def categorias():
    search_query = request.args.get('q', '').strip()
    estado_filtro = request.args.get('estado', 'activos').strip()
    sort_by = request.args.get('sort', 'nombre_asc').strip()
    page = request.args.get('page', 1, type=int)

    pagination = categoria_service.listar_categorias(
        search_query=search_query,
        estado=estado_filtro,
        sort_by=sort_by,
        page=page,
        per_page=10
    )
    stats = categoria_service.get_estadisticas_categorias()

    return render_template(
        'admin/categorias/list.html',
        pagination=pagination,
        categorias=pagination.items,
        stats=stats,
        search_query=search_query,
        estado_filtro=estado_filtro,
        sort_by=sort_by
    )

@admin_bp.route('/categorias/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def categoria_crear():
    if request.method == 'POST':
        success, message, nueva = categoria_service.crear_categoria(request.form)
        if success:
            flash(message, 'success')
            return redirect(url_for('admin.categorias'))
        else:
            flash(message, 'danger')
            return render_template('admin/categorias/create.html', form_data=request.form)
    return render_template('admin/categorias/create.html', form_data={})

@admin_bp.route('/categorias/<int:id_categoria>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def categoria_editar(id_categoria):
    cat = categoria_service.obtener_categoria(id_categoria)
    if not cat:
        flash('Categoría no encontrada.', 'danger')
        return redirect(url_for('admin.categorias'))

    if request.method == 'POST':
        success, message, _ = categoria_service.actualizar_categoria(id_categoria, request.form)
        if success:
            flash(message, 'success')
            return redirect(url_for('admin.categorias'))
        else:
            flash(message, 'danger')
            return render_template('admin/categorias/edit.html', categoria=cat, form_data=request.form)

    return render_template('admin/categorias/edit.html', categoria=cat, form_data={
        'nombre': cat.nombre,
        'descripcion': cat.descripcion or ''
    })

@admin_bp.route('/categorias/<int:id_categoria>/eliminar', methods=['POST'])
@login_required
@admin_required
def categoria_eliminar(id_categoria):
    success, message = categoria_service.eliminar_categoria(id_categoria)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.categorias'))

@admin_bp.route('/categorias/<int:id_categoria>/restaurar', methods=['POST'])
@login_required
@admin_required
def categoria_restaurar(id_categoria):
    success, message = categoria_service.restaurar_categoria(id_categoria)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.categorias', estado='activos'))

@admin_bp.route('/api/categorias/crear-rapida', methods=['POST'])
@login_required
@admin_required
def api_categoria_crear_rapida():
    """Endpoint AJAX para crear categoría rápidamente desde el modal de atractivo."""
    data = request.get_json() if request.is_json else request.form
    success, message, nueva_cat = categoria_service.crear_categoria(data)
    if success:
        return jsonify({
            'success': True,
            'message': message,
            'categoria': {
                'id_categoria': nueva_cat.id_categoria,
                'nombre': nueva_cat.nombre
            }
        }), 201
    return jsonify({'success': False, 'message': message}), 400


# ==============================================================================
# GESTIÓN DE SUBCATEGORÍAS
# ==============================================================================
@admin_bp.route('/subcategorias')
@login_required
@admin_required
def subcategorias():
    search_query = request.args.get('q', '').strip()
    categoria_id = request.args.get('categoria_id', type=int)
    estado_filtro = request.args.get('estado', 'activos')
    sort_by = request.args.get('sort', 'nombre_asc')
    page = request.args.get('page', 1, type=int)

    pagination = subcategoria_service.listar_subcategorias(
        categoria_id=categoria_id,
        search_query=search_query,
        estado=estado_filtro,
        sort_by=sort_by,
        page=page,
        per_page=10
    )
    stats = subcategoria_service.get_estadisticas_subcategorias()
    categorias_activas = categoria_service.obtener_todas_activas()

    return render_template(
        'admin/subcategorias/list.html',
        subcategorias=pagination.items,
        pagination=pagination,
        stats=stats,
        categorias=categorias_activas,
        categoria_id_filtro=categoria_id,
        search_query=search_query,
        estado_filtro=estado_filtro,
        sort_by=sort_by
    )

@admin_bp.route('/subcategorias/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def subcategoria_crear():
    categorias_activas = categoria_service.obtener_todas_activas()
    if request.method == 'POST':
        success, message, nueva = subcategoria_service.crear_subcategoria(request.form)
        if success:
            flash(message, 'success')
            return redirect(url_for('admin.subcategorias'))
        else:
            flash(message, 'danger')
            return render_template('admin/subcategorias/create.html', categorias=categorias_activas, form_data=request.form)
    return render_template('admin/subcategorias/create.html', categorias=categorias_activas, form_data={})

@admin_bp.route('/subcategorias/<int:id_subcategoria>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def subcategoria_editar(id_subcategoria):
    subcat = subcategoria_service.obtener_subcategoria(id_subcategoria)
    if not subcat:
        flash('Subcategoría no encontrada.', 'danger')
        return redirect(url_for('admin.subcategorias'))

    categorias_activas = categoria_service.obtener_todas_activas()

    if request.method == 'POST':
        success, message, _ = subcategoria_service.actualizar_subcategoria(id_subcategoria, request.form)
        if success:
            flash(message, 'success')
            return redirect(url_for('admin.subcategorias'))
        else:
            flash(message, 'danger')
            return render_template('admin/subcategorias/edit.html', subcategoria=subcat, categorias=categorias_activas, form_data=request.form)

    return render_template('admin/subcategorias/edit.html', subcategoria=subcat, categorias=categorias_activas, form_data={
        'nombre': subcat.nombre,
        'descripcion': subcat.descripcion or '',
        'id_categoria': subcat.id_categoria
    })

@admin_bp.route('/subcategorias/<int:id_subcategoria>/eliminar', methods=['POST'])
@login_required
@admin_required
def subcategoria_eliminar(id_subcategoria):
    success, message = subcategoria_service.eliminar_subcategoria(id_subcategoria)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.subcategorias'))

@admin_bp.route('/subcategorias/<int:id_subcategoria>/restaurar', methods=['POST'])
@login_required
@admin_required
def subcategoria_restaurar(id_subcategoria):
    success, message = subcategoria_service.restaurar_subcategoria(id_subcategoria)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.subcategorias', estado='activos'))

@admin_bp.route('/api/subcategorias/crear-rapida', methods=['POST'])
@login_required
@admin_required
def api_subcategoria_crear_rapida():
    data = request.get_json() if request.is_json else request.form
    success, message, nueva = subcategoria_service.crear_subcategoria(data)
    if success:
        return jsonify({
            'success': True,
            'message': message,
            'subcategoria': {
                'id_subcategoria': nueva.id_subcategoria,
                'nombre': nueva.nombre,
                'id_categoria': nueva.id_categoria,
                'categoria_nombre': nueva.categoria.nombre if nueva.categoria else ''
            }
        }), 201
    return jsonify({'success': False, 'message': message}), 400



# ==============================================================================
# GESTIÓN DE PROVEEDORES
# ==============================================================================
@admin_bp.route('/proveedores')
@login_required
@admin_required
def proveedores():
    search_query = request.args.get('q', '').strip()
    estado_filtro = request.args.get('estado', 'activos').strip()
    sort_by = request.args.get('sort', 'razon_social_asc').strip()
    page = request.args.get('page', 1, type=int)

    pagination = proveedor_service.listar_proveedores(
        search_query=search_query,
        estado=estado_filtro,
        sort_by=sort_by,
        page=page,
        per_page=10
    )
    stats = proveedor_service.get_estadisticas_proveedores()

    return render_template(
        'admin/proveedores/list.html',
        pagination=pagination,
        proveedores=pagination.items,
        stats=stats,
        search_query=search_query,
        estado_filtro=estado_filtro,
        sort_by=sort_by
    )

@admin_bp.route('/proveedores/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def proveedor_crear():
    if request.method == 'POST':
        success, message, nuevo = proveedor_service.crear_proveedor(request.form)
        if success:
            flash(message, 'success')
            return redirect(url_for('admin.proveedores'))
        else:
            flash(message, 'danger')
            return render_template('admin/proveedores/create.html', form_data=request.form)
    return render_template('admin/proveedores/create.html', form_data={})

@admin_bp.route('/proveedores/<int:id_proveedor>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def proveedor_editar(id_proveedor):
    prov = proveedor_service.obtener_proveedor(id_proveedor)
    if not prov:
        flash('Proveedor no encontrado.', 'danger')
        return redirect(url_for('admin.proveedores'))

    if request.method == 'POST':
        success, message, _ = proveedor_service.actualizar_proveedor(id_proveedor, request.form)
        if success:
            flash(message, 'success')
            return redirect(url_for('admin.proveedores'))
        else:
            flash(message, 'danger')
            return render_template('admin/proveedores/edit.html', proveedor=prov, form_data=request.form)

    return render_template('admin/proveedores/edit.html', proveedor=prov, form_data={
        'razon_social': prov.razon_social,
        'tipo': prov.tipo or '',
        'contacto_nombre': prov.contacto_nombre or '',
        'contacto_telefono': prov.contacto_telefono or '',
        'contacto_email': prov.contacto_email or '',
        'tarifa_especial': str(prov.tarifa_especial) if prov.tarifa_especial is not None else '',
        'observaciones': prov.observaciones or ''
    })

@admin_bp.route('/proveedores/<int:id_proveedor>/eliminar', methods=['POST'])
@login_required
@admin_required
def proveedor_eliminar(id_proveedor):
    success, message = proveedor_service.eliminar_proveedor(id_proveedor)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.proveedores'))

@admin_bp.route('/proveedores/<int:id_proveedor>/restaurar', methods=['POST'])
@login_required
@admin_required
def proveedor_restaurar(id_proveedor):
    success, message = proveedor_service.restaurar_proveedor(id_proveedor)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.proveedores', estado='activos'))

@admin_bp.route('/api/proveedores/crear-rapida', methods=['POST'])
@login_required
@admin_required
def api_proveedor_crear_rapida():
    """Endpoint AJAX para crear proveedor rápidamente desde el modal de atractivo."""
    data = request.get_json() if request.is_json else request.form
    success, message, nuevo_prov = proveedor_service.crear_proveedor(data)
    if success:
        return jsonify({
            'success': True,
            'message': message,
            'proveedor': {
                'id_proveedor': nuevo_prov.id_proveedor,
                'razon_social': nuevo_prov.razon_social
            }
        }), 201
    return jsonify({'success': False, 'message': message}), 400


# ==============================================================================
# GESTIÓN DE MEDIOS DE TRANSPORTE
# ==============================================================================
@admin_bp.route('/transportes')
@login_required
@admin_required
def transportes():
    search_query = request.args.get('q', '').strip()
    tipo_filtro = request.args.get('tipo', '').strip()
    estado_filtro = request.args.get('estado', 'activos').strip()
    sort_by = request.args.get('sort', 'id_asc').strip()
    page = request.args.get('page', 1, type=int)

    pagination = transporte_service.listar_transportes(
        search_query=search_query,
        tipo_filtro=tipo_filtro,
        estado=estado_filtro,
        sort_by=sort_by,
        page=page,
        per_page=10
    )
    stats = transporte_service.get_estadisticas_transportes()

    return render_template(
        'admin/transportes/list.html',
        pagination=pagination,
        transportes=pagination.items,
        stats=stats,
        search_query=search_query,
        tipo_filtro=tipo_filtro,
        estado_filtro=estado_filtro,
        sort_by=sort_by
    )

@admin_bp.route('/transportes/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def transporte_crear():
    if request.method == 'POST':
        success, message, nuevo = transporte_service.crear_transporte(request.form)
        if success:
            flash(message, 'success')
            return redirect(url_for('admin.transportes'))
        else:
            flash(message, 'danger')
            return render_template('admin/transportes/create.html', form_data=request.form)
    return render_template('admin/transportes/create.html', form_data={})

@admin_bp.route('/transportes/<int:id_transporte>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def transporte_editar(id_transporte):
    transporte = transporte_service.obtener_transporte(id_transporte, include_deleted=True)
    if not transporte:
        flash('Transporte no encontrado.', 'danger')
        return redirect(url_for('admin.transportes'))

    if request.method == 'POST':
        success, message, _ = transporte_service.actualizar_transporte(id_transporte, request.form, rol='admin')
        if success:
            flash(message, 'success')
            return redirect(url_for('admin.transportes'))
        else:
            flash(message, 'danger')
            return render_template('admin/transportes/edit.html', transporte=transporte, form_data=request.form)

    return render_template('admin/transportes/edit.html', transporte=transporte, form_data={
        'nombre': transporte.nombre,
        'tipo': transporte.tipo,
        'capacidad': str(transporte.capacidad) if transporte.capacidad else '',
        'horario_inicio': transporte.horario_inicio.strftime('%H:%M') if transporte.horario_inicio else '',
        'horario_fin': transporte.horario_fin.strftime('%H:%M') if transporte.horario_fin else '',
        'costo': str(transporte.costo) if transporte.costo is not None else '0.00',
        'costo_por_tramo': str(transporte.costo) if transporte.costo is not None else '0.00',
        'tipo_costo': transporte.tipo_costo,
        'velocidad_promedio_kmh': str(transporte.velocidad_promedio_kmh) if transporte.velocidad_promedio_kmh is not None else '30.0'
    })

@admin_bp.route('/transportes/<int:id_transporte>')
@login_required
@admin_required
def transporte_detalle(id_transporte):
    transporte = transporte_service.obtener_transporte(id_transporte, include_deleted=True)
    if not transporte:
        flash('Transporte no encontrado.', 'danger')
        return redirect(url_for('admin.transportes'))
    return render_template('admin/transportes/detail.html', transporte=transporte)

@admin_bp.route('/transportes/<int:id_transporte>/eliminar', methods=['POST'])
@login_required
@admin_required
def transporte_eliminar(id_transporte):
    success, message = transporte_service.eliminar_transporte(id_transporte)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.transportes'))

@admin_bp.route('/transportes/<int:id_transporte>/restaurar', methods=['POST'])
@login_required
@admin_required
def transporte_restaurar(id_transporte):
    success, message = transporte_service.restaurar_transporte(id_transporte)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.transportes', estado='activos'))
