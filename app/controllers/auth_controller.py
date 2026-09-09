from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.services import auth_service

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))

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

        success, message, user = auth_service.login_user(email, password, remember)
        if success:
            flash(message, 'success')
            next_page = request.args.get('next')
            # Evitar open redirects verificando que sea ruta relativa
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('auth.dashboard'))
        else:
            flash(message, 'danger')
            return render_template('auth/login.html', email=email)

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    auth_service.logout_user()
    flash('Has cerrado sesión correctamente. ¡Hasta pronto!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('auth/dashboard.html', user=current_user)
