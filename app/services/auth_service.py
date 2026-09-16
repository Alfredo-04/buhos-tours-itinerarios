import re
import io
import base64
import secrets
import string
from datetime import datetime, timedelta
import pyotp
import qrcode
from flask_login import login_user as flask_login_user, logout_user as flask_logout_user
from app import db
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.turista import Turista
from app.services import email_service

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

def validate_password_strength(password: str, min_length: int | str = 8) -> tuple[bool, str]:
    """
    Valida que la contraseña cumpla los criterios de seguridad:
    - Longitud mínima (8 para turista, 12 para agentes/admin)
    - Al menos una letra mayúscula
    - Al menos una letra minúscula
    - Al menos un número
    - Al menos un carácter especial
    """
    if isinstance(min_length, str):
        min_len = 12 if min_length.lower() in ['admin', 'agente'] else 8
    else:
        min_len = int(min_length)

    if len(password) < min_len:
        return False, f"La contraseña debe tener al menos {min_len} caracteres."
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe contener al menos una letra mayúscula."
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe contener al menos una letra minúscula."
    if not re.search(r"[0-9]", password):
        return False, "La contraseña debe contener al menos un número."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-\[\]]", password):
        return False, "La contraseña debe contener al menos un carácter especial (!@#$%^&*...)."
    return True, ""

def generate_random_password(length: int = 14) -> str:
    """
    Genera una contraseña temporal aleatoria criptográficamente segura
    que garantiza mayúsculas, minúsculas, números y símbolos especiales.
    """
    specials = "!@#$%&*_-+"
    characters = string.ascii_letters + string.digits + specials
    while True:
        password = ''.join(secrets.choice(characters) for _ in range(length))
        # Verificar que cumpla con todos los criterios de fuerza
        is_strong, _ = validate_password_strength(password, min_length=12)
        if is_strong:
            return password

def generate_2fa_setup(usuario: Usuario) -> tuple[str, str]:
    """
    Genera una clave secreta TOTP y un código QR en base64 para Google Authenticator.
    Retorna (secret_key: str, qr_code_base64: str)
    """
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=usuario.email,
        issuer_name="Buhos Tours"
    )
    
    # Generar imagen QR en memoria con PIL
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=3,
    )
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="#151C28", back_color="#FFFFFF")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return secret, f"data:image/png;base64,{qr_base64}"

def verify_totp_code(secret: str, code: str) -> bool:
    """
    Verifica si el código numérico de 6 dígitos ingresado coincide con el TOTP secret.
    """
    if not secret or not code:
        return False
    code_cleaned = str(code).strip().replace(' ', '')
    totp = pyotp.TOTP(secret)
    # valid_window=1 tolera pequeños desfases de reloj (+/- 30s)
    return totp.verify(code_cleaned, valid_window=1)

def register_user(data: dict) -> tuple[bool, str, Usuario | None]:
    """
    Registra un nuevo usuario turista público con datos básicos y vinculación a Turista.
    Envía correo de bienvenida dinámicamente.
    """
    nombres = (data.get('nombres') or '').strip()
    apellidos = (data.get('apellidos') or '').strip()
    email = (data.get('email') or '').strip().lower()
    contrasenia = data.get('contrasenia') or data.get('password') or ''
    confirm_password = data.get('confirm_password') or data.get('confirmar_contrasenia') or ''
    telefono = (data.get('telefono') or '').strip()

    if not nombres or len(nombres) < 2:
        return False, "El nombre es obligatorio y debe tener al menos 2 caracteres.", None

    if not apellidos or len(apellidos) < 2:
        return False, "Los apellidos son obligatorios y deben tener al menos 2 caracteres.", None

    if not email or not re.match(EMAIL_REGEX, email):
        return False, "Por favor ingresa un correo electrónico válido.", None

    usuario_existente = Usuario.query.filter_by(email=email).first()
    if usuario_existente:
        return False, "El correo electrónico ya se encuentra registrado.", None

    # Validación de contraseña para turista (mínimo 8 caracteres)
    is_valid_pwd, pwd_error = validate_password_strength(contrasenia, min_length=8)
    if not is_valid_pwd:
        return False, pwd_error, None

    if contrasenia != confirm_password:
        return False, "Las contraseñas no coinciden.", None

    rol_turista = Rol.query.filter_by(nombre='turista').first()
    if not rol_turista:
        rol_turista = Rol(nombre='turista')
        db.session.add(rol_turista)
        db.session.flush()

    try:
        nuevo_usuario = Usuario(
            nombres=nombres,
            apellidos=apellidos,
            email=email,
            id_rol=rol_turista.id_rol,
            must_change_password=False,
            two_factor_enabled=False
        )
        nuevo_usuario.set_password(contrasenia)

        db.session.add(nuevo_usuario)
        db.session.flush()

        nuevo_turista = Turista(
            id_usuario=nuevo_usuario.id_usuario,
            nombres=nombres,
            apellidos=apellidos,
            email=email,
            telefono=telefono if telefono else None
        )
        db.session.add(nuevo_turista)
        db.session.commit()

        # Enviar correo de bienvenida dinámico
        email_service.enviar_bienvenida(nuevo_usuario)

        return True, "¡Registro exitoso! Ya puedes iniciar sesión con tu cuenta.", nuevo_usuario
    except Exception as e:
        db.session.rollback()
        return False, f"Ocurrió un error al procesar el registro: {str(e)}", None

def validate_user_login(email: str, password: str) -> tuple[bool, str, Usuario | None]:
    """
    Valida credenciales, estado de soft-delete y expiración de contraseña temporal.
    Retorna (éxito: bool, mensaje: str, usuario: Usuario | None)
    """
    email = (email or '').strip().lower()
    password = password or ''

    if not email or not password:
        return False, "Debes ingresar tu correo y contraseña.", None

    usuario = Usuario.query.filter_by(email=email).first()

    if not usuario or not usuario.check_password(password):
        return False, "Credenciales incorrectas. Verifica tu correo y contraseña.", None

    # Verificar si el usuario ha sido eliminado lógicamente
    if usuario.is_deleted:
        return False, "Tu cuenta ha sido desactivada. Comunícate con el administrador.", None

    # Verificar si la contraseña temporal expiró
    if usuario.must_change_password and usuario.is_temp_password_expired:
        return False, "Tu contraseña temporal ha expirado. Contacta al administrador para que genere una nueva.", None

    return True, "Credenciales válidas.", usuario

def login_flask_user(usuario: Usuario, remember: bool = False):
    """Ejecuta el inicio de sesión real con Flask-Login"""
    flask_login_user(usuario, remember=remember)

def logout_user():
    """Cierra la sesión activa con Flask-Login"""
    flask_logout_user()

def request_password_reset(email: str) -> tuple[bool, str, str | None, Usuario | None]:
    """
    Inicia la solicitud de recuperación de contraseña para un correo dado.
    Genera un token seguro válido por 15 minutos.
    Por seguridad, no revela si el correo existe o no en el sistema.
    Retorna (éxito: bool, mensaje: str, token: str | None, usuario: Usuario | None)
    """
    email_clean = (email or '').strip().lower()
    msg_generico = "Si el correo electrónico está registrado en el sistema, recibirás un enlace para restablecer tu contraseña en los próximos minutos."

    if not email_clean or not re.match(EMAIL_REGEX, email_clean):
        return True, msg_generico, None, None

    usuario = Usuario.query.filter_by(email=email_clean).first()
    if not usuario or usuario.is_deleted:
        return True, msg_generico, None, None

    # Generar token seguro e intransferible
    token = secrets.token_urlsafe(32)
    usuario.reset_token = token
    usuario.reset_token_expires_at = datetime.utcnow() + timedelta(minutes=15)
    usuario.reset_token_used = False

    try:
        db.session.commit()
        return True, msg_generico, token, usuario
    except Exception as e:
        db.session.rollback()
        return False, f"Error al procesar la solicitud: {str(e)}", None, None

def verify_reset_token(token: str) -> tuple[bool, str, Usuario | None]:
    """
    Verifica si el token de recuperación de contraseña es válido, no ha sido usado
    y se encuentra dentro de los 15 minutos de vigencia.
    """
    if not token:
        return False, "Token de restablecimiento no proporcionado.", None

    usuario = Usuario.query.filter_by(reset_token=token).first()
    if not usuario:
        return False, "El enlace de restablecimiento es inválido o no existe.", None

    if usuario.reset_token_used:
        return False, "Este enlace de restablecimiento ya ha sido utilizado. Solicita uno nuevo.", None

    if not usuario.reset_token_expires_at or datetime.utcnow() > usuario.reset_token_expires_at:
        return False, "El enlace de restablecimiento ha expirado (validez máxima de 15 minutos). Por favor solicita uno nuevo.", None

    return True, "Token válido.", usuario

def reset_password_with_token(token: str, new_password: str, confirm_password: str) -> tuple[bool, str]:
    """
    Restablece la contraseña utilizando el token validado, aplicando las reglas
    de seguridad diferenciadas según el rol del usuario (12+ caracteres para agentes/admin,
    8+ para turistas).
    """
    is_valid_token, token_err, usuario = verify_reset_token(token)
    if not is_valid_token or not usuario:
        return False, token_err

    if new_password != confirm_password:
        return False, "Las contraseñas no coinciden."

    # Aplicar reglas de contraseña según el rol del usuario
    min_len = 12 if (usuario.rol and usuario.rol.nombre in ['admin', 'agente']) else 8
    is_valid_pwd, pwd_err = validate_password_strength(new_password, min_length=min_len)
    if not is_valid_pwd:
        if min_len == 12:
            return False, f"Para tu rol ({usuario.rol.nombre.capitalize()}), la contraseña debe tener al menos 12 caracteres, incluyendo mayúscula, minúscula, número y símbolo especial."
        return False, pwd_err

    try:
        usuario.set_password(new_password)
        usuario.reset_token_used = True
        usuario.reset_token = None
        usuario.reset_token_expires_at = None
        usuario.must_change_password = False
        usuario.temp_password_expires_at = None
        db.session.commit()
        return True, "Tu contraseña ha sido restablecida exitosamente. Ya puedes iniciar sesión con tu nueva clave."
    except Exception as e:
        db.session.rollback()
        return False, f"Error al restablecer la contraseña: {str(e)}"

def update_mandatory_password(usuario: Usuario, new_password: str, confirm_password: str) -> tuple[bool, str]:
    """
    Actualiza la contraseña obligatoria de primer login para agentes/admin.
    Exige mínimo 12 caracteres y reglas fuertes.
    """
    if new_password != confirm_password:
        return False, "Las contraseñas no coinciden."

    # Agentes y Administradores requieren mínimo 12 caracteres
    min_len = 12 if (usuario.rol and usuario.rol.nombre in ['admin', 'agente']) else 8
    is_valid, err_msg = validate_password_strength(new_password, min_length=min_len)
    if not is_valid:
        return False, err_msg

    try:
        usuario.set_password(new_password)
        usuario.must_change_password = False
        usuario.temp_password_expires_at = None
        db.session.commit()
        return True, "Contraseña actualizada exitosamente."
    except Exception as e:
        db.session.rollback()
        return False, f"Error al actualizar la contraseña: {str(e)}"



