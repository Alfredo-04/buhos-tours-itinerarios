from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app import db
from app.models.usuario import Usuario
from app.services import auth_service, email_service

auth_bp = Blueprint('auth', __name__)

def redirect_by_role(usuario: Usuario):
    """Redirige al dashboard correspondiente según el rol del usuario."""
    if not usuario or not usuario.rol:
        return redirect(url_for('auth.login'))
    
    rol_nombre = usuario.rol.nombre
    if rol_nombre == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif rol_nombre == 'agente':
        return redirect(url_for('agente.dashboard'))
    else:
        return redirect(url_for('turista.dashboard'))

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """Ruta unificada que despacha al dashboard según el rol del usuario actual."""
    # Verificar si el usuario debe cambiar su contraseña
    if current_user.must_change_password:
        return redirect(url_for('auth.cambiar_password_obligatorio'))
    
    # Verificar si administradores o agentes tienen 2FA pendiente (obligatorio)
    if current_user.rol.nombre in ['admin', 'agente'] and not current_user.two_factor_enabled:
        flash('Debes configurar la autenticación de dos factores (2FA) para proteger tu cuenta.', 'warning')
        return redirect(url_for('auth.configurar_2fa'))

    return redirect_by_role(current_user)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        success, message, user = auth_service.register_user(request.form)
        if success:
            flash(message, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(message, 'danger')
            return render_template('auth/signup.html', form_data=request.form)

    return render_template('auth/signup.html', form_data={})

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))

        success, message, usuario = auth_service.validate_user_login(email, password)
        if not success:
            flash(message, 'danger')
            return render_template('auth/login.html', email=email)

        # 1. Caso: Debe cambiar contraseña obligatoriamente (primer login agente/admin o reseteo)
        if usuario.must_change_password:
            session['force_change_user_id'] = usuario.id_usuario
            session['force_change_remember'] = remember
            flash('Debes cambiar tu contraseña temporal antes de continuar.', 'info')
            return redirect(url_for('auth.cambiar_password_obligatorio'))

        # 2. Caso: Cuenta con 2FA habilitado -> redirigir a verificación
        if usuario.two_factor_enabled:
            session['pre_2fa_user_id'] = usuario.id_usuario
            session['pre_2fa_remember'] = remember
            return redirect(url_for('auth.verificar_2fa'))

        # 3. Caso: Login directo
        auth_service.login_flask_user(usuario, remember=remember)
        flash(f"¡Bienvenido de nuevo, {usuario.nombres}!", 'success')

        # Si es admin o agente y no tiene 2FA configurado, obligar a configurarlo
        if usuario.rol.nombre in ['admin', 'agente'] and not usuario.two_factor_enabled:
            flash('Por seguridad de la empresa, es obligatorio configurar 2FA.', 'warning')
            return redirect(url_for('auth.configurar_2fa'))

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect_by_role(usuario)

    return render_template('auth/login.html')

@auth_bp.route('/auth/verificar-2fa', methods=['GET', 'POST'])
@auth_bp.route('/verificar-2fa', methods=['GET', 'POST'])
def verificar_2fa():
    user_id = session.get('pre_2fa_user_id')
    if not user_id:
        flash('Sesión de verificación expirada. Por favor ingresa tus credenciales.', 'warning')
        return redirect(url_for('auth.login'))

    usuario = db.session.get(Usuario, user_id)
    if not usuario or usuario.is_deleted:
        session.pop('pre_2fa_user_id', None)
        flash('Usuario no válido.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        if auth_service.verify_totp_code(usuario.two_factor_secret, codigo):
            remember = session.pop('pre_2fa_remember', False)
            session.pop('pre_2fa_user_id', None)
            auth_service.login_flask_user(usuario, remember=remember)
            flash(f"¡Autenticación de dos factores completada! Bienvenido, {usuario.nombres}.", 'success')
            return redirect_by_role(usuario)
        else:
            flash('El código de 6 dígitos ingresado es incorrecto o ha expirado.', 'danger')

    return render_template('auth/verificar_2fa.html', usuario=usuario)

@auth_bp.route('/auth/configurar-2fa', methods=['GET', 'POST'])
@auth_bp.route('/configurar-2fa', methods=['GET', 'POST'])
def configurar_2fa():
    # Obtener el usuario activo o en flujo de configuración
    usuario = None
    if current_user.is_authenticated:
        usuario = current_user
    elif 'force_setup_2fa_user_id' in session:
        usuario = db.session.get(Usuario, session['force_setup_2fa_user_id'])

    if not usuario:
        flash('Debes iniciar sesión para configurar la autenticación de dos factores.', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        secret = session.get('pending_2fa_secret')
        
        if not secret:
            flash('Error en la sesión de configuración. Inténtalo nuevamente.', 'danger')
            return redirect(url_for('auth.configurar_2fa'))

        if auth_service.verify_totp_code(secret, codigo):
            usuario.two_factor_secret = secret
            usuario.two_factor_enabled = True
            usuario.two_factor_confirmed_at = datetime.utcnow()
            db.session.commit()

            session.pop('pending_2fa_secret', None)
            session.pop('force_setup_2fa_user_id', None)

            if not current_user.is_authenticated:
                auth_service.login_flask_user(usuario)

            flash('¡Autenticación de dos factores (2FA) configurada y activada con éxito!', 'success')
            return redirect_by_role(usuario)
        else:
            flash('Código incorrecto. Verifica el número en tu aplicación autenticadora.', 'danger')

    # Generar secreto y QR nuevo si no está en sesión
    secret, qr_code_base64 = auth_service.generate_2fa_setup(usuario)
    session['pending_2fa_secret'] = secret

    return render_template(
        'auth/configurar_2fa.html',
        usuario=usuario,
        secret=secret,
        qr_code_base64=qr_code_base64
    )

@auth_bp.route('/auth/cambiar-password-obligatorio', methods=['GET', 'POST'])
@auth_bp.route('/cambiar-password-obligatorio', methods=['GET', 'POST'])
def cambiar_password_obligatorio():
    user_id = session.get('force_change_user_id')
    usuario = None

    if user_id:
        usuario = db.session.get(Usuario, user_id)
    elif current_user.is_authenticated and current_user.must_change_password:
        usuario = current_user

    if not usuario:
        flash('No tienes ningún cambio de contraseña pendiente.', 'info')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        success, message = auth_service.update_mandatory_password(usuario, new_password, confirm_password)
        if success:
            flash('Contraseña actualizada con éxito.', 'success')
            session.pop('force_change_user_id', None)
            remember = session.pop('force_change_remember', False)
            auth_service.login_flask_user(usuario, remember=remember)

            # Si es agente o admin y aún no configuró 2FA, forzar configuración
            if usuario.rol.nombre in ['admin', 'agente'] and not usuario.two_factor_enabled:
                flash('Ahora debes configurar la autenticación de dos factores (2FA).', 'info')
                return redirect(url_for('auth.configurar_2fa'))

            return redirect_by_role(usuario)
        else:
            flash(message, 'danger')

    return render_template('auth/cambiar_password_obligatorio.html', usuario=usuario)

@auth_bp.route('/auth/forgot-password', methods=['GET', 'POST'])
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            flash('Por favor ingresa tu correo electrónico.', 'warning')
            return render_template('auth/forgot_password.html')

        success, message, token, usuario = auth_service.request_password_reset(email)
        if token and usuario:
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            email_service.enviar_reset_password_link(usuario, reset_url)
        session['reset_email_sent_to'] = email
        return redirect(url_for('auth.check_email'))

    return render_template('auth/forgot_password.html')

@auth_bp.route('/auth/check-email')
@auth_bp.route('/check-email')
def check_email():
    email = session.pop('reset_email_sent_to', None)
    return render_template('auth/check_email.html', email=email)

@auth_bp.route('/auth/reset-password/<token>', methods=['GET', 'POST'])
@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    valid, message, usuario = auth_service.verify_reset_token(token)
    if not valid:
        flash(message, 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        success, msg = auth_service.reset_password_with_token(token, new_password, confirm_password)
        if success:
            flash(msg, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(msg, 'danger')
            return render_template('auth/reset_password.html', token=token, usuario=usuario)

    return render_template('auth/reset_password.html', token=token, usuario=usuario)

@auth_bp.route('/logout')
@login_required
def logout():
    auth_service.logout_user()
    session.clear()
    flash('Has cerrado sesión correctamente. ¡Hasta pronto!', 'info')
    return redirect(url_for('auth.login'))
