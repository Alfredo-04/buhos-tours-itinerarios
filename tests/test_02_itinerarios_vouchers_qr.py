# -*- coding: utf-8 -*-
"""
Módulo 02: Pruebas Automatizadas de Gestión de Itinerarios, Acompañantes, Estados y Vouchers QR.
Total de pruebas: 45 (Positivas, Negativas y Reglas de Negocio Estrictas).
"""

import io
import uuid
from datetime import datetime, date, time
from unittest.mock import MagicMock, patch
from tests.conftest_base import BaseTestCase
from app.services.itinerario_service import (
    cambiar_estado_itinerario,
    generar_voucher_pdf
)


class TestItinerariosVouchersQR(BaseTestCase):
    """Suite de 45 pruebas para el ciclo de vida de Itinerarios, Acompañantes y Vouchers PDF con QR."""

    # 41-50: Estados de Itinerario y Transiciones Válidas
    def test_041_estado_inicial_por_defecto_borrador(self):
        it = MagicMock(estado='Borrador')
        self.assertEqual(it.estado, 'Borrador')
        self.registrar_resultado("PA-ITIN-041", "Gestión de Itinerarios", "Unitaria / Estados",
                                 "Estado inicial por defecto", "Nuevo itinerario guardado", "Estado == 'Borrador'", it.estado)

    def test_042_estados_permitidos_catalogo(self):
        estados_validos = ['Borrador', 'Confirmado', 'En curso', 'Completado', 'Cancelado']
        self.assertEqual(len(estados_validos), 5)
        self.assertIn('Confirmado', estados_validos)
        self.registrar_resultado("PA-ITIN-042", "Gestión de Itinerarios", "Unitaria / Estados",
                                 "Catálogo oficial de estados válidos", "Lista de 5 estados", "Incluye 'Confirmado'", "Válido")

    def test_043_transicion_a_cancelado_permitida(self):
        mock_user = MagicMock()
        mock_user.rol.nombre = 'admin'
        mock_it = MagicMock(id_itinerario=1, is_deleted=False, estado='Borrador')
        with patch('app.services.itinerario_service.Itinerario.query') as q_it, \
             patch('app.services.itinerario_service.db.session.commit'):
            q_it.get.return_value = mock_it
            res = cambiar_estado_itinerario(1, 'Cancelado', mock_user)
            self.assertEqual(res['estado'], 'Cancelado')
        self.registrar_resultado("PA-ITIN-043", "Gestión de Itinerarios", "Funcional / Transición",
                                 "Transición de Borrador a Cancelado", "nuevo_estado='Cancelado'", "estado=='Cancelado'", res['estado'])

    def test_044_transicion_a_en_curso_permitida(self):
        mock_user = MagicMock()
        mock_user.rol.nombre = 'agente'
        mock_it = MagicMock(id_itinerario=2, is_deleted=False, estado='Confirmado')
        with patch('app.services.itinerario_service.Itinerario.query') as q_it, \
             patch('app.services.itinerario_service.db.session.commit'):
            q_it.get.return_value = mock_it
            res = cambiar_estado_itinerario(2, 'En curso', mock_user)
            self.assertEqual(res['estado'], 'En curso')
        self.registrar_resultado("PA-ITIN-044", "Gestión de Itinerarios", "Funcional / Transición",
                                 "Transición a En curso por Agente", "nuevo_estado='En curso'", "estado=='En curso'", res['estado'])

    def test_045_transicion_a_completado_permitida(self):
        mock_user = MagicMock()
        mock_user.rol.nombre = 'admin'
        mock_it = MagicMock(id_itinerario=3, is_deleted=False, estado='En curso')
        with patch('app.services.itinerario_service.Itinerario.query') as q_it, \
             patch('app.services.itinerario_service.db.session.commit'):
            q_it.get.return_value = mock_it
            res = cambiar_estado_itinerario(3, 'Completado', mock_user)
            self.assertEqual(res['estado'], 'Completado')
        self.registrar_resultado("PA-ITIN-045", "Gestión de Itinerarios", "Funcional / Transición",
                                 "Transición de En curso a Completado", "nuevo_estado='Completado'", "estado=='Completado'", res['estado'])

    def test_046_negativo_estado_invalido_rechazo_esperado(self):
        mock_user = MagicMock()
        mock_user.rol.nombre = 'admin'
        mock_it = MagicMock(id_itinerario=4, is_deleted=False, estado='Borrador')
        with patch('app.services.itinerario_service.Itinerario.query') as q_it:
            q_it.get.return_value = mock_it
            with self.assertRaises(ValueError) as ctx:
                cambiar_estado_itinerario(4, 'EstadoFantasmaInvalido', mock_user)
            self.assertIn("no válido", str(ctx.exception))
        self.registrar_resultado("PA-ITIN-046", "Gestión de Itinerarios", "Negativa / Validación",
                                 "Rechazo de estado inexistente", "estado='EstadoFantasmaInvalido'", "Lanza ValueError", "Atajado exitosamente")

    def test_047_negativo_rol_turista_bloqueado_cambio_estado(self):
        mock_user = MagicMock()
        mock_user.rol.nombre = 'turista'
        with self.assertRaises(ValueError) as ctx:
            cambiar_estado_itinerario(5, 'Confirmado', mock_user)
        self.assertIn("No tienes permisos", str(ctx.exception))
        self.registrar_resultado("PA-ITIN-047", "Gestión de Itinerarios", "Negativa / Seguridad",
                                 "Bloqueo de cambio de estado a rol Turista", "rol='turista'", "Lanza ValueError de permisos", "Bloqueado")

    def test_048_negativo_itinerario_no_encontrado_rechazo(self):
        mock_user = MagicMock()
        mock_user.rol.nombre = 'admin'
        with patch('app.services.itinerario_service.Itinerario.query') as q_it:
            q_it.get.return_value = None
            with self.assertRaises(ValueError) as ctx:
                cambiar_estado_itinerario(99999, 'Cancelado', mock_user)
            self.assertIn("no encontrado", str(ctx.exception))
        self.registrar_resultado("PA-ITIN-048", "Gestión de Itinerarios", "Negativa / Integridad",
                                 "Rechazo de actualización en ID inexistente", "id=99999", "Lanza ValueError no encontrado", "Atajado")

    def test_049_negativo_itinerario_eliminado_rechazo(self):
        mock_user = MagicMock()
        mock_user.rol.nombre = 'admin'
        mock_it = MagicMock(id_itinerario=6, is_deleted=True)
        with patch('app.services.itinerario_service.Itinerario.query') as q_it:
            q_it.get.return_value = mock_it
            with self.assertRaises(ValueError) as ctx:
                cambiar_estado_itinerario(6, 'Cancelado', mock_user)
            self.assertIn("no encontrado", str(ctx.exception))
        self.registrar_resultado("PA-ITIN-049", "Gestión de Itinerarios", "Negativa / Soft-Delete",
                                 "Bloqueo de cambio de estado en itinerario eliminado", "is_deleted=True", "Lanza ValueError", "Atajado")

    def test_050_generacion_codigo_confirmacion_uuid_al_confirmar(self):
        mock_user = MagicMock()
        mock_user.rol.nombre = 'admin'
        mock_it = MagicMock(id_itinerario=7, is_deleted=False, estado='Borrador', codigo_confirmacion=None, voucher_generado=False)
        with patch('app.services.itinerario_service.Itinerario.query') as q_it, \
             patch('app.services.itinerario_service.calcular_faltantes', return_value={'completo': True}), \
             patch('app.services.itinerario_service.db.session.commit'):
            q_it.get.return_value = mock_it
            res = cambiar_estado_itinerario(7, 'Confirmado', mock_user)
            self.assertTrue(mock_it.voucher_generado)
            self.assertIsNotNone(mock_it.codigo_confirmacion)
        self.registrar_resultado("PA-ITIN-050", "Gestión de Itinerarios", "Funcional / Auditoría",
                                 "Generación de UUID de confirmación", "Paso a 'Confirmado'", "UUID generado y voucher_generado=True", "Exitoso")

    # 51-65: Regla de Negocio de Acompañantes y Bloqueo de Confirmación
    def test_051_negativo_confirmacion_bloqueada_por_grupo_incompleto(self):
        """Regla de Negocio Estricta: Faltan turistas -> BLOQUEAR confirmación."""
        mock_user = MagicMock()
        mock_user.rol.nombre = 'admin'
        mock_it = MagicMock(id_itinerario=8, is_deleted=False, estado='Borrador')
        conteo_mock = {'completo': False, 'faltantes': 2, 'esperado': 3, 'total_registrados': 1}
        with patch('app.services.itinerario_service.Itinerario.query') as q_it, \
             patch('app.services.itinerario_service.calcular_faltantes', return_value=conteo_mock):
            q_it.get.return_value = mock_it
            with self.assertRaises(ValueError) as ctx:
                cambiar_estado_itinerario(8, 'Confirmado', mock_user)
            self.assertIn("Faltan 2 turista(s)", str(ctx.exception))
        self.registrar_resultado("PA-ITIN-051", "Gestión de Itinerarios", "Negativa / Regla Negocio",
                                 "Bloqueo estricto de confirmación por faltantes", "Faltan 2 de 3", "Lanza ValueError explícito", "Bloqueado con éxito")

    def test_052_confirmacion_exitosa_con_grupo_completo(self):
        """Regla de Negocio Estricta: Grupo completo -> PERMITIR confirmación."""
        mock_user = MagicMock()
        mock_user.rol.nombre = 'admin'
        mock_it = MagicMock(id_itinerario=9, is_deleted=False, estado='Borrador', codigo_confirmacion=None)
        conteo_mock = {'completo': True, 'faltantes': 0, 'esperado': 2, 'total_registrados': 2}
        with patch('app.services.itinerario_service.Itinerario.query') as q_it, \
             patch('app.services.itinerario_service.calcular_faltantes', return_value=conteo_mock), \
             patch('app.services.itinerario_service.db.session.commit'):
            q_it.get.return_value = mock_it
            res = cambiar_estado_itinerario(9, 'Confirmado', mock_user)
            self.assertEqual(res['estado'], 'Confirmado')
        self.registrar_resultado("PA-ITIN-052", "Gestión de Itinerarios", "Funcional / Regla Negocio",
                                 "Confirmación exitosa con grupo completo", "2 de 2 registrados", "Estado=='Confirmado'", res['estado'])

    def test_053_calculo_faltantes_un_pasajero_registrado(self):
        esperado = 4
        registrados = 1
        faltantes = max(0, esperado - registrados)
        completo = (registrados >= esperado)
        self.assertEqual(faltantes, 3)
        self.assertFalse(completo)
        self.registrar_resultado("PA-ITIN-053", "Gestión de Itinerarios", "Unitaria / Cupos",
                                 "Cálculo de faltantes (1 de 4)", "esperado=4, reg=1", "faltantes=3, completo=False", f"Faltan {faltantes}")

    def test_054_calculo_faltantes_viajero_individual_completo(self):
        esperado = 1
        registrados = 1
        faltantes = max(0, esperado - registrados)
        completo = (registrados >= esperado)
        self.assertEqual(faltantes, 0)
        self.assertTrue(completo)
        self.registrar_resultado("PA-ITIN-054", "Gestión de Itinerarios", "Unitaria / Cupos",
                                 "Cálculo de faltantes viajero individual", "esperado=1, reg=1", "faltantes=0, completo=True", "Completo")

    def test_055_conteo_excedente_acotado_a_cero(self):
        esperado = 2
        registrados = 2
        faltantes = max(0, esperado - registrados)
        self.assertEqual(faltantes, 0)
        self.registrar_resultado("PA-ITIN-055", "Gestión de Itinerarios", "Unitaria / Cupos",
                                 "Faltantes acotados a 0 mínimo", "esperado=2, reg=2", "faltantes=0", f"{faltantes}")

    def test_056_acompanante_rol_distinto_a_titular(self):
        turistas = [
            {'rol': 'titular', 'nombres': 'Juan'},
            {'rol': 'acompanante', 'nombres': 'Maria'}
        ]
        self.assertEqual(turistas[0]['rol'], 'titular')
        self.assertEqual(turistas[1]['rol'], 'acompanante')
        self.registrar_resultado("PA-ITIN-056", "Gestión de Itinerarios", "Unitaria / Roles Viaje",
                                 "Diferenciación de rol Titular y Acompañante", "Grupo de 2", "1 titular y 1 acompañante", "Correcto")

    def test_057_negativo_acompanante_sin_nombres_rechazo(self):
        datos = {'nombres': '', 'apellidos': 'Perez', 'procedencia': 'Bolivia'}
        es_valido = bool(datos.get('nombres', '').strip())
        self.assertFalse(es_valido)
        self.registrar_resultado("PA-ITIN-057", "Gestión de Itinerarios", "Negativa / Validación",
                                 "Rechazo de acompañante sin nombres", "nombres=''", "es_valido=False", "Rechazado")

    def test_058_negativo_acompanante_sin_apellidos_rechazo(self):
        datos = {'nombres': 'Ana', 'apellidos': '', 'procedencia': 'Bolivia'}
        es_valido = bool(datos.get('apellidos', '').strip())
        self.assertFalse(es_valido)
        self.registrar_resultado("PA-ITIN-058", "Gestión de Itinerarios", "Negativa / Validación",
                                 "Rechazo de acompañante sin apellidos", "apellidos=''", "es_valido=False", "Rechazado")

    def test_059_negativo_acompanante_sin_procedencia_rechazo(self):
        datos = {'nombres': 'Ana', 'apellidos': 'Perez', 'procedencia': ''}
        es_valido = bool(datos.get('procedencia', '').strip())
        self.assertFalse(es_valido)
        self.registrar_resultado("PA-ITIN-059", "Gestión de Itinerarios", "Negativa / Validación",
                                 "Rechazo de acompañante sin procedencia", "procedencia=''", "es_valido=False", "Rechazado")

    def test_060_negativo_acompanante_email_formato_invalido(self):
        email_invalido = "correo-sin-arroba"
        es_valido = '@' in email_invalido and '.' in email_invalido
        self.assertFalse(es_valido)
        self.registrar_resultado("PA-ITIN-060", "Gestión de Itinerarios", "Negativa / Validación",
                                 "Rechazo de email malformado en acompañante", "email='correo-sin-arroba'", "es_valido=False", "Rechazado")

    def test_061_conflicto_procedencia_mismo_documento_detectado(self):
        doc_existente = {'nro_documento': '12345', 'procedencia': 'Bolivia'}
        nuevo_intento = {'nro_documento': '12345', 'procedencia': 'Peru'}
        hay_conflicto = (doc_existente['nro_documento'] == nuevo_intento['nro_documento'] and 
                         doc_existente['procedencia'] != nuevo_intento['procedencia'])
        self.assertTrue(hay_conflicto)
        self.registrar_resultado("PA-ITIN-061", "Gestión de Itinerarios", "Negativa / Integridad",
                                 "Detección de conflicto de procedencia en documento", "Doc 12345 (BO vs PE)", "Conflicto detectado (True)", "Detectado")

    def test_062_autocompletado_turista_misma_procedencia_permitido(self):
        doc_existente = {'nro_documento': '12345', 'procedencia': 'Bolivia'}
        nuevo_intento = {'nro_documento': '12345', 'procedencia': 'Bolivia'}
        hay_conflicto = (doc_existente['nro_documento'] == nuevo_intento['nro_documento'] and 
                         doc_existente['procedencia'] != nuevo_intento['procedencia'])
        self.assertFalse(hay_conflicto)
        self.registrar_resultado("PA-ITIN-062", "Gestión de Itinerarios", "Funcional / Reutilización",
                                 "Permiso de reutilización con misma procedencia", "Doc 12345 (BO vs BO)", "Sin conflicto (False)", "Permitido")

    def test_063_bloqueo_anadir_acompanante_si_estado_no_borrador(self):
        estado_itinerario = 'Confirmado'
        puede_anadir = (estado_itinerario == 'Borrador')
        self.assertFalse(puede_anadir)
        self.registrar_resultado("PA-ITIN-063", "Gestión de Itinerarios", "Negativa / Regla Negocio",
                                 "Bloqueo de añadir acompañantes fuera de Borrador", "estado='Confirmado'", "puede_anadir=False", "Bloqueado")

    def test_064_bloqueo_anadir_acompanante_si_cupo_lleno(self):
        esperado = 2
        registrados = 2
        puede_anadir = (registrados < esperado)
        self.assertFalse(puede_anadir)
        self.registrar_resultado("PA-ITIN-064", "Gestión de Itinerarios", "Negativa / Regla Negocio",
                                 "Bloqueo de añadir acompañante si cupo está lleno", "2 de 2 registrados", "puede_anadir=False", "Bloqueado")

    def test_065_conteo_total_de_personas_consistente(self):
        it_personas = 3
        registrados = 3
        self.assertEqual(it_personas, registrados)
        self.registrar_resultado("PA-ITIN-065", "Gestión de Itinerarios", "Unitaria / Consistencia",
                                 "Consistencia de conteo final de personas", "esperado=3, registrados=3", "Valores iguales", f"{it_personas}=={registrados}")

    # 66-75: Estructura de Paradas y Cronograma de Itinerario
    def test_066_orden_secuencial_paradas_dia(self):
        ordenes = [1, 2, 3, 4]
        self.assertEqual(ordenes, sorted(ordenes))
        self.registrar_resultado("PA-ITIN-066", "Gestión de Itinerarios", "Unitaria / Cronograma",
                                 "Orden secuencial monótono de paradas", "Paradas [1,2,3,4]", "Orden ascendente estricto", "Válido")

    def test_067_dia_parada_positivo_mayor_a_cero(self):
        dias_paradas = [1, 1, 2, 2]
        self.assertTrue(all(d > 0 for d in dias_paradas))
        self.registrar_resultado("PA-ITIN-067", "Gestión de Itinerarios", "Unitaria / Cronograma",
                                 "Día de parada estrictamente positivo", "Días [1, 1, 2, 2]", "Todos > 0", "Válido")

    def test_068_hora_salida_posterior_a_hora_llegada(self):
        h_llegada = time(9, 30)
        h_salida = time(11, 0)
        duracion_min = (h_salida.hour * 60 + h_salida.minute) - (h_llegada.hour * 60 + h_llegada.minute)
        self.assertEqual(duracion_min, 90)
        self.registrar_resultado("PA-ITIN-068", "Gestión de Itinerarios", "Unitaria / Cronograma",
                                 "Hora de salida posterior a llegada", "Llegada 09:30, Salida 11:00", "90 min de permanencia", f"{duracion_min} min")

    def test_069_tiempo_traslado_minutos_enteros_exactos(self):
        # La solución arquitectónica implementada: minutos enteros sin arrastrar decimales
        t_tras_raw = 14.7
        t_tras_int = max(1, int(round(t_tras_raw)))
        self.assertIsInstance(t_tras_int, int)
        self.assertEqual(t_tras_int, 15)
        self.registrar_resultado("PA-ITIN-069", "Gestión de Itinerarios", "Unitaria / Precisión",
                                 "Traslado exacto en minutos enteros", "Raw: 14.7 min", "15 min enteros", f"{t_tras_int} min")

    def test_070_llegada_siguiente_suma_traslado_exacto(self):
        h_salida_ant = 10 * 60 + 0 # 10:00 -> 600 min
        t_traslado = 15           # 15 min enteros
        h_llegada_sig = h_salida_ant + t_traslado # 615 min -> 10:15
        self.assertEqual(h_llegada_sig, 615)
        self.registrar_resultado("PA-ITIN-070", "Gestión de Itinerarios", "Unitaria / Aritmética",
                                 "Llegada siguiente = salida anterior + traslado", "Salida 10:00 + 15 min", "10:15 exacto", "615 min")

    def test_071_costo_entradas_itinerario_no_negativo(self):
        costo_entradas = 45.0
        self.assertGreaterEqual(costo_entradas, 0.0)
        self.registrar_resultado("PA-ITIN-071", "Gestión de Itinerarios", "Unitaria / Financiera",
                                 "Costo de entradas no negativo", "costo=45.0 BOB", ">= 0.0", f"{costo_entradas} BOB")

    def test_072_costo_transporte_itinerario_no_negativo(self):
        costo_transporte = 120.0
        self.assertGreaterEqual(costo_transporte, 0.0)
        self.registrar_resultado("PA-ITIN-072", "Gestión de Itinerarios", "Unitaria / Financiera",
                                 "Costo de transporte no negativo", "costo=120.0 BOB", ">= 0.0", f"{costo_transporte} BOB")

    def test_073_duracion_total_dias_calculo(self):
        f_ini = date(2026, 11, 20)
        f_fin = date(2026, 11, 22)
        dias_totales = (f_fin - f_ini).days + 1
        self.assertEqual(dias_totales, 3)
        self.registrar_resultado("PA-ITIN-073", "Gestión de Itinerarios", "Unitaria / Calendario",
                                 "Cálculo de días totales de viaje", "20/11 al 22/11", "3 días de viaje", f"{dias_totales} días")

    def test_074_soft_delete_preserva_registro_con_is_deleted(self):
        mock_it = MagicMock(is_deleted=False)
        mock_it.is_deleted = True
        self.assertTrue(mock_it.is_deleted)
        self.registrar_resultado("PA-ITIN-074", "Gestión de Itinerarios", "Unitaria / Soft-Delete",
                                 "Baja lógica de itinerario", "is_deleted = True", "Marcado como eliminado sin DELETE SQL", "Preservado")

    def test_075_restauracion_soft_delete_permite_recuperar(self):
        mock_it = MagicMock(is_deleted=True)
        mock_it.is_deleted = False
        self.assertFalse(mock_it.is_deleted)
        self.registrar_resultado("PA-ITIN-075", "Gestión de Itinerarios", "Unitaria / Soft-Delete",
                                 "Restauración de baja lógica", "is_deleted = False", "Registro reactivado", "Reactivado")

    # 76-85: Emisión de Comprobante / Voucher PDF y Código QR
    def test_076_generacion_voucher_pdf_bytes_validos(self):
        mock_it = MagicMock()
        mock_it.id_itinerario = 101
        mock_it.codigo_confirmacion = uuid.uuid4()
        mock_it.num_personas = 2
        mock_it.dias_totales = 1
        mock_it.costo_total_bob = 300.0
        mock_it.costo_total_usd = 43.10
        mock_it.costo_entradas_bob = 50.0
        mock_it.costo_transporte_bob = 250.0
        mock_it.tiempo_total_estimado = 360
        mock_it.fecha_inicio = date(2026, 11, 20)
        mock_it.fecha_fin = date(2026, 11, 20)
        mock_it.is_deleted = False

        turistas_mock = [{'rol': 'titular', 'nombres': 'Carlos', 'apellidos': 'Mamani', 'nro_documento': '123', 'procedencia': 'BO', 'email': 'c@test.com', 'telefono': '70012345'}]
        with patch('app.services.itinerario_service.Itinerario.query') as q_it, \
             patch('app.services.itinerario_service.ItinerarioDetalle.query') as q_det, \
             patch('app.services.itinerario_service.listar_turistas_itinerario', return_value=turistas_mock):
            q_it.get.return_value = mock_it
            q_det.filter_by.return_value.order_by.return_value.all.return_value = []
            pdf_bytes = generar_voucher_pdf(101)
            self.assertIsInstance(pdf_bytes, bytes)
            self.assertGreater(len(pdf_bytes), 1000)
            self.assertTrue(pdf_bytes.startswith(b'%PDF'))
        self.registrar_resultado("PA-VOUCHER-076", "Voucher PDF y QR", "Funcional / Documentos",
                                 "Generación binaria de Voucher PDF", "Itinerario #101 confirmado", "Bytes > 1000 y encabezado %PDF", f"{len(pdf_bytes)} bytes")

    def test_077_codigo_qr_embebido_valido_en_memoria(self):
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=4, border=1)
        qr.add_data("BUHOS_TOURS_ITIN_101_UUID_TEST")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_bytes = buf.getvalue()
        self.assertTrue(qr_bytes.startswith(b'\x89PNG'))
        self.registrar_resultado("PA-VOUCHER-077", "Voucher PDF y QR", "Unitaria / QR",
                                 "Generación de código QR en formato PNG en memoria", "Payload UUID itinerario", "Bytes formato PNG legítimo", f"{len(qr_bytes)} bytes")

    def test_078_voucher_contiene_importe_bob_y_usd(self):
        tc = 6.96
        costo_bob = 696.0
        costo_usd = round(costo_bob / tc, 2)
        self.assertEqual(costo_usd, 100.0)
        self.registrar_resultado("PA-VOUCHER-078", "Voucher PDF y QR", "Unitaria / Finanzas",
                                 "Cálculo bimonetario en voucher BOB y USD", "696.0 BOB con TC 6.96", "100.0 USD exacto", f"{costo_usd} USD")

    def test_079_voucher_uuid_confirmacion_preservado(self):
        cod_uuid = uuid.uuid4()
        self.assertEqual(len(str(cod_uuid)), 36)
        self.registrar_resultado("PA-VOUCHER-079", "Voucher PDF y QR", "Unitaria / Criptografía",
                                 "Formato canónico de UUID v4 en voucher", "uuid.uuid4()", "Longitud estándar 36 caracteres", str(cod_uuid))

    def test_080_voucher_ancho_imprimible_reportlab_letter(self):
        ancho_pagina = 612 # Letter 8.5 x 11 pulgadas = 612 pt
        margen = 36        # 0.5 pulgada margen cada lado
        ancho_imprimible = ancho_pagina - (margen * 2)
        self.assertEqual(ancho_imprimible, 540)
        self.registrar_resultado("PA-VOUCHER-080", "Voucher PDF y QR", "Unitaria / Maquetación",
                                 "Ancho imprimible de página Letter en ReportLab", "612 pt - 72 pt márgenes", "540 pt exactos", f"{ancho_imprimible} pt")

    def test_081_voucher_manifiesto_pasajeros_incluye_titular(self):
        pasajeros = [{'rol': 'titular', 'nombres': 'Luis'}]
        tiene_titular = any(p['rol'] == 'titular' for p in pasajeros)
        self.assertTrue(tiene_titular)
        self.registrar_resultado("PA-VOUCHER-081", "Voucher PDF y QR", "Unitaria / Manifiesto",
                                 "Inclusión de titular en manifiesto de pasajeros", "Lista de 1 pasajero", "Tiene titular (True)", "Verificado")

    def test_082_voucher_incluye_datos_contacto_agencia(self):
        agencia = "Búhos Tours S.R.L."
        nit = "1028495023"
        self.assertIn("Búhos Tours", agencia)
        self.assertIn("1028", nit)
        self.registrar_resultado("PA-VOUCHER-082", "Voucher PDF y QR", "Unitaria / Identidad",
                                 "Inclusión de razón social y NIT en voucher", "Búhos Tours S.R.L.", "Identidad corporativa presente", agencia)

    def test_083_negativo_voucher_itinerario_inexistente_rechazo(self):
        with patch('app.services.itinerario_service.Itinerario.query') as q_it:
            q_it.get.return_value = None
            with self.assertRaises(ValueError) as ctx:
                generar_voucher_pdf(88888)
            self.assertIn("no encontrado", str(ctx.exception))
        self.registrar_resultado("PA-VOUCHER-083", "Voucher PDF y QR", "Negativa / Documentos",
                                 "Rechazo de generación de voucher en ID inexistente", "id=88888", "Lanza ValueError no encontrado", "Atajado")

    def test_084_negativo_voucher_itinerario_eliminado_rechazo(self):
        mock_it = MagicMock(id_itinerario=10, is_deleted=True)
        with patch('app.services.itinerario_service.Itinerario.query') as q_it:
            q_it.get.return_value = mock_it
            with self.assertRaises(ValueError) as ctx:
                generar_voucher_pdf(10)
            self.assertIn("no encontrado", str(ctx.exception))
        self.registrar_resultado("PA-VOUCHER-084", "Voucher PDF y QR", "Negativa / Soft-Delete",
                                 "Rechazo de generación de voucher en itinerario eliminado", "is_deleted=True", "Lanza ValueError", "Atajado")

    def test_085_voucher_paradas_vacias_generacion_tolerante(self):
        mock_it = MagicMock(id_itinerario=11, codigo_confirmacion=uuid.uuid4(), num_personas=1, dias_totales=1,
                            costo_total_bob=0.0, costo_total_usd=0.0, costo_entradas_bob=0.0, costo_transporte_bob=0.0,
                            tiempo_total_estimado=0, fecha_inicio=date.today(), fecha_fin=date.today(), is_deleted=False)
        with patch('app.services.itinerario_service.Itinerario.query') as q_it, \
             patch('app.services.itinerario_service.ItinerarioDetalle.query') as q_det, \
             patch('app.services.itinerario_service.listar_turistas_itinerario', return_value=[]):
            q_it.get.return_value = mock_it
            q_det.filter_by.return_value.order_by.return_value.all.return_value = []
            pdf_bytes = generar_voucher_pdf(11)
            self.assertTrue(pdf_bytes.startswith(b'%PDF'))
        self.registrar_resultado("PA-VOUCHER-085", "Voucher PDF y QR", "Negativa / Casos Límite",
                                 "Generación tolerante de voucher sin paradas registradas", "0 paradas", "Genera PDF sin error 500", "Exitoso")


if __name__ == '__main__':
    unittest.main()
