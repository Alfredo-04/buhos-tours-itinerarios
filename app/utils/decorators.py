from functools import wraps
from flask import abort, flash, redirect, url_for, session
from flask_login import current_user

def role_required(*roles):
    """
    Decorador para proteger vistas según el rol del usuario autenticado.
    Uso: @role_required('admin') o @role_required('admin', 'agente')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Verificar si el usuario tiene asignado un rol válido
            if not current_user.rol or current_user.rol.nombre not in roles:
                flash('No tienes permiso para acceder a esta sección.', 'danger')
                abort(403)
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Acceso exclusivo para rol 'admin'"""
    return role_required('admin')(f)

def agente_required(f):
    """Acceso para rol 'agente' y 'admin'"""
    return role_required('agente', 'admin')(f)

def require_2fa(f):
    """
    Decorador para exigir que el usuario tenga 2FA activo si es admin o agente.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.rol and current_user.rol.nombre in ['admin', 'agente'] and not current_user.two_factor_enabled:
            flash('Como agente o administrador, debes configurar la autenticación de dos factores (2FA) para continuar.', 'warning')
            return redirect(url_for('auth.configurar_2fa'))
        return f(*args, **kwargs)
    return decorated_function

def turista_required(f):
    """Acceso para rol 'turista'"""
    return role_required('turista')(f)
