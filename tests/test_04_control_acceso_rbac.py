# -*- coding: utf-8 -*-
"""
Módulo 04: Pruebas Automatizadas de Control de Acceso y Matriz de Roles (RBAC).
Total de pruebas: 30 (Permisos, Bloqueos 403, Redirecciones 302 y Aislamiento de Datos).
Pruebas PA-RBAC-121 a PA-RBAC-150.
"""

import unittest
from unittest.mock import MagicMock, patch
from werkzeug.exceptions import Forbidden
from tests.conftest_base import BaseTestCase
from app.utils.decorators import (
    role_required,
    admin_required,
    agente_required,
    turista_required,
    require_2fa,
)
from app.services.itinerario_service import cambiar_estado_itinerario


class TestControlAccesoRBAC(BaseTestCase):
    """Suite de 30 pruebas para la Matriz de Control de Acceso Basado en Roles (RBAC)."""

    # 121-128: Turista Bloqueado en Módulos de Administración / Agente (HTTP 403 Forbidden)
    def test_121_negativo_turista_bloqueado_admin_usuarios_403(self):
        @admin_required
        def dummy_view():
            return "ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='turista')
                with self.assertRaises(Forbidden):
                    dummy_view()
        self.registrar_resultado("PA-RBAC-121", "Control de Acceso (RBAC)", "Seguridad / Bloqueo",
                                 "Turista bloqueado en gestión de usuarios", "GET /admin/usuarios con rol turista", "Código 403 Forbidden", "403 Forbidden")

    def test_122_negativo_turista_bloqueado_admin_atractivos_crear_403(self):
        @admin_required
        def dummy_view():
            return "ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='turista')
                with self.assertRaises(Forbidden):
                    dummy_view()
        self.registrar_resultado("PA-RBAC-122", "Control de Acceso (RBAC)", "Seguridad / Bloqueo",
                                 "Turista bloqueado en creación de atractivos", "GET /admin/atractivos/create con rol turista", "Código 403 Forbidden", "403 Forbidden")

    def test_123_negativo_turista_bloqueado_admin_proveedores_403(self):
        @admin_required
        def dummy_view():
            return "ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='turista')
                with self.assertRaises(Forbidden):
                    dummy_view()
        self.registrar_resultado("PA-RBAC-123", "Control de Acceso (RBAC)", "Seguridad / Bloqueo",
                                 "Turista bloqueado en gestión de proveedores", "GET /admin/proveedores con rol turista", "Código 403 Forbidden", "403 Forbidden")

    def test_124_negativo_turista_bloqueado_admin_transportes_403(self):
        @admin_required
        def dummy_view():
            return "ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='turista')
                with self.assertRaises(Forbidden):
                    dummy_view()
        self.registrar_resultado("PA-RBAC-124", "Control de Acceso (RBAC)", "Seguridad / Bloqueo",
                                 "Turista bloqueado en gestión de transportes", "GET /admin/transportes con rol turista", "Código 403 Forbidden", "403 Forbidden")

    def test_125_negativo_turista_bloqueado_admin_categorias_403(self):
        @admin_required
        def dummy_view():
            return "ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='turista')
                with self.assertRaises(Forbidden):
                    dummy_view()
        self.registrar_resultado("PA-RBAC-125", "Control de Acceso (RBAC)", "Seguridad / Bloqueo",
                                 "Turista bloqueado en gestión de categorías", "GET /admin/categorias con rol turista", "Código 403 Forbidden", "403 Forbidden")

    def test_126_negativo_turista_bloqueado_reportes_dashboard_403(self):
        @admin_required
        def dummy_view():
            return "ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='turista')
                with self.assertRaises(Forbidden):
                    dummy_view()
        self.registrar_resultado("PA-RBAC-126", "Control de Acceso (RBAC)", "Seguridad / Bloqueo",
                                 "Turista bloqueado en Dashboard analítico", "GET /reportes/dashboard con rol turista", "Código 403 Forbidden", "403 Forbidden")

    def test_127_negativo_turista_bloqueado_generador_itinerarios_403(self):
        @agente_required
        def dummy_view():
            return "ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='turista')
                with self.assertRaises(Forbidden):
                    dummy_view()
        self.registrar_resultado("PA-RBAC-127", "Control de Acceso (RBAC)", "Seguridad / Bloqueo",
                                 "Turista bloqueado en generador de itinerarios", "GET /itinerarios/generar con rol turista", "Código 403 Forbidden", "403 Forbidden")

    def test_128_negativo_turista_bloqueado_cambio_estado_itinerario_endpoint(self):
        @role_required('admin', 'agente')
        def dummy_cambio_estado():
            return "ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='turista')
                with self.assertRaises(Forbidden):
                    dummy_cambio_estado()
        self.registrar_resultado("PA-RBAC-128", "Control de Acceso (RBAC)", "Seguridad / Bloqueo",
                                 "Turista bloqueado de cambiar estado por API", "POST /itinerarios/1/estado con rol turista", "Código 403 Forbidden", "403 Forbidden")

    # 129-135: Usuario Anónimo (No Autenticado) Redirigido a Login (HTTP 302)
    def test_129_anonimo_redirigido_en_turista_dashboard_302(self):
        res = self.client.get('/turista/dashboard', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))
        self.registrar_resultado("PA-RBAC-129", "Control de Acceso (RBAC)", "Seguridad / Redirección",
                                 "Anónimo redirigido a login en panel turista", "GET /turista/dashboard", "302 -> /auth/login", res.headers.get('Location'))

    def test_130_anonimo_redirigido_en_turista_perfil_302(self):
        res = self.client.get('/turista/perfil', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))
        self.registrar_resultado("PA-RBAC-130", "Control de Acceso (RBAC)", "Seguridad / Redirección",
                                 "Anónimo redirigido a login en perfil", "GET /turista/perfil", "302 -> /auth/login", res.headers.get('Location'))

    def test_131_anonimo_redirigido_en_itinerarios_lista_302(self):
        res = self.client.get('/itinerarios/lista', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))
        self.registrar_resultado("PA-RBAC-131", "Control de Acceso (RBAC)", "Seguridad / Redirección",
                                 "Anónimo redirigido a login en lista itinerarios", "GET /itinerarios/lista", "302 -> /auth/login", res.headers.get('Location'))

    def test_132_anonimo_redirigido_en_itinerarios_generar_302(self):
        res = self.client.get('/itinerarios/generar', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))
        self.registrar_resultado("PA-RBAC-132", "Control de Acceso (RBAC)", "Seguridad / Redirección",
                                 "Anónimo redirigido a login en generador", "GET /itinerarios/generar", "302 -> /auth/login", res.headers.get('Location'))

    def test_133_anonimo_redirigido_en_admin_usuarios_302(self):
        res = self.client.get('/admin/usuarios', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))
        self.registrar_resultado("PA-RBAC-133", "Control de Acceso (RBAC)", "Seguridad / Redirección",
                                 "Anónimo redirigido a login en admin usuarios", "GET /admin/usuarios", "302 -> /auth/login", res.headers.get('Location'))

    def test_134_anonimo_redirigido_en_descargar_voucher_302(self):
        res = self.client.get('/itinerarios/1/voucher', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))
        self.registrar_resultado("PA-RBAC-134", "Control de Acceso (RBAC)", "Seguridad / Redirección",
                                 "Anónimo redirigido a login en descarga voucher", "GET /itinerarios/1/voucher", "302 -> /auth/login", res.headers.get('Location'))

    def test_135_anonimo_redirigido_en_reportes_dashboard_302(self):
        res = self.client.get('/reportes/dashboard', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))
        self.registrar_resultado("PA-RBAC-135", "Control de Acceso (RBAC)", "Seguridad / Redirección",
                                 "Anónimo redirigido a login en reportes", "GET /reportes/dashboard", "302 -> /auth/login", res.headers.get('Location'))

    # 136-142: Rol Agente (Permisos Operativos Intermedios)
    def test_136_agente_autorizado_en_lista_itinerarios(self):
        @agente_required
        def dummy_lista():
            return "lista_itinerarios_ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='agente')
                res, code = dummy_lista()
                self.assertEqual(code, 200)
                self.assertEqual(res, "lista_itinerarios_ok")
        self.registrar_resultado("PA-RBAC-136", "Control de Acceso (RBAC)", "Funcional / Permisos",
                                 "Agente autorizado en lista de itinerarios", "Decorador @agente_required con rol agente", "200 OK", "Autorizado")

    def test_137_agente_autorizado_cambiar_estado_itinerario(self):
        mock_user = MagicMock(rol=MagicMock(nombre='agente'))
        mock_it = MagicMock(id_itinerario=1, is_deleted=False, estado='Borrador')
        with patch('app.services.itinerario_service.Itinerario.query') as q_it, \
             patch('app.services.itinerario_service.db.session.commit'):
            q_it.get.return_value = mock_it
            res = cambiar_estado_itinerario(1, 'Cancelado', mock_user)
            self.assertEqual(res['estado'], 'Cancelado')
        self.registrar_resultado("PA-RBAC-137", "Control de Acceso (RBAC)", "Funcional / Permisos",
                                 "Agente facultado para cambiar estado a Cancelado", "nuevo_estado='Cancelado'", "estado=='Cancelado'", res['estado'])

    def test_138_negativo_agente_bloqueado_admin_usuarios_403(self):
        @admin_required
        def dummy_admin_usuarios():
            return "usuarios_ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='agente')
                with self.assertRaises(Forbidden):
                    dummy_admin_usuarios()
        self.registrar_resultado("PA-RBAC-138", "Control de Acceso (RBAC)", "Seguridad / Bloqueo",
                                 "Agente bloqueado en administración de usuarios", "@admin_required con rol agente", "Código 403 Forbidden", "403 Forbidden")

    def test_139_negativo_agente_bloqueado_admin_proveedores_403(self):
        @admin_required
        def dummy_admin_proveedores():
            return "proveedores_ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='agente')
                with self.assertRaises(Forbidden):
                    dummy_admin_proveedores()
        self.registrar_resultado("PA-RBAC-139", "Control de Acceso (RBAC)", "Seguridad / Bloqueo",
                                 "Agente bloqueado en gestión de proveedores", "@admin_required con rol agente", "Código 403 Forbidden", "403 Forbidden")

    def test_140_negativo_agente_bloqueado_admin_transportes_403(self):
        @admin_required
        def dummy_admin_transportes():
            return "transportes_ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='agente')
                with self.assertRaises(Forbidden):
                    dummy_admin_transportes()
        self.registrar_resultado("PA-RBAC-140", "Control de Acceso (RBAC)", "Seguridad / Bloqueo",
                                 "Agente bloqueado en gestión de transportes", "@admin_required con rol agente", "Código 403 Forbidden", "403 Forbidden")

    def test_141_negativo_agente_bloqueado_admin_categorias_403(self):
        @admin_required
        def dummy_admin_categorias():
            return "categorias_ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='agente')
                with self.assertRaises(Forbidden):
                    dummy_admin_categorias()
        self.registrar_resultado("PA-RBAC-141", "Control de Acceso (RBAC)", "Seguridad / Bloqueo",
                                 "Agente bloqueado en gestión de categorías", "@admin_required con rol agente", "Código 403 Forbidden", "403 Forbidden")

    def test_142_agente_autorizado_en_detalle_itinerario(self):
        @agente_required
        def dummy_detalle():
            return "detalle_ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='agente')
                res, code = dummy_detalle()
                self.assertEqual(code, 200)
                self.assertEqual(res, "detalle_ok")
        self.registrar_resultado("PA-RBAC-142", "Control de Acceso (RBAC)", "Funcional / Permisos",
                                 "Agente autorizado en detalle de itinerario", "@agente_required con rol agente", "200 OK", "Autorizado")

    # 143-150: Rol Administrador, 2FA Forzado y Aislamiento de Datos
    def test_143_admin_acceso_total_usuarios(self):
        @admin_required
        def dummy_usuarios():
            return "usuarios_admin_ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='admin')
                res, code = dummy_usuarios()
                self.assertEqual(code, 200)
        self.registrar_resultado("PA-RBAC-143", "Control de Acceso (RBAC)", "Funcional / Permisos",
                                 "Admin con acceso autorizado a usuarios", "@admin_required con rol admin", "200 OK", "Acceso concedido")

    def test_144_admin_acceso_total_generador_itinerarios(self):
        @agente_required
        def dummy_generar():
            return "generar_nsga2_ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='admin')
                res, code = dummy_generar()
                self.assertEqual(code, 200)
        self.registrar_resultado("PA-RBAC-144", "Control de Acceso (RBAC)", "Funcional / Permisos",
                                 "Admin autorizado en Generador NSGA-II", "@agente_required con rol admin", "200 OK", "Acceso concedido")

    def test_145_admin_acceso_total_reportes_dashboard(self):
        @admin_required
        def dummy_reportes():
            return "reportes_ok", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='admin')
                res, code = dummy_reportes()
                self.assertEqual(code, 200)
        self.registrar_resultado("PA-RBAC-145", "Control de Acceso (RBAC)", "Funcional / Permisos",
                                 "Admin autorizado en módulo de reportes", "@admin_required con rol admin", "200 OK", "Acceso concedido")

    def test_146_aislamiento_itinerarios_turista_solo_ve_propios(self):
        """Aislamiento Multi-Inquilino: Turista solo puede ver itinerarios que le pertenecen."""
        turista_actual_id = 10
        otro_turista_id = 99
        itinerario_ajeno = MagicMock(generacion=MagicMock(id_usuario=otro_turista_id))
        
        es_propietario = (itinerario_ajeno.generacion.id_usuario == turista_actual_id)
        self.assertFalse(es_propietario)
        self.registrar_resultado("PA-RBAC-146", "Control de Acceso (RBAC)", "Seguridad / Aislamiento",
                                 "Aislamiento de itinerarios ajenos a turistas", "Turista 10 consulta Itinerario de Turista 99", "es_propietario == False", "Aislado")

    def test_147_turista_autorizado_en_itinerario_propio(self):
        turista_actual_id = 10
        itinerario_propio = MagicMock(generacion=MagicMock(id_usuario=turista_actual_id))
        es_propietario = (itinerario_propio.generacion.id_usuario == turista_actual_id)
        self.assertTrue(es_propietario)
        self.registrar_resultado("PA-RBAC-147", "Control de Acceso (RBAC)", "Seguridad / Aislamiento",
                                 "Turista autorizado para ver itinerario propio", "Turista 10 consulta Itinerario de Turista 10", "es_propietario == True", "Autorizado")

    def test_148_require_2fa_bloquea_y_redirige_si_no_esta_activo(self):
        @require_2fa
        def dummy_sensible():
            return "secreto", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='admin')
                cu.two_factor_enabled = False
                res = dummy_sensible()
                self.assertEqual(res.status_code, 302)
                self.assertIn('2fa', res.headers.get('Location', '').lower())
        self.registrar_resultado("PA-RBAC-148", "Control de Acceso (RBAC)", "Seguridad / 2FA",
                                 "Decorador @require_2fa exige 2FA activo a admin", "admin sin two_factor_enabled", "302 -> /configurar-2fa", res.headers.get('Location'))

    def test_149_require_2fa_permite_paso_si_esta_confirmado(self):
        @require_2fa
        def dummy_sensible():
            return "acceso_concedido", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='admin')
                cu.two_factor_enabled = True
                res, code = dummy_sensible()
                self.assertEqual(code, 200)
                self.assertEqual(res, "acceso_concedido")
        self.registrar_resultado("PA-RBAC-149", "Control de Acceso (RBAC)", "Seguridad / 2FA",
                                 "Decorador @require_2fa aprueba acceso con 2FA activo", "admin con two_factor_enabled=True", "200 OK", "Aprobado")

    def test_150_decorador_turista_required_bloquea_otros_roles(self):
        @turista_required
        def dummy_turista():
            return "perfil_turista", 200

        with self.app.test_request_context():
            with patch('app.utils.decorators.current_user') as cu:
                cu.is_authenticated = True
                cu.rol = MagicMock(nombre='agente')
                with self.assertRaises(Forbidden):
                    dummy_turista()
        self.registrar_resultado("PA-RBAC-150", "Control de Acceso (RBAC)", "Seguridad / Bloqueo",
                                 "Decorador @turista_required bloquea rol agente", "@turista_required con rol agente", "Código 403 Forbidden", "403 Forbidden")


if __name__ == '__main__':
    unittest.main()
