from flask import current_app
from flask_mail import Message
from app import mail
from threading import Thread

def _enviar_async(app, msg):
    """Envía el correo en un hilo aparte para no bloquear la petición."""
    with app.app_context():
        try:
            mail.send(msg)
            current_app.logger.info(f"Correo enviado exitosamente a: {msg.recipients}")
        except Exception as e:
            current_app.logger.error(f"Error al enviar correo: {e}")

def enviar_correo(asunto: str, destinatario: str, cuerpo_html: str, cuerpo_texto: str = None) -> bool:
    """
    Envía un correo electrónico de forma asíncrona.
    - destinatario: string con el email del usuario (dinámico).
    """
    if not destinatario:
        return False
    
    sender = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
    
    msg = Message(
        subject=asunto,
        sender=sender,
        recipients=[destinatario],
        html=cuerpo_html,
        body=cuerpo_texto or cuerpo_html
    )
    
    # Enviar en segundo plano para no bloquear
    app = current_app._get_current_object()
    Thread(target=_enviar_async, args=(app, msg), daemon=True).start()
    return True

def enviar_bienvenida(usuario) -> bool:
    """Correo de bienvenida al registrarse (turista)."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333333; background-color: #f9f9fb; padding: 20px; }}
            .card {{ background: #ffffff; border-radius: 12px; padding: 30px; max-width: 550px; margin: 0 auto; border: 1px solid #e5e7eb; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            .header {{ text-align: center; border-bottom: 2px solid #2ECC71; padding-bottom: 15px; margin-bottom: 20px; }}
            .brand {{ font-size: 24px; font-weight: bold; color: #151C28; }}
            .btn {{ display: inline-block; background-color: #2ECC71; color: #ffffff !important; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 15px; }}
            .footer {{ margin-top: 25px; font-size: 12px; color: #9ca3af; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <div class="brand">🦉 Búhos Tours</div>
            </div>
            <h2>¡Bienvenido a Buhos Tours, {usuario.nombres}!</h2>
            <p>Tu cuenta ha sido creada exitosamente.</p>
            <p>Ya puedes iniciar sesión en la plataforma y comenzar a planificar tu itinerario turístico optimizado con Inteligencia Artificial.</p>
            <p style="text-align: center;">
                <a href="http://127.0.0.1:5000/login" class="btn">Iniciar Sesión</a>
            </p>
            <div class="footer">
                <p>Saludos,<br><strong>Equipo Buhos Tours</strong></p>
                <p>Este es un correo automático, por favor no responder directamente a este mensaje.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return enviar_correo(
        asunto="¡Bienvenido a Buhos Tours!",
        destinatario=usuario.email,
        cuerpo_html=html
    )

def enviar_credenciales_temporales(usuario, password_temporal: str) -> bool:
    """Correo al agente/admin con su contraseña temporal (creado por admin)."""
    rol_str = usuario.rol.nombre.capitalize() if (usuario.rol and usuario.rol.nombre) else 'Agente'
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333333; background-color: #f9f9fb; padding: 20px; }}
            .card {{ background: #ffffff; border-radius: 12px; padding: 30px; max-width: 550px; margin: 0 auto; border: 1px solid #e5e7eb; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            .header {{ text-align: center; border-bottom: 2px solid #2ECC71; padding-bottom: 15px; margin-bottom: 20px; }}
            .brand {{ font-size: 24px; font-weight: bold; color: #151C28; }}
            .box-credentials {{ background-color: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 8px; padding: 15px; margin: 20px 0; }}
            .password-code {{ font-size: 18px; font-weight: bold; color: #0284C7; font-family: monospace; background: #E0F2FE; padding: 4px 8px; border-radius: 4px; }}
            .warning {{ color: #D97706; font-size: 13px; font-weight: 600; margin-top: 10px; }}
            .footer {{ margin-top: 25px; font-size: 12px; color: #9ca3af; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <div class="brand">🦉 Búhos Tours</div>
            </div>
            <h2>Hola {usuario.nombres},</h2>
            <p>El administrador del sistema te ha creado una cuenta con rol de <strong>{rol_str}</strong> en Buhos Tours.</p>
            
            <div class="box-credentials">
                <p style="margin: 0 0 10px 0;"><strong>Correo de acceso:</strong> {usuario.email}</p>
                <p style="margin: 0;"><strong>Contraseña temporal:</strong> <span class="password-code">{password_temporal}</span></p>
                <p class="warning">⚠️ Esta contraseña temporal expira en 24 horas.</p>
            </div>

            <p>Al iniciar sesión por primera vez, el sistema te solicitará obligatoriamente:</p>
            <ol>
                <li>Cambiar tu contraseña por una clave segura y definitiva (mínimo 12 caracteres).</li>
                <li>Configurar la autenticación de dos factores (2FA) escaneando tu código QR.</li>
            </ol>

            <div class="footer">
                <p>Saludos cordiales,<br><strong>Equipo de Seguridad - Buhos Tours</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    return enviar_correo(
        asunto="Tus credenciales de acceso a Buhos Tours",
        destinatario=usuario.email,
        cuerpo_html=html
    )

def enviar_reset_password(usuario, password_temporal: str) -> bool:
    """Correo cuando el admin resetea la contraseña de un usuario."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333333; background-color: #f9f9fb; padding: 20px; }}
            .card {{ background: #ffffff; border-radius: 12px; padding: 30px; max-width: 550px; margin: 0 auto; border: 1px solid #e5e7eb; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            .header {{ text-align: center; border-bottom: 2px solid #2ECC71; padding-bottom: 15px; margin-bottom: 20px; }}
            .brand {{ font-size: 24px; font-weight: bold; color: #151C28; }}
            .box-credentials {{ background-color: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 8px; padding: 15px; margin: 20px 0; }}
            .password-code {{ font-size: 18px; font-weight: bold; color: #0284C7; font-family: monospace; background: #E0F2FE; padding: 4px 8px; border-radius: 4px; }}
            .warning {{ color: #D97706; font-size: 13px; font-weight: 600; margin-top: 10px; }}
            .footer {{ margin-top: 25px; font-size: 12px; color: #9ca3af; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <div class="brand">🦉 Búhos Tours</div>
            </div>
            <h2>Hola {usuario.nombres},</h2>
            <p>El administrador ha reseteado la contraseña de tu cuenta en Buhos Tours.</p>
            
            <div class="box-credentials">
                <p style="margin: 0 0 10px 0;"><strong>Correo:</strong> {usuario.email}</p>
                <p style="margin: 0;"><strong>Nueva contraseña temporal:</strong> <span class="password-code">{password_temporal}</span></p>
                <p class="warning">⚠️ Esta contraseña temporal expira en 24 horas.</p>
            </div>

            <p>Deberás cambiarla obligatoriamente la próxima vez que inicies sesión.</p>
            
            <div class="footer">
                <p>Saludos,<br><strong>Equipo Buhos Tours</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    return enviar_correo(
        asunto="Reseteo de contraseña - Buhos Tours",
        destinatario=usuario.email,
        cuerpo_html=html
    )

def enviar_reset_password_link(usuario, reset_url: str) -> bool:
    """Correo con enlace seguro de restablecimiento de contraseña (15 minutos)."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333333; background-color: #f9f9fb; padding: 20px; }}
            .card {{ background: #ffffff; border-radius: 12px; padding: 30px; max-width: 550px; margin: 0 auto; border: 1px solid #e5e7eb; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            .header {{ text-align: center; border-bottom: 2px solid #2ECC71; padding-bottom: 15px; margin-bottom: 20px; }}
            .brand {{ font-size: 24px; font-weight: bold; color: #151C28; }}
            .btn {{ display: inline-block; background-color: #2ECC71; color: #ffffff !important; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 15px; }}
            .warning {{ color: #D97706; font-size: 13px; font-weight: 600; margin-top: 15px; }}
            .footer {{ margin-top: 25px; font-size: 12px; color: #9ca3af; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <div class="brand">🦉 Búhos Tours</div>
            </div>
            <h2>Hola {usuario.nombres},</h2>
            <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en Buhos Tours.</p>
            <p>Para definir tu nueva contraseña, haz clic en el siguiente botón:</p>
            
            <p style="text-align: center; margin: 25px 0;">
                <a href="{reset_url}" class="btn">Restablecer mi Contraseña</a>
            </p>

            <p class="warning">⏱️ Este enlace es de un solo uso y expirará en <strong>15 minutos</strong>.</p>
            <p style="font-size: 12px; color: #6b7280; word-break: break-all;">
                Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
                <a href="{reset_url}">{reset_url}</a>
            </p>

            <p style="font-size: 13px; color: #6b7280;">Si no solicitaste este cambio, puedes ignorar este mensaje de forma segura.</p>

            <div class="footer">
                <p>Saludos,<br><strong>Equipo de Seguridad - Buhos Tours</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    return enviar_correo(
        asunto="Restablecer tu contraseña - Buhos Tours",
        destinatario=usuario.email,
        cuerpo_html=html
    )

def enviar_codigo_2fa(usuario, codigo: str) -> bool:
    """Correo con el código 2FA de respaldo (si aplica)."""
    html = f"""
    <h2>Hola {usuario.nombres},</h2>
    <p>Tu código de verificación de dos factores es: <strong style="font-size: 22px; letter-spacing: 2px; color: #151C28;">{codigo}</strong></p>
    <p>Este código expira en 5 minutos.</p>
    <p>Saludos,<br>Equipo Buhos Tours</p>
    """
    return enviar_correo(
        asunto="Código de verificación - Buhos Tours",
        destinatario=usuario.email,
        cuerpo_html=html
    )

def enviar_itinerario_confirmado(usuario, itinerario) -> bool:
    """Correo cuando el itinerario se confirma y se genera el voucher."""
    id_itin = getattr(itinerario, 'id_itinerario', 'N/A')
    html = f"""
    <h2>¡Tu itinerario está confirmado!</h2>
    <p>Hola {usuario.nombres}, tu itinerario <strong>#{id_itin}</strong> ha sido confirmado exitosamente.</p>
    <p>Ya puedes descargar tu voucher y ver todos los detalles de transporte y atractivos desde tu panel de usuario.</p>
    <p>Saludos cordiales,<br><strong>Equipo Buhos Tours</strong></p>
    """
    return enviar_correo(
        asunto="Itinerario confirmado - Buhos Tours",
        destinatario=usuario.email,
        cuerpo_html=html
    )
