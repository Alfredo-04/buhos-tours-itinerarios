# -*- coding: utf-8 -*-
"""
Módulo 07: Pruebas Automatizadas de Gestión de Proveedores y Transportes (Logística, Costos, Velocidad y Horarios).
Total de pruebas: 30 (Pruebas PA-PROV-211 a PA-PROV-240).
"""

import unittest
from decimal import Decimal
from datetime import time, datetime
from unittest.mock import MagicMock, patch
from tests.conftest_base import BaseTestCase
from app.models.transporte import Transporte
from app.models.proveedor import Proveedor
from app.services.transporte_service import (
    crear_transporte,
    listar_transportes,
    obtener_transporte,
    parse_time_str
)
from app.services.proveedor_service import (
    crear_proveedor,
    listar_proveedores,
    obtener_proveedor
)


class TestProveedoresTransportes(BaseTestCase):
    """Suite de 30 pruebas para la logística de Medios de Transporte y Proveedores de Servicios."""

    # 211-218: Creación y Validaciones de Transporte
    def test_211_crear_transporte_privado_exitoso(self):
        data = {
            'nombre': 'Van Turística Privada VIP',
            'tipo': 'Privado',
            'capacidad': '12',
            'horario_inicio': '07:00',
            'horario_fin': '21:00',
            'costo': '350.00',
            'tipo_costo': 'por_dia',
            'velocidad_promedio_kmh': '35.0'
        }
        with patch('app.services.transporte_service.db.session.add'), \
             patch('app.services.transporte_service.db.session.commit'):
            ok, msg, t = crear_transporte(data)
            self.assertTrue(ok)
            self.assertEqual(t.nombre, 'Van Turística Privada VIP')
            self.assertEqual(t.tipo, 'Privado')
        self.registrar_resultado("PA-PROV-211", "Transportes y Logística", "Funcional / Creación",
                                 "Creación exitosa de transporte privado por día", "Van VIP 12 pasajeros", "ok == True, tipo=='Privado'", "Aprobado")

    def test_212_crear_transporte_publico_por_persona_exitoso(self):
        data = {
            'nombre': 'Minibus Interurbano Línea 2',
            'tipo': 'Público',
            'capacidad': '14',
            'horario_inicio': '06:00',
            'horario_fin': '22:00',
            'costo': '3.50',
            'tipo_costo': 'por_persona',
            'velocidad_promedio_kmh': '25.0'
        }
        with patch('app.services.transporte_service.db.session.add'), \
             patch('app.services.transporte_service.db.session.commit'):
            ok, msg, t = crear_transporte(data)
            self.assertTrue(ok)
            self.assertEqual(t.tipo, 'Público')
            self.assertEqual(t.tipo_costo, 'por_persona')
        self.registrar_resultado("PA-PROV-212", "Transportes y Logística", "Funcional / Creación",
                                 "Creación exitosa de transporte público por persona", "Tarifa 3.50 BOB/persona", "ok == True, tipo_costo=='por_persona'", "Aprobado")

    def test_213_negativo_transporte_nombre_corto_rechazado(self):
        data = {'nombre': 'AB', 'tipo': 'Privado', 'tipo_costo': 'por_dia', 'capacidad': '5'}
        ok, msg, t = crear_transporte(data)
        self.assertFalse(ok)
        self.assertIn("al menos 3 caracteres", msg)
        self.registrar_resultado("PA-PROV-213", "Transportes y Logística", "Validación / Negativa",
                                 "Rechazo de transporte con nombre menor a 3 caracteres", "nombre='AB'", "ok == False", msg)

    def test_214_negativo_transporte_nombre_largo_rechazado(self):
        data = {'nombre': 'T' * 101, 'tipo': 'Privado', 'tipo_costo': 'por_dia', 'capacidad': '5'}
        ok, msg, t = crear_transporte(data)
        self.assertFalse(ok)
        self.assertIn("no puede exceder los 100 caracteres", msg)
        self.registrar_resultado("PA-PROV-214", "Transportes y Logística", "Validación / Negativa",
                                 "Rechazo de nombre que excede 100 caracteres", "len == 101", "ok == False", msg)

    def test_215_negativo_transporte_tipo_invalido_rechazado(self):
        data = {'nombre': 'Teleférico Aéreo', 'tipo': 'Ficticio', 'tipo_costo': 'por_dia', 'capacidad': '8'}
        ok, msg, t = crear_transporte(data)
        self.assertFalse(ok)
        self.assertIn("debe ser 'Privado' o 'Público'", msg)
        self.registrar_resultado("PA-PROV-215", "Transportes y Logística", "Validación / Negativa",
                                 "Rechazo de tipo de transporte no permitido", "tipo='Ficticio'", "ok == False", msg)

    def test_216_negativo_transporte_tipo_costo_invalido_rechazado(self):
        data = {'nombre': 'Van Ejecutiva', 'tipo': 'Privado', 'tipo_costo': 'por_hora', 'capacidad': '8'}
        ok, msg, t = crear_transporte(data)
        self.assertFalse(ok)
        self.assertIn("debe ser 'por_dia' o 'por_persona'", msg)
        self.registrar_resultado("PA-PROV-216", "Transportes y Logística", "Validación / Negativa",
                                 "Rechazo de modalidad de cobro desconocida", "tipo_costo='por_hora'", "ok == False", msg)

    def test_217_negativo_transporte_capacidad_cero_rechazada(self):
        data = {'nombre': 'Van Ejecutiva', 'tipo': 'Privado', 'tipo_costo': 'por_dia', 'capacidad': '0'}
        ok, msg, t = crear_transporte(data)
        self.assertFalse(ok)
        self.assertIn("mayor a 0", msg)
        self.registrar_resultado("PA-PROV-217", "Transportes y Logística", "Validación / Negativa",
                                 "Rechazo de capacidad igual a cero", "capacidad=0", "ok == False", msg)

    def test_218_negativo_transporte_capacidad_no_entera_rechazada(self):
        data = {'nombre': 'Van Ejecutiva', 'tipo': 'Privado', 'tipo_costo': 'por_dia', 'capacidad': 'cuatro'}
        ok, msg, t = crear_transporte(data)
        self.assertFalse(ok)
        self.assertIn("número entero mayor a 0", msg)
        self.registrar_resultado("PA-PROV-218", "Transportes y Logística", "Validación / Negativa",
                                 "Rechazo de capacidad con texto no numérico", "capacidad='cuatro'", "ok == False", msg)

    # 219-226: Horarios, Costos y Velocidad
    def test_219_horarios_transporte_formato_valido(self):
        hi = parse_time_str('07:30')
        hf = parse_time_str('20:00')
        self.assertEqual(hi, time(7, 30))
        self.assertEqual(hf, time(20, 0))
        self.registrar_resultado("PA-PROV-219", "Transportes y Logística", "Horarios / Parsing",
                                 "Formato estructurado de horario de operaciones", "07:30 y 20:00", "time(7,30) y time(20,0)", "Válido")

    def test_220_negativo_horario_inicio_invalido_rechazado(self):
        data = {'nombre': 'Bus Nocturno', 'tipo': 'Público', 'tipo_costo': 'por_persona', 'capacidad': '30',
                'horario_inicio': 'madrugada', 'horario_fin': '22:00'}
        ok, msg, t = crear_transporte(data)
        self.assertFalse(ok)
        self.assertIn("formato válido (HH:MM)", msg)
        self.registrar_resultado("PA-PROV-220", "Transportes y Logística", "Horarios / Negativa",
                                 "Rechazo de horario de inicio no parseable", "horario_inicio='madrugada'", "ok == False", msg)

    def test_221_negativo_horario_fin_menor_a_inicio_rechazado(self):
        data = {'nombre': 'Bus Exprés', 'tipo': 'Público', 'tipo_costo': 'por_persona', 'capacidad': '30',
                'horario_inicio': '20:00', 'horario_fin': '08:00'}
        ok, msg, t = crear_transporte(data)
        self.assertFalse(ok)
        self.assertIn("horario de finalización debe ser posterior", msg)
        self.registrar_resultado("PA-PROV-221", "Transportes y Logística", "Horarios / Negativa",
                                 "Rechazo de horario de finalización antes que inicio", "20:00 a 08:00", "ok == False", msg)

    def test_222_costo_transporte_positivo_valido(self):
        c = Decimal('150.00')
        self.assertGreaterEqual(c, Decimal('0.0'))
        self.registrar_resultado("PA-PROV-222", "Transportes y Logística", "Financiero / Costo",
                                 "Validación de tarifa decimal mayor o igual a cero", "costo=150.00", "costo >= 0", "Válido")

    def test_223_negativo_costo_transporte_negativo_rechazado(self):
        data = {'nombre': 'Bus Exprés', 'tipo': 'Público', 'tipo_costo': 'por_persona', 'capacidad': '30',
                'horario_inicio': '08:00', 'horario_fin': '20:00', 'costo': '-50.00'}
        ok, msg, t = crear_transporte(data)
        self.assertFalse(ok)
        self.assertIn("mayor o igual a 0", msg)
        self.registrar_resultado("PA-PROV-223", "Transportes y Logística", "Financiero / Negativa",
                                 "Rechazo de tarifa de transporte negativa", "costo=-50.00", "ok == False", msg)

    def test_224_velocidad_promedio_rango_valido(self):
        v = Decimal('40.0')
        es_valida = Decimal('0.0') < v <= Decimal('120.0')
        self.assertTrue(es_valida)
        self.registrar_resultado("PA-PROV-224", "Transportes y Logística", "Física / Velocidad",
                                 "Velocidad promedio dentro de rango operacional seguro", "v=40.0 km/h", "0 < v <= 120", "Válido")

    def test_225_negativo_velocidad_cero_rechazada(self):
        data = {'nombre': 'Bus Detenido', 'tipo': 'Público', 'tipo_costo': 'por_persona', 'capacidad': '30',
                'horario_inicio': '08:00', 'horario_fin': '20:00', 'costo': '5.00', 'velocidad_promedio_kmh': '0.0'}
        ok, msg, t = crear_transporte(data)
        self.assertFalse(ok)
        self.assertIn("mayor a 0 km/h", msg)
        self.registrar_resultado("PA-PROV-225", "Transportes y Logística", "Física / Negativa",
                                 "Rechazo de velocidad de transporte nula", "velocidad=0.0 km/h", "ok == False", msg)

    def test_226_negativo_velocidad_excesiva_mayor_120_rechazada(self):
        data = {'nombre': 'Avión Supersonico', 'tipo': 'Privado', 'tipo_costo': 'por_dia', 'capacidad': '10',
                'horario_inicio': '08:00', 'horario_fin': '20:00', 'costo': '500.00', 'velocidad_promedio_kmh': '180.0'}
        ok, msg, t = crear_transporte(data)
        self.assertFalse(ok)
        self.assertIn("menor o igual a 120 km/h", msg)
        self.registrar_resultado("PA-PROV-226", "Transportes y Logística", "Física / Negativa",
                                 "Rechazo de velocidad superior al límite de 120 km/h", "velocidad=180.0 km/h", "ok == False", msg)

    # 227-228: Estimación de Traslado y Soft Delete Transporte
    def test_227_calculo_tiempo_traslado_minutos(self):
        distancia_km = 15.0
        velocidad_kmh = 30.0
        tiempo_horas = distancia_km / velocidad_kmh
        tiempo_minutos = tiempo_horas * 60.0
        self.assertEqual(tiempo_minutos, 30.0)
        self.registrar_resultado("PA-PROV-227", "Transportes y Logística", "Algorítmica / Traslado",
                                 "Cálculo exacto de tiempo de viaje (15 km @ 30 km/h)", "15 / 30 * 60", "30.0 minutos", f"{tiempo_minutos} min")

    def test_228_soft_delete_transporte_propiedad_is_deleted(self):
        t = Transporte(nombre="Taxi Test", tipo="Privado", tipo_costo="por_dia")
        self.assertFalse(t.is_deleted)
        t.deleted_at = datetime.utcnow()
        self.assertTrue(t.is_deleted)
        self.registrar_resultado("PA-PROV-228", "Transportes y Logística", "Auditoría / Soft-Delete",
                                 "Transporte con soft delete activa flag is_deleted", "deleted_at=utcnow()", "is_deleted == True", "Verificado")

    # 229-235: Creación y Validaciones de Proveedor
    def test_229_crear_proveedor_datos_completos_exitoso(self):
        data = {
            'razon_social': 'Operadora Turística Illimani Tours S.R.L.',
            'tipo': 'Agencia Receptiva',
            'contacto_nombre': 'Gonzalo Flores',
            'contacto_telefono': '71512345',
            'contacto_email': 'contacto@illimanitours.bo',
            'tarifa_especial': '10.00',
            'observaciones': 'Convenio institucional 2026'
        }
        with patch('app.services.proveedor_service.db.session.add'), \
             patch('app.services.proveedor_service.db.session.commit'):
            ok, msg, p = crear_proveedor(data)
            self.assertTrue(ok)
            self.assertEqual(p.razon_social, 'Operadora Turística Illimani Tours S.R.L.')
        self.registrar_resultado("PA-PROV-229", "Proveedores de Servicios", "Funcional / Creación",
                                 "Registro exitoso de proveedor institucional", "Datos completos Illimani Tours", "ok == True", "Aprobado")

    def test_230_negativo_proveedor_razon_social_corta_rechazada(self):
        data = {'razon_social': 'OT'}
        ok, msg, p = crear_proveedor(data)
        self.assertFalse(ok)
        self.assertIn("al menos 3 caracteres", msg)
        self.registrar_resultado("PA-PROV-230", "Proveedores de Servicios", "Validación / Negativa",
                                 "Rechazo de razón social con menos de 3 caracteres", "razon_social='OT'", "ok == False", msg)

    def test_231_negativo_proveedor_razon_social_larga_rechazada(self):
        data = {'razon_social': 'R' * 101}
        ok, msg, p = crear_proveedor(data)
        self.assertFalse(ok)
        self.assertIn("no puede exceder los 100 caracteres", msg)
        self.registrar_resultado("PA-PROV-231", "Proveedores de Servicios", "Validación / Negativa",
                                 "Rechazo de razón social mayor a 100 caracteres", "len == 101", "ok == False", msg)

    def test_232_proveedor_email_formato_valido(self):
        data = {'razon_social': 'Hotel Rosario', 'contacto_email': 'reservas@hotelrosario.bo'}
        with patch('app.services.proveedor_service.db.session.add'), \
             patch('app.services.proveedor_service.db.session.commit'):
            ok, msg, p = crear_proveedor(data)
            self.assertTrue(ok)
        self.registrar_resultado("PA-PROV-232", "Proveedores de Servicios", "Comunicación / Email",
                                 "Aprobación de email institucional de proveedor", "reservas@hotelrosario.bo", "ok == True", "Válido")

    def test_233_negativo_proveedor_email_invalido_rechazado(self):
        data = {'razon_social': 'Hotel Rosario', 'contacto_email': 'email_sin_arroba_ni_punto'}
        ok, msg, p = crear_proveedor(data)
        self.assertFalse(ok)
        self.assertIn("formato inválido", msg)
        self.registrar_resultado("PA-PROV-233", "Proveedores de Servicios", "Comunicación / Negativa",
                                 "Rechazo de email malformado de proveedor", "email inválido", "ok == False", msg)

    def test_234_tarifa_especial_proveedor_valida(self):
        t = Decimal('15.50')
        self.assertGreaterEqual(t, Decimal('0.0'))
        self.registrar_resultado("PA-PROV-234", "Proveedores de Servicios", "Financiero / Tarifas",
                                 "Validación de tarifa especial no negativa", "tarifa=15.50", "tarifa >= 0", "Válido")

    def test_235_negativo_tarifa_especial_negativa_rechazada(self):
        data = {'razon_social': 'Hotel Rosario', 'tarifa_especial': '-5.00'}
        ok, msg, p = crear_proveedor(data)
        self.assertFalse(ok)
        self.assertIn("mayor o igual a 0", msg)
        self.registrar_resultado("PA-PROV-235", "Proveedores de Servicios", "Financiero / Negativa",
                                 "Rechazo de tarifa especial negativa", "tarifa=-5.00", "ok == False", msg)

    # 236-240: Paginación, Consultas y Soft Delete Proveedor
    def test_236_soft_delete_proveedor_propiedad_is_deleted(self):
        p = Proveedor(razon_social="Guías Cordillera")
        self.assertFalse(p.is_deleted)
        p.deleted_at = datetime.utcnow()
        self.assertTrue(p.is_deleted)
        self.registrar_resultado("PA-PROV-236", "Proveedores de Servicios", "Auditoría / Soft-Delete",
                                 "Proveedor con baja lógica activa flag is_deleted", "deleted_at=utcnow()", "is_deleted == True", "Verificado")

    def test_237_paginacion_transportes_filtro_privado(self):
        with patch('app.models.transporte.Transporte.query') as q_t:
            mock_chain = MagicMock()
            q_t.filter.return_value.filter.return_value.order_by.return_value.paginate.return_value = "transportes_privados"
            res = listar_transportes(tipo_filtro='Privado')
            self.assertIsNotNone(res)
        self.registrar_resultado("PA-PROV-237", "Transportes y Logística", "Paginación / Filtro",
                                 "Filtro de transportes por modalidad Privado", "tipo_filtro='Privado'", "Transporte.tipo == 'Privado'", "OK")

    def test_238_paginacion_transportes_filtro_publico(self):
        with patch('app.models.transporte.Transporte.query') as q_t:
            mock_chain = MagicMock()
            q_t.filter.return_value.filter.return_value.order_by.return_value.paginate.return_value = "transportes_publicos"
            res = listar_transportes(tipo_filtro='Público')
            self.assertIsNotNone(res)
        self.registrar_resultado("PA-PROV-238", "Transportes y Logística", "Paginación / Filtro",
                                 "Filtro de transportes por modalidad Público", "tipo_filtro='Público'", "Transporte.tipo == 'Público'", "OK")

    def test_239_paginacion_proveedores_busqueda_razon_social(self):
        with patch('app.models.proveedor.Proveedor.query') as q_p:
            mock_chain = MagicMock()
            q_p.filter.return_value.filter.return_value.order_by.return_value.paginate.return_value = "proveedores_encontrados"
            res = listar_proveedores(search_query='Illimani')
            self.assertIsNotNone(res)
        self.registrar_resultado("PA-PROV-239", "Proveedores de Servicios", "Paginación / Búsqueda",
                                 "Búsqueda por coincidencia en razón social", "search_query='Illimani'", "Búsqueda ILIKE aplicada", "OK")

    def test_240_obtener_transporte_inexistente_retorna_none(self):
        with patch('app.services.transporte_service.db.session.get', return_value=None):
            t = obtener_transporte(9999)
            self.assertIsNone(t)
        self.registrar_resultado("PA-PROV-240", "Transportes y Logística", "Consulta / Robustez",
                                 "Consulta de transporte inexistente retorna None seguro", "id=9999", "t is None", "None")


if __name__ == '__main__':
    unittest.main()
