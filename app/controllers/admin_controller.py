from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.utils.decorators import admin_required
from app.services import usuario_service
from app.models.rol import Rol

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = usuario_service.get_total_estadisticas()
    return render_template('dashboards/admin.html', user=current_user, stats=stats)

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

    # Recuperar de la sesión temporal password si se acaba de crear o resetear
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
                # Almacenar en sesión temporalmente para mostrar modal en el listado
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
