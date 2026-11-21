# -*- coding: utf-8 -*-
"""
Módulo 05: Pruebas Automatizadas de Gestión de Usuarios y Administración (CRUD, Validación, Soft-Delete, Paginación).
Total de pruebas: 25 (Pruebas PA-USRM-151 a PA-USRM-175).
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from tests.conftest_base import BaseTestCase
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.services.usuario_service import (
    create_user_by_admin,
    update_user_by_admin,
    get_total_estadisticas,
    get_usuarios_paginados,
    EMAIL_REGEX
)


class TestUsuariosGestionAdmin(BaseTestCase):
    """Suite de 25 pruebas para el módulo de Gestión de Usuarios por el Administrador."""

    # 151-158: Creación y Validaciones Negativas
    def test_151_crear_usuario_admin_exitoso(self):
        data = {
            'nombres': 'Carlos',
            'apellidos': 'Gutiérrez',
            'email': 'carlos.admin@buhostours.com',
            'rol': 'admin'
        }
        with patch('app.models.rol.Rol.query') as q_r, \
             patch('app.models.usuario.Usuario.query') as q_u, \
             patch('app.services.email_service.enviar_credenciales_temporales'), \
             patch('app.services.usuario_service.db.session.commit'):
            q_u.filter_by.return_value.first.return_value = None
            q_r.filter_by.return_value.first.return_value = MagicMock(id_rol=1, nombre='admin')
            ok, msg, usr, pwd = create_user_by_admin(data)
            self.assertTrue(ok)
            self.assertIsNotNone(usr)
            self.assertEqual(len(pwd), 14)
        self.registrar_resultado("PA-USRM-151", "Gestión de Usuarios", "Funcional / Creación",
                                 "Creación exitosa de usuario administrador", "Datos válidos admin", "ok == True, pwd 14 chars", f"{ok}")

    def test_152_crear_usuario_agente_con_password_temporal(self):
        data = {
            'nombres': 'Valeria',
            'apellidos': 'Roca',
            'email': 'valeria.agente@buhostours.com',
            'rol': 'agente'
        }
        with patch('app.models.rol.Rol.query') as q_r, \
             patch('app.models.usuario.Usuario.query') as q_u, \
             patch('app.services.email_service.enviar_credenciales_temporales'), \
             patch('app.services.usuario_service.db.session.commit'):
            q_u.filter_by.return_value.first.return_value = None
            q_r.filter_by.return_value.first.return_value = MagicMock(id_rol=2, nombre='agente')
            ok, msg, usr, pwd = create_user_by_admin(data)
            self.assertTrue(ok)
            self.assertTrue(usr.must_change_password)
        self.registrar_resultado("PA-USRM-152", "Gestión de Usuarios", "Funcional / Creación",
                                 "Creación de agente con flag must_change_password", "Rol agente", "must_change_password == True", f"{usr.must_change_password}")

    def test_153_crear_usuario_turista_sincroniza_modelo_turista(self):
        data = {
            'nombres': 'Jean',
            'apellidos': 'Dupont',
            'email': 'jean.dupont@paris.fr',
            'rol': 'turista'
        }
        with patch('app.models.rol.Rol.query') as q_r, \
             patch('app.models.usuario.Usuario.query') as q_u, \
             patch('app.services.email_service.enviar_credenciales_temporales'), \
             patch('app.services.usuario_service.db.session.add') as mock_add, \
             patch('app.services.usuario_service.db.session.commit'):
            q_u.filter_by.return_value.first.return_value = None
            q_r.filter_by.return_value.first.return_value = MagicMock(id_rol=3, nombre='turista')
            ok, msg, usr, pwd = create_user_by_admin(data)
            self.assertTrue(ok)
            self.assertEqual(mock_add.call_count, 2)
        self.registrar_resultado("PA-USRM-153", "Gestión de Usuarios", "Integración / Sincronización",
                                 "Creación de turista añade entidad Usuario y Turista", "Rol turista", "db.session.add llamado 2 veces", "Sincronizado")

    def test_154_negativo_crear_usuario_nombre_vacio_falla(self):
        data = {'nombres': ' ', 'apellidos': 'Pérez', 'email': 'p@t.com', 'rol': 'agente'}
        ok, msg, usr, pwd = create_user_by_admin(data)
        self.assertFalse(ok)
        self.assertIn("nombre es obligatorio", msg.lower())
        self.registrar_resultado("PA-USRM-154", "Gestión de Usuarios", "Validación / Negativa",
                                 "Rechazo de creación con nombres vacíos", "nombres=' '", "ok == False", msg)

    def test_155_negativo_crear_usuario_apellidos_cortos_falla(self):
        data = {'nombres': 'Juan', 'apellidos': 'P', 'email': 'p@t.com', 'rol': 'agente'}
        ok, msg, usr, pwd = create_user_by_admin(data)
        self.assertFalse(ok)
        self.assertIn("al menos 2 caracteres", msg.lower())
        self.registrar_resultado("PA-USRM-155", "Gestión de Usuarios", "Validación / Negativa",
                                 "Rechazo de creación con apellidos menores a 2 caracteres", "apellidos='P'", "ok == False", msg)

    def test_156_negativo_crear_usuario_email_invalido_falla(self):
        data = {'nombres': 'Juan', 'apellidos': 'Pérez', 'email': 'correo_invalido_sin_arroba', 'rol': 'agente'}
        ok, msg, usr, pwd = create_user_by_admin(data)
        self.assertFalse(ok)
        self.assertIn("correo electrónico válido", msg.lower())
        self.registrar_resultado("PA-USRM-156", "Gestión de Usuarios", "Validación / Negativa",
                                 "Rechazo de formato de email no estándar", "email sin dominio", "ok == False", msg)

    def test_157_negativo_crear_usuario_email_duplicado_falla(self):
        data = {'nombres': 'Juan', 'apellidos': 'Pérez', 'email': 'existente@buhos.com', 'rol': 'agente'}
        with patch('app.models.usuario.Usuario.query') as q_u:
            q_u.filter_by.return_value.first.return_value = MagicMock(id_usuario=99)
            ok, msg, usr, pwd = create_user_by_admin(data)
            self.assertFalse(ok)
            self.assertIn("ya se encuentra registrado", msg.lower())
        self.registrar_resultado("PA-USRM-157", "Gestión de Usuarios", "Validación / Unicidad",
                                 "Bloqueo de creación con email ya existente", "email existente", "ok == False", msg)

    def test_158_negativo_crear_usuario_rol_invalido_falla(self):
        data = {'nombres': 'Juan', 'apellidos': 'Pérez', 'email': 'nuevo@buhos.com', 'rol': 'hacker'}
        with patch('app.models.usuario.Usuario.query') as q_u, \
             patch('app.models.rol.Rol.query') as q_r:
            q_u.filter_by.return_value.first.return_value = None
            q_r.filter_by.return_value.first.return_value = None
            ok, msg, usr, pwd = create_user_by_admin(data)
            self.assertFalse(ok)
            self.assertIn("no es válido", msg.lower())
        self.registrar_resultado("PA-USRM-158", "Gestión de Usuarios", "Validación / Negativa",
                                 "Bloqueo con rol inexistente en el sistema", "rol='hacker'", "ok == False", msg)

    # 159-162: Actualización de Usuarios
    def test_159_actualizar_datos_basicos_exitoso(self):
        mock_usr = MagicMock(id_usuario=10, nombres='Old', apellidos='Name', email='old@test.com', turista=None)
        data = {'nombres': 'NuevoNombre', 'apellidos': 'NuevoApellido', 'email': 'old@test.com', 'rol': 'agente'}
        with patch('app.services.usuario_service.db.session.get', return_value=mock_usr), \
             patch('app.models.usuario.Usuario.query') as q_u, \
             patch('app.models.rol.Rol.query') as q_r, \
             patch('app.services.usuario_service.db.session.commit'):
            q_u.filter.return_value.first.return_value = None
            q_r.filter_by.return_value.first.return_value = MagicMock(id_rol=2)
            ok, msg, usr = update_user_by_admin(10, data)
            self.assertTrue(ok)
            self.assertEqual(mock_usr.nombres, 'NuevoNombre')
        self.registrar_resultado("PA-USRM-159", "Gestión de Usuarios", "Funcional / Actualización",
                                 "Actualización de nombres y apellidos exitosa", "nombres='NuevoNombre'", "ok == True", "Actualizado")

    def test_160_actualizar_rol_de_agente_a_admin(self):
        mock_usr = MagicMock(id_usuario=10, id_rol=2, turista=None)
        data = {'nombres': 'Ana', 'apellidos': 'Gómez', 'email': 'ana@test.com', 'rol': 'admin'}
        with patch('app.services.usuario_service.db.session.get', return_value=mock_usr), \
             patch('app.models.usuario.Usuario.query') as q_u, \
             patch('app.models.rol.Rol.query') as q_r, \
             patch('app.services.usuario_service.db.session.commit'):
            q_u.filter.return_value.first.return_value = None
            q_r.filter_by.return_value.first.return_value = MagicMock(id_rol=1)
            ok, msg, usr = update_user_by_admin(10, data)
            self.assertTrue(ok)
            self.assertEqual(mock_usr.id_rol, 1)
        self.registrar_resultado("PA-USRM-160", "Gestión de Usuarios", "Funcional / Roles",
                                 "Promoción de rol de agente a admin", "rol='admin'", "id_rol == 1", "Promovido")

    def test_161_negativo_actualizar_email_duplicado_otro_usuario(self):
        mock_usr = MagicMock(id_usuario=10, email='usuario10@test.com')
        data = {'nombres': 'Ana', 'apellidos': 'Gómez', 'email': 'ocupado@test.com', 'rol': 'admin'}
        with patch('app.services.usuario_service.db.session.get', return_value=mock_usr), \
             patch('app.models.usuario.Usuario.query') as q_u:
            q_u.filter.return_value.first.return_value = MagicMock(id_usuario=20)
            ok, msg, usr = update_user_by_admin(10, data)
            self.assertFalse(ok)
            self.assertIn("siendo usado por otro usuario", msg.lower())
        self.registrar_resultado("PA-USRM-161", "Gestión de Usuarios", "Validación / Negativa",
                                 "Impedir colisión de email al actualizar", "email de otro usuario", "ok == False", msg)

    def test_162_negativo_actualizar_usuario_inexistente(self):
        with patch('app.services.usuario_service.db.session.get', return_value=None):
            ok, msg, usr = update_user_by_admin(999, {'nombres': 'X', 'apellidos': 'Y', 'email': 'x@y.com', 'rol': 'admin'})
            self.assertFalse(ok)
            self.assertIn("no encontrado", msg.lower())
        self.registrar_resultado("PA-USRM-162", "Gestión de Usuarios", "Validación / Negativa",
                                 "Actualizar usuario inexistente retorna error", "id_usuario=999", "ok == False", msg)

    # 163-166: Soft Delete y Reactivación
    def test_163_soft_delete_asigna_deleted_at(self):
        usr = Usuario(nombres="Luis", apellidos="Mora", email="l@t.com", id_rol=1)
        self.assertIsNone(usr.deleted_at)
        usr.deleted_at = datetime.utcnow()
        self.assertIsNotNone(usr.deleted_at)
        self.registrar_resultado("PA-USRM-163", "Gestión de Usuarios", "Auditoría / Soft-Delete",
                                 "Asignación de timestamp deleted_at para baja lógica", "deleted_at=utcnow()", "deleted_at != None", f"{usr.deleted_at}")

    def test_164_soft_delete_propiedades_is_active_e_is_deleted(self):
        usr = Usuario(nombres="Luis", apellidos="Mora", email="l@t.com", id_rol=1)
        usr.deleted_at = datetime.utcnow()
        self.assertFalse(usr.is_active)
        self.assertTrue(usr.is_deleted)
        self.registrar_resultado("PA-USRM-164", "Gestión de Usuarios", "Auditoría / Soft-Delete",
                                 "Usuario en baja lógica tiene is_active=False e is_deleted=True", "deleted_at activo", "is_active==False, is_deleted==True", "Verificado")

    def test_165_reactivacion_usuario_limpia_deleted_at(self):
        usr = Usuario(nombres="Luis", apellidos="Mora", email="l@t.com", id_rol=1)
        usr.deleted_at = datetime.utcnow()
        usr.deleted_at = None
        self.assertIsNone(usr.deleted_at)
        self.registrar_resultado("PA-USRM-165", "Gestión de Usuarios", "Auditoría / Reactivación",
                                 "Reactivación de usuario restablece deleted_at a None", "deleted_at=None", "deleted_at == None", "Reactivado")

    def test_166_usuario_reactivado_propiedades_is_active(self):
        usr = Usuario(nombres="Luis", apellidos="Mora", email="l@t.com", id_rol=1)
        usr.deleted_at = None
        self.assertTrue(usr.is_active)
        self.assertFalse(usr.is_deleted)
        self.registrar_resultado("PA-USRM-166", "Gestión de Usuarios", "Auditoría / Reactivación",
                                 "Usuario activo tiene is_active=True e is_deleted=False", "deleted_at=None", "is_active==True, is_deleted==False", "Verificado")

    # 167-172: Estadísticas y Filtros de Paginación
    def test_167_metricas_totales_estadisticas_dashboard(self):
        with patch('app.models.usuario.Usuario.query') as q_u:
            q_u.count.return_value = 15
            q_u.filter.return_value.count.side_effect = [12, 3]
            q_u.join.return_value.filter.return_value.count.side_effect = [2, 5, 5]
            stats = get_total_estadisticas()
            self.assertEqual(stats['total'], 15)
            self.assertEqual(stats['activos'], 12)
            self.assertEqual(stats['eliminados'], 3)
        self.registrar_resultado("PA-USRM-167", "Gestión de Usuarios", "Analítica / Métricas",
                                 "Métricas agregadas para tarjetas del panel admin", "Cálculo de estadísticas", "total==15, activos==12, eliminados==3", f"{stats}")

    def test_168_paginacion_filtro_activos_excluye_soft_deleted(self):
        with patch('app.models.usuario.Usuario.query') as q_u:
            mock_paginate = MagicMock()
            q_u.filter.return_value.order_by.return_value.paginate.return_value = mock_paginate
            res = get_usuarios_paginados(estado_filtro='activos')
            self.assertEqual(res, mock_paginate)
        self.registrar_resultado("PA-USRM-168", "Gestión de Usuarios", "Paginación / Filtro",
                                 "Paginación con filtro de activos", "estado_filtro='activos'", "Llamada con filtro deleted_at.is_(None)", "OK")

    def test_169_paginacion_filtro_eliminados_incluye_solo_soft_deleted(self):
        with patch('app.models.usuario.Usuario.query') as q_u:
            mock_paginate = MagicMock()
            q_u.filter.return_value.order_by.return_value.paginate.return_value = mock_paginate
            res = get_usuarios_paginados(estado_filtro='eliminados')
            self.assertEqual(res, mock_paginate)
        self.registrar_resultado("PA-USRM-169", "Gestión de Usuarios", "Paginación / Filtro",
                                 "Paginación con filtro de eliminados", "estado_filtro='eliminados'", "Llamada con filtro deleted_at.isnot(None)", "OK")

    def test_170_paginacion_busqueda_por_nombre(self):
        with patch('app.models.usuario.Usuario.query') as q_u:
            mock_filter = MagicMock()
            q_u.filter.return_value.filter.return_value.order_by.return_value.paginate.return_value = "resultado_busqueda"
            res = get_usuarios_paginados(search_query='Gonzales')
            self.assertIsNotNone(res)
        self.registrar_resultado("PA-USRM-170", "Gestión de Usuarios", "Paginación / Búsqueda",
                                 "Búsqueda insensible a mayúsculas por nombre", "search_query='Gonzales'", "Búsqueda ILIKE aplicada", "OK")

    def test_171_paginacion_filtro_por_rol_agente(self):
        with patch('app.models.usuario.Usuario.query') as q_u:
            mock_chain = MagicMock()
            q_u.filter.return_value.join.return_value.filter.return_value.order_by.return_value.paginate.return_value = "resultado_rol"
            res = get_usuarios_paginados(rol_filtro='agente')
            self.assertIsNotNone(res)
        self.registrar_resultado("PA-USRM-171", "Gestión de Usuarios", "Paginación / Roles",
                                 "Filtro estricto por rol agente", "rol_filtro='agente'", "Join con Rol.nombre == 'agente'", "OK")

    def test_172_paginacion_ordenamiento_por_fecha_desc(self):
        with patch('app.models.usuario.Usuario.query') as q_u:
            mock_chain = MagicMock()
            q_u.filter.return_value.order_by.return_value.paginate.return_value = "resultado_orden"
            res = get_usuarios_paginados(sort_by='fecha_desc')
            self.assertIsNotNone(res)
        self.registrar_resultado("PA-USRM-172", "Gestión de Usuarios", "Paginación / Orden",
                                 "Ordenamiento cronológico descendente", "sort_by='fecha_desc'", "Order by fecha_registro desc", "OK")

    # 173-175: Contraseña Temporal y Expiración
    def test_173_contrasenia_temporal_duracion_24_horas(self):
        ahora = datetime.utcnow()
        expira = ahora + timedelta(hours=24)
        delta_horas = (expira - ahora).total_seconds() / 3600.0
        self.assertAlmostEqual(delta_horas, 24.0, places=2)
        self.registrar_resultado("PA-USRM-173", "Gestión de Usuarios", "Seguridad / Expiración",
                                 "Cálculo de vigencia de clave temporal a 24 horas", "ahora + 24h", "delta == 24.0 horas", f"{delta_horas}h")

    def test_174_is_temp_password_expired_retorna_true_si_expirada(self):
        usr = Usuario(nombres="Test", apellidos="Expired", email="e@t.com", id_rol=2)
        usr.temp_password_expires_at = datetime.utcnow() - timedelta(minutes=5)
        self.assertTrue(usr.is_temp_password_expired)
        self.registrar_resultado("PA-USRM-174", "Gestión de Usuarios", "Seguridad / Expiración",
                                 "is_temp_password_expired detecta clave vencida", "expires_at = 5 min atrás", "is_temp_password_expired == True", "Expirada")

    def test_175_is_temp_password_expired_retorna_false_si_vigente(self):
        usr = Usuario(nombres="Test", apellidos="Active", email="a@t.com", id_rol=2)
        usr.temp_password_expires_at = datetime.utcnow() + timedelta(hours=12)
        self.assertFalse(usr.is_temp_password_expired)
        self.registrar_resultado("PA-USRM-175", "Gestión de Usuarios", "Seguridad / Expiración",
                                 "is_temp_password_expired aprueba clave vigente", "expires_at = +12 horas", "is_temp_password_expired == False", "Vigente")


if __name__ == '__main__':
    unittest.main()
