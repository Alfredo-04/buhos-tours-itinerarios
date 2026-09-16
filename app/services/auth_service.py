import re
from datetime import datetime
from flask_login import login_user as flask_login_user, logout_user as flask_logout_user
from app import db
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.turista import Turista

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valida que la contraseña cumpla los criterios mínimos de seguridad:
    - Al menos 8 caracteres
    - Al menos una letra mayúscula
    - Al menos una letra minúscula
    - Al menos un número
    - Al menos un carácter especial
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe contener al menos una letra mayúscula."
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe contener al menos una letra minúscula."
    if not re.search(r"[0-9]", password):
        return False, "La contraseña debe contener al menos un número."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "La contraseña debe contener al menos un carácter especial (!@#$%^&*...)."
    return True, ""

def register_user(data: dict) -> tuple[bool, str, Usuario | None]:
    """
    Registra un nuevo usuario turista con sus datos básicos y crea simultáneamente
    el registro inicial en la tabla TURISTA vinculado al USUARIO. Los datos legales del
    viajero se completan posteriormente al planificar o confirmar un itinerario.
    Retorna (éxito: bool, mensaje: str, usuario: Usuario | None)
    """
    nombres = (data.get('nombres') or '').strip()
    apellidos = (data.get('apellidos') or '').strip()
    email = (data.get('email') or '').strip().lower()
    contrasenia = data.get('contrasenia') or ''
    confirm_password = data.get('confirm_password') or ''
    telefono = (data.get('telefono') or '').strip()

    # Validación de nombres y apellidos
    if not nombres or len(nombres) < 2:
        return False, "El nombre es obligatorio y debe tener al menos 2 caracteres.", None

    if not apellidos or len(apellidos) < 2:
        return False, "Los apellidos son obligatorios y deben tener al menos 2 caracteres.", None

    # Validación de email
    if not email or not re.match(EMAIL_REGEX, email):
        return False, "Por favor ingresa un correo electrónico válido.", None

    # Verificar si el email ya está registrado en Usuario
    usuario_existente = Usuario.query.filter_by(email=email).first()
    if usuario_existente:
        return False, "El correo electrónico ya se encuentra registrado.", None

    # Validación de contraseña
    is_valid_pwd, pwd_error = validate_password_strength(contrasenia)
    if not is_valid_pwd:
        return False, pwd_error, None

    # Validación de coincidencia de contraseñas
    if contrasenia != confirm_password:
        return False, "Las contraseñas no coinciden.", None

    # Buscar rol 'turista' por defecto
    rol_turista = Rol.query.filter_by(nombre='turista').first()
    if not rol_turista:
        rol_turista = Rol(nombre='turista')
        db.session.add(rol_turista)
        db.session.flush()

    # Crear y guardar nuevo usuario y turista mínimo vinculado en una transacción
    try:
        nuevo_usuario = Usuario(
            nombres=nombres,
            apellidos=apellidos,
            email=email,
            id_rol=rol_turista.id_rol
        )
        nuevo_usuario.set_password(contrasenia)

        db.session.add(nuevo_usuario)
        db.session.flush()  # Obtener nuevo_usuario.id_usuario

        # Registro mínimo de Turista: nombres, apellidos, email y teléfono opcional
        nuevo_turista = Turista(
            id_usuario=nuevo_usuario.id_usuario,
            nombres=nombres,
            apellidos=apellidos,
            email=email,
            telefono=telefono if telefono else None
        )
        db.session.add(nuevo_turista)
        db.session.commit()

        return True, "Registro exitoso. Ahora puedes iniciar sesión con tu cuenta.", nuevo_usuario
    except Exception as e:
        db.session.rollback()
        return False, f"Ocurrió un error al procesar el registro: {str(e)}", None

def login_user(email: str, password: str, remember: bool = False) -> tuple[bool, str, Usuario | None]:
    """
    Verifica las credenciales del usuario y gestiona la sesión con Flask-Login.
    Retorna (éxito: bool, mensaje: str, usuario: Usuario | None)
    """
    email = (email or '').strip().lower()
    password = password or ''

    if not email or not password:
        return False, "Debes ingresar tu correo y contraseña.", None

    usuario = Usuario.query.filter_by(email=email).first()

    if not usuario or not usuario.check_password(password):
        return False, "Credenciales incorrectas. Verifica tu correo y contraseña.", None

    # Iniciar sesión con Flask-Login
    flask_login_user(usuario, remember=remember)
    return True, f"¡Bienvenido de nuevo, {usuario.nombres}!", usuario

def logout_user() -> bool:
    """
    Cierra la sesión del usuario actual.
    """
    flask_logout_user()
    return True
