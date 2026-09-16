from datetime import datetime, timedelta
import re
from sqlalchemy import or_
from app import db
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.turista import Turista
from app.services import email_service
from app.services.auth_service import generate_random_password

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

def get_usuarios_paginados(
    search_query: str = '',
    rol_filtro: str = '',
    estado_filtro: str = 'activos',
    sort_by: str = 'id_asc',
    page: int = 1,
    per_page: int = 10
):
    """
    Obtiene lista paginada de usuarios con filtros de búsqueda, rol, estado (soft-delete) y ordenamiento.
    """
    query = Usuario.query

    # Filtro de estado (Soft delete)
    if estado_filtro == 'activos':
        query = query.filter(Usuario.deleted_at.is_(None))
    elif estado_filtro == 'eliminados':
        query = query.filter(Usuario.deleted_at.isnot(None))
    # 'todos' no agrega filtro sobre deleted_at

    # Búsqueda por texto (nombres, apellidos, email)
    if search_query:
        term = f"%{search_query.strip()}%"
        query = query.filter(
            or_(
                Usuario.nombres.ilike(term),
                Usuario.apellidos.ilike(term),
                Usuario.email.ilike(term)
            )
        )

    # Filtro por rol
    if rol_filtro and rol_filtro in ['admin', 'agente', 'turista']:
        query = query.join(Usuario.rol).filter(Rol.nombre == rol_filtro)

    # Ordenamiento
    if sort_by == 'id_desc':
        query = query.order_by(Usuario.id_usuario.desc())
    elif sort_by == 'nombre_asc':
        query = query.order_by(Usuario.nombres.asc(), Usuario.apellidos.asc())
    elif sort_by == 'nombre_desc':
        query = query.order_by(Usuario.nombres.desc(), Usuario.apellidos.desc())
    elif sort_by == 'fecha_desc':
        query = query.order_by(Usuario.fecha_registro.desc(), Usuario.id_usuario.desc())
    elif sort_by == 'fecha_asc':
        query = query.order_by(Usuario.fecha_registro.asc(), Usuario.id_usuario.asc())
    else:  # id_asc por defecto
        query = query.order_by(Usuario.id_usuario.asc())

    return query.paginate(page=page, per_page=per_page, error_out=False)

def get_total_estadisticas() -> dict:
    """
    Retorna métricas completas de usuarios para las tarjetas del panel administrativo.
    """
    total = Usuario.query.count()
    activos = Usuario.query.filter(Usuario.deleted_at.is_(None)).count()
    eliminados = Usuario.query.filter(Usuario.deleted_at.isnot(None)).count()
    admins = Usuario.query.join(Usuario.rol).filter(Rol.nombre == 'admin', Usuario.deleted_at.is_(None)).count()
    agentes = Usuario.query.join(Usuario.rol).filter(Rol.nombre == 'agente', Usuario.deleted_at.is_(None)).count()
    turistas = Usuario.query.join(Usuario.rol).filter(Rol.nombre == 'turista', Usuario.deleted_at.is_(None)).count()
    
    return {
        'total': total,
        'activos': activos,
        'eliminados': eliminados,
        'admins': admins,
        'agentes': agentes,
        'turistas': turistas
    }

def get_usuario_by_id(id_usuario: int) -> Usuario | None:
    """Obtiene un usuario por su ID"""
    return db.session.get(Usuario, id_usuario)

def create_user_by_admin(data: dict) -> tuple[bool, str, Usuario | None, str | None]:
    """
    Crea un nuevo usuario desde el panel del Administrador.
    Genera contraseña temporal para agentes y admins, activa expiración a 24h
    y dispara correo con credenciales temporales.
    Retorna (éxito: bool, mensaje: str, usuario: Usuario | None, password_temporal: str | None)
    """
    nombres = (data.get('nombres') or '').strip()
    apellidos = (data.get('apellidos') or '').strip()
    email = (data.get('email') or '').strip().lower()
    rol_nombre = (data.get('rol') or '').strip().lower()

    if not nombres or len(nombres) < 2:
        return False, "El nombre es obligatorio y debe tener al menos 2 caracteres.", None, None

    if not apellidos or len(apellidos) < 2:
        return False, "Los apellidos son obligatorios y deben tener al menos 2 caracteres.", None, None

    if not email or not re.match(EMAIL_REGEX, email):
        return False, "Por favor ingresa un correo electrónico válido.", None, None

    if Usuario.query.filter_by(email=email).first():
        return False, "El correo electrónico ya se encuentra registrado en el sistema.", None, None

    rol_obj = Rol.query.filter_by(nombre=rol_nombre).first()
    if not rol_obj:
        return False, f"El rol '{rol_nombre}' especificado no es válido.", None, None

    # Generar contraseña temporal aleatoria de 14 caracteres
    password_temporal = generate_random_password(length=14)
    expires_at = datetime.utcnow() + timedelta(hours=24)

    try:
        nuevo_usuario = Usuario(
            nombres=nombres,
            apellidos=apellidos,
            email=email,
            id_rol=rol_obj.id_rol,
            must_change_password=True,
            temp_password_expires_at=expires_at,
            two_factor_enabled=False
        )
        nuevo_usuario.set_password(password_temporal)

        db.session.add(nuevo_usuario)
        db.session.flush()

        # Si el rol es turista, crear también su registro en Turista
        if rol_nombre == 'turista':
            nuevo_turista = Turista(
                id_usuario=nuevo_usuario.id_usuario,
                nombres=nombres,
                apellidos=apellidos,
                email=email
            )
            db.session.add(nuevo_turista)

        db.session.commit()

        # Enviar correo con credenciales temporales al usuario
        email_service.enviar_credenciales_temporales(nuevo_usuario, password_temporal)

        return True, "Usuario creado exitosamente.", nuevo_usuario, password_temporal
    except Exception as e:
        db.session.rollback()
        return False, f"Error al crear el usuario: {str(e)}", None, None

def update_user_by_admin(id_usuario: int, data: dict) -> tuple[bool, str, Usuario | None]:
    """
    Actualiza la información básica de un usuario y su rol.
    """
    usuario = db.session.get(Usuario, id_usuario)
    if not usuario:
        return False, "Usuario no encontrado.", None

    nombres = (data.get('nombres') or '').strip()
    apellidos = (data.get('apellidos') or '').strip()
    email = (data.get('email') or '').strip().lower()
    rol_nombre = (data.get('rol') or '').strip().lower()

    if not nombres or len(nombres) < 2:
        return False, "El nombre es obligatorio y debe tener al menos 2 caracteres.", None

    if not apellidos or len(apellidos) < 2:
        return False, "Los apellidos son obligatorios y deben tener al menos 2 caracteres.", None

    if not email or not re.match(EMAIL_REGEX, email):
        return False, "Por favor ingresa un correo electrónico válido.", None

    # Verificar si el email lo usa otro usuario
    otro = Usuario.query.filter(Usuario.email == email, Usuario.id_usuario != id_usuario).first()
    if otro:
        return False, "Ese correo electrónico ya está siendo usado por otro usuario.", None

    rol_obj = Rol.query.filter_by(nombre=rol_nombre).first()
    if not rol_obj:
        return False, f"El rol '{rol_nombre}' no es válido.", None

    try:
        usuario.nombres = nombres
        usuario.apellidos = apellidos
        usuario.email = email
        usuario.id_rol = rol_obj.id_rol

        # Si tiene registro en Turista, sincronizar nombres y email
        if usuario.turista:
            usuario.turista.nombres = nombres
            usuario.turista.apellidos = apellidos
            usuario.turista.email = email

        db.session.commit()
        return True, "Usuario actualizado exitosamente.", usuario
    except Exception as e:
        db.session.rollback()
        return False, f"Error al actualizar el usuario: {str(e)}", None

def soft_delete_user(id_usuario: int) -> tuple[bool, str]:
    """
    Aplica eliminación lógica (soft delete) estableciendo deleted_at = datetime.utcnow().
    """
    usuario = db.session.get(Usuario, id_usuario)
    if not usuario:
        return False, "Usuario no encontrado."

    try:
        usuario.deleted_at = datetime.utcnow()
        db.session.commit()
        return True, f"El usuario {usuario.nombre_completo} ha sido desactivado (eliminación lógica)."
    except Exception as e:
        db.session.rollback()
        return False, f"Error al eliminar usuario: {str(e)}"

def restore_user(id_usuario: int) -> tuple[bool, str]:
    """
    Restaura un usuario eliminado lógicamente estableciendo deleted_at = None.
    """
    usuario = db.session.get(Usuario, id_usuario)
    if not usuario:
        return False, "Usuario no encontrado."

    try:
        usuario.deleted_at = None
        db.session.commit()
        return True, f"El usuario {usuario.nombre_completo} ha sido restaurado exitosamente."
    except Exception as e:
        db.session.rollback()
        return False, f"Error al restaurar usuario: {str(e)}"

def reset_password_by_admin(id_usuario: int) -> tuple[bool, str, str | None]:
    """
    Genera una nueva contraseña temporal para el usuario, marca must_change_password=True
    y envía correo de notificación.
    Retorna (éxito: bool, mensaje: str, password_temporal: str | None)
    """
    usuario = db.session.get(Usuario, id_usuario)
    if not usuario:
        return False, "Usuario no encontrado.", None

    password_temporal = generate_random_password(length=14)
    expires_at = datetime.utcnow() + timedelta(hours=24)

    try:
        usuario.set_password(password_temporal)
        usuario.must_change_password = True
        usuario.temp_password_expires_at = expires_at
        db.session.commit()

        # Enviar correo de reseteo
        email_service.enviar_reset_password(usuario, password_temporal)

        return True, "Contraseña reseteada exitosamente. Se ha enviado un correo al usuario.", password_temporal
    except Exception as e:
        db.session.rollback()
        return False, f"Error al resetear la contraseña: {str(e)}", None
