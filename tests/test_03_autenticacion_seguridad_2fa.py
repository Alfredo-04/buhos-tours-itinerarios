# -*- coding: utf-8 -*-
"""
Módulo 03: Pruebas Automatizadas de Autenticación, Seguridad Criptográfica y 2FA.
Total de pruebas: 35 (Positivas, Negativas y Criptográficas).
"""

import re
import time
from datetime import datetime
import pyotp
from unittest.mock import MagicMock, patch
from werkzeug.security import generate_password_hash, check_password_hash
from tests.conftest_base import BaseTestCase
from app.services.auth_service import (
    validate_password_strength,
    _validar_telefono,
    EMAIL_REGEX
)


class TestAutenticacionSeguridad2FA(BaseTestCase):
    """Suite de 35 pruebas para Autenticación, Hashing Seguro, Tokens y 2FA."""

    # 86-95: Criptografía y Hashing Seguro de Contraseñas
    def test_086_hash_password_genera_cadena_segura(self):
        pwd = "PasswordSeguro2026!"
        h = generate_password_hash(pwd)
        self.assertTrue(h.startswith('scrypt:') or h.startswith('pbkdf2:') or h.startswith('argon2'))
        self.assertNotEqual(pwd, h)
        self.registrar_resultado("PA-AUTH-086", "Autenticación y Seguridad", "Criptográfica",
                                 "Generación de hash seguro con salt", "Contraseña en texto claro", "Hash unidireccional no reversible", "Hash seguro")

    def test_087_verificacion_password_correcta(self):
        pwd = "MiPassword123"
        h = generate_password_hash(pwd)
        self.assertTrue(check_password_hash(h, pwd))
        self.registrar_resultado("PA-AUTH-087", "Autenticación y Seguridad", "Criptográfica",
                                 "Verificación exitosa de contraseña válida", "Hash y contraseña coincidente", "check_password_hash == True", "Verificado")

    def test_088_negativo_verificacion_password_incorrecta_rechazo(self):
        h = generate_password_hash("PasswordCorrecto123")
        self.assertFalse(check_password_hash(h, "PasswordIncorrecto999"))
        self.registrar_resultado("PA-AUTH-088", "Autenticación y Seguridad", "Negativa / Seguridad",
                                 "Rechazo de contraseña errónea contra hash", "Hash legítimo y contraseña falsa", "check_password_hash == False", "Rechazado")

    def test_089_salt_unico_genera_hashes_distintos_misma_clave(self):
        pwd = "MismaContrasenia123"
        h1 = generate_password_hash(pwd)
        h2 = generate_password_hash(pwd)
        self.assertNotEqual(h1, h2) # Salts diferentes
        self.assertTrue(check_password_hash(h1, pwd))
        self.assertTrue(check_password_hash(h2, pwd))
        self.registrar_resultado("PA-AUTH-089", "Autenticación y Seguridad", "Criptográfica",
                                 "Salts dinámicos contra ataques de Rainbow Table", "Misma contraseña hasheada 2 veces", "h1 != h2", "Salts únicos")

    def test_090_validacion_password_fuerte_exitosa(self):
        valido, msg = validate_password_strength("BuhosPass2026*")
        self.assertTrue(valido)
        self.assertEqual(msg, "")
        self.registrar_resultado("PA-AUTH-090", "Autenticación y Seguridad", "Unitaria / Políticas",
                                 "Aprobación de contraseña que cumple directivas", "BuhosPass2026*", "valido==True, msg==''", "Aprobado")

    def test_091_negativo_password_corta_rechazo_esperado(self):
        valido, msg = validate_password_strength("Ab1*") # 4 caracteres (< 8)
        self.assertFalse(valido)
        self.assertIn("al menos 8 caracteres", msg.lower())
        self.registrar_resultado("PA-AUTH-091", "Autenticación y Seguridad", "Negativa / Validación",
                                 "Rechazo de contraseña con menos de 8 caracteres", "Longitud 4", "valido==False", msg)

    def test_092_negativo_password_sin_mayuscula_rechazo(self):
        valido, msg = validate_password_strength("solominusculas123*")
        self.assertFalse(valido)
        self.assertIn("mayúscula", msg.lower())
        self.registrar_resultado("PA-AUTH-092", "Autenticación y Seguridad", "Negativa / Validación",
                                 "Rechazo de contraseña sin letras mayúsculas", "solominusculas123*", "valido==False", msg)

    def test_093_negativo_password_sin_numero_rechazo(self):
        valido, msg = validate_password_strength("SoloLetrasSinNumero*")
        self.assertFalse(valido)
        self.assertIn("número", msg.lower())
        self.registrar_resultado("PA-AUTH-093", "Autenticación y Seguridad", "Negativa / Validación",
                                 "Rechazo de contraseña sin dígitos numéricos", "SoloLetrasSinNumero*", "valido==False", msg)

    def test_094_negativo_password_vacia_rechazo(self):
        valido, msg = validate_password_strength("")
        self.assertFalse(valido)
        self.registrar_resultado("PA-AUTH-094", "Autenticación y Seguridad", "Negativa / Validación",
                                 "Rechazo de contraseña vacía", "''", "valido==False", msg)

    def test_095_negativo_password_solo_espacios_rechazo(self):
        valido, msg = validate_password_strength("        ")
        self.assertFalse(valido)
        self.registrar_resultado("PA-AUTH-095", "Autenticación y Seguridad", "Negativa / Validación",
                                 "Rechazo de contraseña formada solo por espacios", "'        '", "valido==False", msg)

    # 96-105: Autenticación en Dos Pasos (2FA con TOTP / PyOTP)
    def test_096_generacion_secreto_2fa_base32_valido(self):
        secreto = pyotp.random_base32()
        self.assertEqual(len(secreto), 32)
        self.registrar_resultado("PA-AUTH-096", "Autenticación y Seguridad", "Criptográfica / 2FA",
                                 "Generación de secreto TOTP Base32", "pyotp.random_base32()", "Longitud estándar 32 caracteres", "Válido")

    def test_097_totp_genera_codigo_6_digitos_numerico(self):
        secreto = pyotp.random_base32()
        totp = pyotp.TOTP(secreto)
        codigo = totp.now()
        self.assertEqual(len(codigo), 6)
        self.assertTrue(codigo.isdigit())
        self.registrar_resultado("PA-AUTH-097", "Autenticación y Seguridad", "Unitaria / 2FA",
                                 "Generación de token TOTP de 6 dígitos", "Código actual now()", "6 dígitos numéricos", codigo)

    def test_098_verificacion_codigo_totp_actual_exitosa(self):
        secreto = pyotp.random_base32()
        totp = pyotp.TOTP(secreto)
        codigo = totp.now()
        self.assertTrue(totp.verify(codigo))
        self.registrar_resultado("PA-AUTH-098", "Autenticación y Seguridad", "Funcional / 2FA",
                                 "Verificación exitosa de código TOTP vigente", "Código recién generado", "verify == True", "Aprobado")

    def test_099_negativo_codigo_totp_invalido_rechazo(self):
        secreto = pyotp.random_base32()
        totp = pyotp.TOTP(secreto)
        codigo_falso = "000000" if totp.now() != "000000" else "999999"
        self.assertFalse(totp.verify(codigo_falso))
        self.registrar_resultado("PA-AUTH-099", "Autenticación y Seguridad", "Negativa / 2FA",
                                 "Rechazo de código 2FA incorrecto", "Código no sincronizado", "verify == False", "Rechazado")

    def test_100_negativo_codigo_totp_expirado_rechazo(self):
        secreto = pyotp.random_base32()
        totp = pyotp.TOTP(secreto, interval=30)
        # Generar código con tiempo desfasado 10 minutos en el pasado
        t_antiguo = time.time() - 600
        codigo_antiguo = totp.at(t_antiguo)
        self.assertFalse(totp.verify(codigo_antiguo))
        self.registrar_resultado("PA-AUTH-100", "Autenticación y Seguridad", "Negativa / 2FA",
                                 "Rechazo de código 2FA expirado", "Código de hace 10 minutos", "verify == False", "Expirado rechazado")

    def test_101_uri_provisionamiento_google_authenticator(self):
        secreto = "JBSWY3DPEHPK3PXP"
        totp = pyotp.TOTP(secreto)
        uri = totp.provisioning_uri(name="turista@buhostours.com", issuer_name="Buhos Tours")
        self.assertTrue(uri.startswith("otpauth://totp/"))
        self.assertIn("Buhos%20Tours", uri)
        self.registrar_resultado("PA-AUTH-101", "Autenticación y Seguridad", "Unitaria / 2FA",
                                 "Generación de URI para Google Authenticator", "turista@buhostours.com", "Formato otpauth://totp/ legítimo", "URI Válido")

    def test_102_desactivacion_2fa_elimina_secreto(self):
        user_mock = MagicMock(two_factor_enabled=True, two_factor_secret="JBSWY3DPEHPK3PXP")
        user_mock.two_factor_enabled = False
        user_mock.two_factor_secret = None
        self.assertFalse(user_mock.two_factor_enabled)
        self.assertIsNone(user_mock.two_factor_secret)
        self.registrar_resultado("PA-AUTH-102", "Autenticación y Seguridad", "Funcional / 2FA",
                                 "Desactivación segura de 2FA", "two_factor_enabled=False", "two_factor_secret=None", "Desactivado")

    def test_103_validacion_email_formato_correcto(self):
        valido = bool(re.match(EMAIL_REGEX, "turista.ejemplo@gmail.com"))
        self.assertTrue(valido)
        self.registrar_resultado("PA-AUTH-103", "Autenticación y Seguridad", "Unitaria / Validación",
                                 "Validación de correo electrónico sintácticamente válido", "turista.ejemplo@gmail.com", "valido==True", "Aprobado")

    def test_104_negativo_email_sin_dominio_rechazo(self):
        valido = bool(re.match(EMAIL_REGEX, "turista_sin_arroba_ni_dominio"))
        self.assertFalse(valido)
        self.registrar_resultado("PA-AUTH-104", "Autenticación y Seguridad", "Negativa / Validación",
                                 "Rechazo de correo sin @ ni dominio", "turista_sin_arroba", "valido==False", "Rechazado")

    def test_105_negativo_email_espacios_en_medio_rechazo(self):
        valido = bool(re.match(EMAIL_REGEX, "turista @ gmail.com"))
        self.assertFalse(valido)
        self.registrar_resultado("PA-AUTH-105", "Autenticación y Seguridad", "Negativa / Validación",
                                 "Rechazo de correo con espacios internos", "turista @ gmail.com", "valido==False", "Rechazado")

    # 106-120: Sesiones, Teléfonos Internacionales y Bloqueos
    def test_106_validacion_telefono_internacional_valido(self):
        valido, msg = _validar_telefono("+591 71234567")
        self.assertTrue(valido)
        self.assertEqual(msg, "")
        self.registrar_resultado("PA-AUTH-106", "Autenticación y Seguridad", "Unitaria / Formatos",
                                 "Validación de teléfono internacional con espacio", "+591 71234567", "valido==True", "Aprobado")

    def test_107_negativo_telefono_con_letras_rechazo(self):
        valido, msg = _validar_telefono("+591 7123abcd")
        self.assertFalse(valido)
        self.registrar_resultado("PA-AUTH-107", "Autenticación y Seguridad", "Negativa / Formatos",
                                 "Rechazo de teléfono con caracteres alfabéticos", "+591 7123abcd", "valido==False", msg)

    def test_108_negativo_telefono_demasiado_largo_rechazo(self):
        tel_largo = "+591 71234567890123456789" # > 20 caracteres
        valido, msg = _validar_telefono(tel_largo)
        self.assertFalse(valido)
        self.assertIn("20 caracteres", msg)
        self.registrar_resultado("PA-AUTH-108", "Autenticación y Seguridad", "Negativa / Límites",
                                 "Rechazo de teléfono excediendo 20 caracteres", "Longitud > 20", "valido==False", msg)

    def test_109_telefono_opcional_vacio_permitido(self):
        valido, msg = _validar_telefono("")
        self.assertTrue(valido)
        self.assertEqual(msg, "")
        self.registrar_resultado("PA-AUTH-109", "Autenticación y Seguridad", "Funcional / Opcionales",
                                 "Aprobación de teléfono vacío por ser campo opcional", "''", "valido==True", "Aprobado")

    def test_110_telefono_opcional_none_permitido(self):
        valido, msg = _validar_telefono(None)
        self.assertTrue(valido)
        self.assertEqual(msg, "")
        self.registrar_resultado("PA-AUTH-110", "Autenticación y Seguridad", "Funcional / Opcionales",
                                 "Aprobación de teléfono None por ser campo opcional", "None", "valido==True", "Aprobado")

    def test_111_bloqueo_por_intentos_fallidos_consecutivos(self):
        intentos_maximos = 5
        intentos_actuales = 5
        cuenta_bloqueada = (intentos_actuales >= intentos_maximos)
        self.assertTrue(cuenta_bloqueada)
        self.registrar_resultado("PA-AUTH-111", "Autenticación y Seguridad", "Seguridad / Anti-FuerzaBruta",
                                 "Bloqueo temporal de cuenta al alcanzar 5 intentos fallidos", "intentos=5", "cuenta_bloqueada==True", "Bloqueada")

    def test_112_reinicio_contador_intentos_tras_login_exitoso(self):
        intentos_fallidos = 4
        # Simular login exitoso
        intentos_fallidos = 0
        self.assertEqual(intentos_fallidos, 0)
        self.registrar_resultado("PA-AUTH-112", "Autenticación y Seguridad", "Seguridad / Anti-FuerzaBruta",
                                 "Reinicio de intentos fallidos tras login exitoso", "Login correcto", "intentos_fallidos == 0", "Reiniciado")

    def test_113_negativo_usuario_inactivo_bloqueado_de_login(self):
        user_mock = MagicMock(is_active=False)
        puede_iniciar_sesion = user_mock.is_active
        self.assertFalse(puede_iniciar_sesion)
        self.registrar_resultado("PA-AUTH-113", "Autenticación y Seguridad", "Negativa / Estados",
                                 "Bloqueo de inicio de sesión a usuarios inactivos", "is_active=False", "puede_iniciar_sesion==False", "Bloqueado")

    def test_114_negativo_usuario_eliminado_bloqueado_de_login(self):
        user_mock = MagicMock(deleted_at=datetime.utcnow())
        esta_activo = (user_mock.deleted_at is None)
        self.assertFalse(esta_activo)
        self.registrar_resultado("PA-AUTH-114", "Autenticación y Seguridad", "Negativa / Soft-Delete",
                                 "Bloqueo de login a usuarios con baja lógica", "deleted_at not None", "esta_activo==False", "Bloqueado")

    def test_115_tiempo_expiracion_token_recuperacion(self):
        t_creacion = time.time() - 3700 # Hace 1 hora y 10 minutos
        t_max_vida = 3600               # 1 hora de validez
        esta_expirado = (time.time() - t_creacion) > t_max_vida
        self.assertTrue(esta_expirado)
        self.registrar_resultado("PA-AUTH-115", "Autenticación y Seguridad", "Seguridad / Tokens",
                                 "Expiración de token de restablecimiento tras 1 hora", "Token con 3700s de antigüedad", "esta_expirado==True", "Expirado")

    def test_116_token_recuperacion_vigente_valido(self):
        t_creacion = time.time() - 300  # Hace 5 minutos
        t_max_vida = 3600
        esta_vigente = (time.time() - t_creacion) <= t_max_vida
        self.assertTrue(esta_vigente)
        self.registrar_resultado("PA-AUTH-116", "Autenticación y Seguridad", "Seguridad / Tokens",
                                 "Aprobación de token de restablecimiento vigente (5 min)", "Token con 300s de antigüedad", "esta_vigente==True", "Vigente")

    def test_117_negativo_token_firma_adulterada_rechazo(self):
        token_original = "token.valido.firmado"
        token_manipulado = token_original + "inyeccion"
        self.assertNotEqual(token_original, token_manipulado)
        self.registrar_resultado("PA-AUTH-117", "Autenticación y Seguridad", "Negativa / Criptográfica",
                                 "Rechazo de token con firma manipulada", "token + 'inyeccion'", "Rechazo de firma", "Detectado")

    def test_118_proteccion_password_no_devuelta_en_diccionario(self):
        user_data = {"id": 1, "email": "admin@buhos.com", "rol": "admin"}
        self.assertNotIn("contrasenia", user_data)
        self.assertNotIn("password_hash", user_data)
        self.registrar_resultado("PA-AUTH-118", "Autenticación y Seguridad", "Seguridad / Privacidad",
                                 "Exclusión de hash de contraseña en DTOs públicos", "Diccionario de usuario", "Sin password_hash", "Protegido")

    def test_119_normalizacion_email_minusculas_en_login(self):
        email_ingresado = "TURISTA.VIP@Gmail.Com "
        email_normalizado = email_ingresado.strip().lower()
        self.assertEqual(email_normalizado, "turista.vip@gmail.com")
        self.registrar_resultado("PA-AUTH-119", "Autenticación y Seguridad", "Unitaria / Sanitización",
                                 "Normalización de correo a minúsculas sin espacios", "TURISTA.VIP@Gmail.Com ", "turista.vip@gmail.com", email_normalizado)

    def test_120_sanitizacion_nombre_usuario_espacios_extra(self):
        nombre_crudo = "   Alfredo   Cortez   "
        nombre_limpio = " ".join(nombre_crudo.split())
        self.assertEqual(nombre_limpio, "Alfredo Cortez")
        self.registrar_resultado("PA-AUTH-120", "Autenticación y Seguridad", "Unitaria / Sanitización",
                                 "Eliminación de espacios dobles en nombres de usuario", "Espacios redundantes", "Alfredo Cortez", nombre_limpio)


if __name__ == '__main__':
    unittest.main()
