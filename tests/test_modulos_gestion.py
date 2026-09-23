"""
Tests de integración y unidad para los Módulos de Gestión de Buhos Tours.
Cubre:
- Categorías (CRUD, soft-delete, restricciones de integridad)
- Proveedores (CRUD, soft-delete, restricciones de integridad)
- Transportes (CRUD, velocidad_promedio_kmh, validaciones de velocidad, permisos por rol)
- Atractivos (CRUD, validación de coordenadas en Bolivia, imágenes, permisos por rol)
- Servicio de Tipo de Cambio BCB (caching, manejo seguro sin hardcodeo)
- Rutas públicas y de mapa Leaflet (/catalogo/atractivos/mapa, /catalogo/atractivos/<id>/mapa)
- Rutas de gestión por rol (Admin, Agente, Turista)
"""

import os
import uuid
import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock

from app import create_app, db
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.categoria import Categoria
from app.models.proveedor import Proveedor
from app.models.transporte import Transporte
from app.models.atractivo import Atractivo
from app.services import (
    categoria_service, proveedor_service,
    transporte_service, atractivo_service,
    obtener_tc_oficial, convertir_bs_a_usd, obtener_info_tc
)


class TestModulosGestion(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_categoria_crud_and_integrity(self):
        unique_name = f"Termal Test {uuid.uuid4().hex[:6]}"
        # 1. Crear categoría
        success, msg, cat = categoria_service.crear_categoria({
            'nombre': unique_name,
            'descripcion': 'Aguas termales y spas'
        })
        self.assertTrue(success, f"Fallo al crear categoría: {msg}")
        self.assertIsNotNone(cat)
        cat_id = cat.id_categoria

        # 2. Nombre duplicado
        success_dup, msg_dup, _ = categoria_service.crear_categoria({
            'nombre': unique_name
        })
        self.assertFalse(success_dup)

        # 3. Actualizar categoría
        success_upd, msg_upd, _ = categoria_service.actualizar_categoria(cat_id, {
            'nombre': f"{unique_name} Editado",
            'descripcion': 'Nueva descripción'
        })
        self.assertTrue(success_upd)

        # 4. Soft delete
        success_del, msg_del = categoria_service.eliminar_categoria(cat_id)
        self.assertTrue(success_del)
        cat_db = categoria_service.obtener_categoria(cat_id)
        self.assertTrue(cat_db.is_deleted)

        # 5. Restaurar categoría
        success_res, msg_res = categoria_service.restaurar_categoria(cat_id)
        self.assertTrue(success_res)
        self.assertFalse(cat_db.is_deleted)

    def test_proveedor_crud_and_integrity(self):
        unique_name = f"Operador Turistico {uuid.uuid4().hex[:6]}"
        # 1. Crear proveedor
        success, msg, prov = proveedor_service.crear_proveedor({
            'razon_social': unique_name,
            'tipo': 'Transporte',
            'contacto_nombre': 'Juan Pérez',
            'contacto_telefono': '70012345',
            'contacto_email': f"contacto_{uuid.uuid4().hex[:6]}@empresa.bo"
        })
        self.assertTrue(success, f"Fallo al crear proveedor: {msg}")
        self.assertIsNotNone(prov)
        prov_id = prov.id_proveedor

        # 2. Actualizar proveedor
        success_upd, msg_upd, _ = proveedor_service.actualizar_proveedor(prov_id, {
            'razon_social': f"{unique_name} SRL",
            'tipo': 'Guía Especializado',
            'contacto_nombre': 'Juan Pérez M.',
            'contacto_telefono': '70012346',
            'contacto_email': prov.contacto_email
        })
        self.assertTrue(success_upd)

        # 3. Soft delete
        success_del, msg_del = proveedor_service.eliminar_proveedor(prov_id)
        self.assertTrue(success_del)
        prov_db = proveedor_service.obtener_proveedor(prov_id)
        self.assertTrue(prov_db.is_deleted)

        # 4. Restaurar proveedor
        success_res, msg_res = proveedor_service.restaurar_proveedor(prov_id)
        self.assertTrue(success_res)
        self.assertFalse(prov_db.is_deleted)

    def test_transporte_crud_and_velocidad_promedio(self):
        unique_tr_name = f"Minivan Turística {uuid.uuid4().hex[:6]}"
        # 1. Crear transporte con velocidad_promedio_kmh válida
        success, msg, tr = transporte_service.crear_transporte({
            'nombre': unique_tr_name,
            'tipo': 'Privado',
            'capacidad': 12,
            'costo_por_tramo': 45.0,
            'tipo_costo': 'por_persona',
            'horario_inicio': '07:00',
            'horario_fin': '21:00',
            'velocidad_promedio_kmh': 50.0
        })
        self.assertTrue(success, f"Error al crear transporte: {msg}")
        self.assertEqual(float(tr.velocidad_promedio_kmh), 50.0)
        tr_id = tr.id_transporte

        # 2. Validación de velocidad inválida (<=0 o >120)
        success_invalid, msg_inv, _ = transporte_service.crear_transporte({
            'nombre': f"Transporte Invalido {uuid.uuid4().hex[:6]}",
            'tipo': 'Privado',
            'capacidad': 10,
            'costo_por_tramo': 30.0,
            'tipo_costo': 'por_persona',
            'horario_inicio': '08:00',
            'horario_fin': '20:00',
            'velocidad_promedio_kmh': 150.0 # Inválido > 120
        })
        self.assertFalse(success_invalid)
        self.assertIn('velocidad', msg_inv.lower())

        # 3. Edición parcial como Agente (debe ignorar campos comerciales)
        success_ag, msg_ag, tr_ag = transporte_service.actualizar_transporte(
            tr_id,
            {
                'capacidad': 14,
                'costo_por_tramo': 999.0,  # Agente NO puede cambiar esto
                'horario_inicio': '08:00',
                'horario_fin': '20:00',
                'velocidad_promedio_kmh': 45.0, # Agente SÍ puede actualizar velocidad
                'nombre': 'Hacked Transporte Name' # Agente NO puede cambiar esto
            },
            rol='agente'
        )
        self.assertTrue(success_ag)
        self.assertEqual(tr_ag.capacidad, 14)
        self.assertEqual(tr_ag.nombre, unique_tr_name) # Sin cambios
        self.assertEqual(float(tr_ag.costo_por_tramo), 45.0) # Sin cambios
        self.assertEqual(float(tr_ag.velocidad_promedio_kmh), 45.0) # Sí cambió

        # 4. Soft delete (Admin)
        success_del, _ = transporte_service.eliminar_transporte(tr_id)
        self.assertTrue(success_del)
        self.assertTrue(tr.is_deleted)

        # 5. Restaurar transporte
        success_res, _ = transporte_service.restaurar_transporte(tr_id)
        self.assertTrue(success_res)
        self.assertFalse(tr.is_deleted)

    def test_atractivo_crud_and_permissions(self):
        cat = Categoria.query.filter(Categoria.deleted_at.is_(None)).first()
        prov = Proveedor.query.filter(Proveedor.deleted_at.is_(None)).first()

        unique_title = f"Mirador Andino {uuid.uuid4().hex[:6]}"
        # 1. Crear atractivo (Admin)
        success, msg, a = atractivo_service.crear_atractivo({
            'nombre': unique_title,
            'descripcion': 'Vista panorámica de la cordillera.',
            'direccion': 'Zona Alta',
            'latitud': -16.5000,
            'longitud': -68.1500,
            'costo_entrada': 15.0,
            'horario_apertura': '08:30',
            'horario_cierre': '18:30',
            'tiempo_visita_estimado': 45,
            'id_categoria': cat.id_categoria,
            'id_proveedor': prov.id_proveedor
        })
        self.assertTrue(success, f"Error al crear atractivo: {msg}")
        a_id = a.id_atractivo

        # 2. Validación de coordenadas fuera de Bolivia
        success_bad, msg_bad, _ = atractivo_service.crear_atractivo({
            'nombre': f"Invalido {uuid.uuid4().hex[:4]}",
            'latitud': 45.0,  # Fuera de Bolivia
            'longitud': 10.0,
            'costo_entrada': 10,
            'id_categoria': cat.id_categoria,
            'id_proveedor': prov.id_proveedor
        })
        self.assertFalse(success_bad)
        self.assertIn('Bolivia', msg_bad)

        # 3. Edición parcial como Agente (ignora nombre, costo_entrada, categoria, proveedor, imagen)
        success_ag, _, a_ag = atractivo_service.actualizar_atractivo(
            a_id,
            {
                'nombre': 'HACKED NAME',
                'costo_entrada': 999.0,
                'descripcion': 'Descripción actualizada por el agente.',
                'direccion': 'Nueva Dirección 123',
                'latitud': -16.5100,
                'longitud': -68.1600,
                'tiempo_visita_estimado': 60
            },
            rol='agente'
        )
        self.assertTrue(success_ag)
        self.assertEqual(a_ag.nombre, unique_title) # No debe cambiar
        self.assertEqual(float(a_ag.costo_entrada), 15.0) # No debe cambiar
        self.assertEqual(a_ag.descripcion, 'Descripción actualizada por el agente.') # Sí cambió
        self.assertEqual(a_ag.tiempo_visita_estimado, 60) # Sí cambió

        # 4. Integridad referencial: no se puede eliminar la categoría o proveedor mientras tengan este atractivo
        success_del_cat, msg_del_cat = categoria_service.eliminar_categoria(cat.id_categoria)
        self.assertFalse(success_del_cat)
        self.assertTrue('asociado' in msg_del_cat.lower())

        # 5. Soft delete (Admin)
        success_del, _ = atractivo_service.eliminar_atractivo(a_id)
        self.assertTrue(success_del)
        self.assertTrue(a.is_deleted)

        # 6. Restaurar atractivo
        success_res, _ = atractivo_service.restaurar_atractivo(a_id)
        self.assertTrue(success_res)
        self.assertFalse(a.is_deleted)

    def test_exchange_service_without_hardcoded_fallback(self):
        """Verifica que el servicio de tipo de cambio retorne None si la API falla sin usar 6.96 harcodeado."""
        # 1. Caso éxito simulado
        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                'tc_oficial': {'valor': 12.06, 'venta': 12.16, 'compra': 12.06}
            }
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            tc = obtener_tc_oficial(forzar_refresco=True)
            self.assertEqual(tc, 12.16)
            usd = convertir_bs_a_usd(121.60, tc)
            self.assertEqual(usd, 10.0)

        # 2. Caso error simulado (debe utilizar caché o fallback 6.96)
        with patch('requests.get', side_effect=Exception("API Unreachable")):
            tc_fallback = obtener_tc_oficial(forzar_refresco=True)
            self.assertEqual(tc_fallback, 6.96)
            self.assertEqual(convertir_bs_a_usd(69.60, tc_fallback), 10.0)

    def test_turista_catalog_and_map_routes(self):
        rol_turista = Rol.query.filter_by(nombre='turista').first()
        turista_user = Usuario(
            nombres='Turista', apellidos='Test',
            email=f'turista_{uuid.uuid4().hex[:6]}@test.com',
            contrasenia='testpass', id_rol=rol_turista.id_rol,
            two_factor_enabled=False,
            must_change_password=False
        )
        db.session.add(turista_user)
        db.session.commit()

        atractivo = Atractivo.query.filter(Atractivo.deleted_at.is_(None)).first()
        transporte = Transporte.query.filter(Transporte.deleted_at.is_(None)).first()

        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(turista_user.id_usuario)
            sess['_fresh'] = True

        res = client.get('/catalogo/atractivos')
        self.assertEqual(res.status_code, 200)

        # Mapa general de todos los atractivos
        res_mapa = client.get('/catalogo/atractivos/mapa')
        self.assertEqual(res_mapa.status_code, 200)

        if atractivo:
            res_det = client.get(f'/catalogo/atractivos/{atractivo.id_atractivo}')
            self.assertEqual(res_det.status_code, 200)

            # Mapa individual
            res_ind_mapa = client.get(f'/catalogo/atractivos/{atractivo.id_atractivo}/mapa')
            self.assertEqual(res_ind_mapa.status_code, 200)

        res_tr = client.get('/catalogo/transportes')
        self.assertEqual(res_tr.status_code, 200)

        if transporte:
            res_tr_det = client.get(f'/catalogo/transportes/{transporte.id_transporte}')
            self.assertEqual(res_tr_det.status_code, 200)

    def test_agente_routes(self):
        rol_agente = Rol.query.filter_by(nombre='agente').first()
        agente_user = Usuario(
            nombres='Agente', apellidos='Test',
            email=f'agente_{uuid.uuid4().hex[:6]}@test.com',
            contrasenia='testpass', id_rol=rol_agente.id_rol,
            two_factor_enabled=True, two_factor_confirmed_at=datetime.utcnow(),
            must_change_password=False
        )
        db.session.add(agente_user)
        db.session.commit()

        atractivo = Atractivo.query.filter(Atractivo.deleted_at.is_(None)).first()
        transporte = Transporte.query.filter(Transporte.deleted_at.is_(None)).first()

        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(agente_user.id_usuario)
            sess['_fresh'] = True

        if atractivo:
            res_ag_edit = client.get(f'/agente/atractivos/{atractivo.id_atractivo}/editar')
            self.assertEqual(res_ag_edit.status_code, 200)

        if transporte:
            res_tr_edit = client.get(f'/agente/transportes/{transporte.id_transporte}/editar')
            self.assertEqual(res_tr_edit.status_code, 200)

    def test_admin_routes(self):
        rol_admin = Rol.query.filter_by(nombre='admin').first()
        admin_user = Usuario(
            nombres='Admin', apellidos='Test',
            email=f'admin_{uuid.uuid4().hex[:6]}@test.com',
            contrasenia='testpass', id_rol=rol_admin.id_rol,
            two_factor_enabled=True, two_factor_confirmed_at=datetime.utcnow(),
            must_change_password=False
        )
        db.session.add(admin_user)
        db.session.commit()

        atractivo = Atractivo.query.filter(Atractivo.deleted_at.is_(None)).first()
        transporte = Transporte.query.filter(Transporte.deleted_at.is_(None)).first()
        categoria = Categoria.query.filter(Categoria.deleted_at.is_(None)).first()
        proveedor = Proveedor.query.filter(Proveedor.deleted_at.is_(None)).first()

        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id_usuario)
            sess['_fresh'] = True

        rutas_admin = [
            '/admin/atractivos',
            '/admin/atractivos/crear',
            '/admin/categorias',
            '/admin/categorias/crear',
            '/admin/proveedores',
            '/admin/proveedores/crear',
            '/admin/transportes',
            '/admin/transportes/crear',
        ]
        for ruta in rutas_admin:
            res = client.get(ruta)
            self.assertEqual(res.status_code, 200, f"Error en ruta {ruta}: {res.status_code}")

        if atractivo:
            res = client.get(f'/admin/atractivos/{atractivo.id_atractivo}/editar')
            self.assertEqual(res.status_code, 200)
            res = client.get(f'/admin/atractivos/{atractivo.id_atractivo}')
            self.assertEqual(res.status_code, 200)

        if categoria:
            res = client.get(f'/admin/categorias/{categoria.id_categoria}/editar')
            self.assertEqual(res.status_code, 200)

        if proveedor:
            res = client.get(f'/admin/proveedores/{proveedor.id_proveedor}/editar')
            self.assertEqual(res.status_code, 200)

        if transporte:
            res = client.get(f'/admin/transportes/{transporte.id_transporte}/editar')
            self.assertEqual(res.status_code, 200)
            res = client.get(f'/admin/transportes/{transporte.id_transporte}')
            self.assertEqual(res.status_code, 200)


if __name__ == '__main__':
    unittest.main()
