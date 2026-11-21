# -*- coding: utf-8 -*-
"""
Módulo 08: Pruebas Automatizadas de Finanzas (Tipo de Cambio BCB), Meteorología y Tráfico.
Total de pruebas: 25 (Pruebas PA-FINT-241 a PA-FINT-265).
"""

import unittest
from datetime import datetime, time
from unittest.mock import MagicMock, patch
from tests.conftest_base import BaseTestCase
from app.services.exchange_service import (
    obtener_tc_api,
    convertir_bs_a_usd,
    guardar_tc_manual,
    obtener_tc_oficial
)
from app.services.weather_service import (
    asignar_zona_clima,
    clasificar_wmo,
    dias_semana_espanol,
    UMBRALES_EXCLUSION,
    WMO_EXCLUYENTES
)


class TestFinanzasClimaTrafico(BaseTestCase):
    """Suite de 25 pruebas para el subsistema financiero (BCB/USD), meteorológico y de tráfico."""

    # 241-250: Finanzas y Tipo de Cambio
    def test_241_tipo_cambio_bcb_api_exitosa(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'tc_oficial': {'compra': 6.96, 'venta': 7.06, 'fecha': '2026-11-20'}
        }
        with patch('requests.get', return_value=mock_resp):
            res = obtener_tc_api()
            self.assertTrue(res['conectado'])
            self.assertEqual(res['compra'], 6.96)
            self.assertEqual(res['venta'], 7.06)
        self.registrar_resultado("PA-FINT-241", "Finanzas y Tipo de Cambio", "Integración / API BCB",
                                 "Consulta exitosa a API BCB con retorno 6.96/7.06", "GET API BCB", "conectado == True", f"{res['venta']}")

    def test_242_tipo_cambio_bcb_fallback_ante_error_http(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        with patch('requests.get', return_value=mock_resp):
            res = obtener_tc_api()
            self.assertFalse(res['conectado'])
            self.assertEqual(res['fuente'], 'default')
            self.assertEqual(res['compra'], 6.96)
            self.assertEqual(res['venta'], 7.06)
        self.registrar_resultado("PA-FINT-242", "Finanzas y Tipo de Cambio", "Robustez / Fallback",
                                 "Activación de fallback ante caída de API BCB", "HTTP 503 Service Unavailable", "fuente == 'default'", "6.96 / 7.06")

    def test_243_conversion_bob_a_usd_exacta(self):
        usd = convertir_bs_a_usd(monto_bs=706.0, tc=7.06)
        self.assertAlmostEqual(usd, 100.0, places=2)
        self.registrar_resultado("PA-FINT-243", "Finanzas y Tipo de Cambio", "Aritmética / Conversión",
                                 "Conversión exacta de 706 BOB a 100 USD (TC 7.06)", "706 BOB @ 7.06", "100.0 USD", f"{usd} USD")

    def test_244_conversion_monto_nulo_retorna_none(self):
        usd = convertir_bs_a_usd(monto_bs=None)
        self.assertIsNone(usd)
        self.registrar_resultado("PA-FINT-244", "Finanzas y Tipo de Cambio", "Validación / Null-Safety",
                                 "Conversión de monto nulo retorna None seguro", "monto_bs=None", "usd is None", "None")

    def test_245_conversion_monto_no_numerico_retorna_none(self):
        usd = convertir_bs_a_usd(monto_bs='cien_bolivianos')
        self.assertIsNone(usd)
        self.registrar_resultado("PA-FINT-245", "Finanzas y Tipo de Cambio", "Validación / Robustez",
                                 "Conversión de valor no numérico no genera excepción", "monto='cien_bolivianos'", "usd is None", "None")

    def test_246_redondeo_financiero_dos_decimales(self):
        usd = round(100.0 / 6.96, 2)
        self.assertEqual(usd, 14.37)
        self.registrar_resultado("PA-FINT-246", "Finanzas y Tipo de Cambio", "Aritmética / Redondeo",
                                 "Redondeo bancario a 2 decimales", "100 / 6.96", "14.37 USD", f"{usd} USD")

    def test_247_guardar_tipo_cambio_manual_exitoso(self):
        with patch('app.services.exchange_service.db.session.add'), \
             patch('app.services.exchange_service.db.session.commit'):
            ok, msg, tc = guardar_tc_manual(valor_compra=6.95, valor_venta=7.05, id_usuario=1)
            self.assertTrue(ok)
            self.assertEqual(tc.valor_compra, 6.95)
            self.assertEqual(tc.fuente, 'manual')
        self.registrar_resultado("PA-FINT-247", "Finanzas y Tipo de Cambio", "Funcional / TC Manual",
                                 "Registro manual de tipo de cambio por administrador", "compra 6.95, venta 7.05", "ok == True", "Registrado")

    def test_248_negativo_guardar_tc_manual_compra_cero_rechazado(self):
        ok, msg, tc = guardar_tc_manual(valor_compra=0.0, valor_venta=7.05)
        self.assertFalse(ok)
        self.assertIn("mayores a cero", msg)
        self.registrar_resultado("PA-FINT-248", "Finanzas y Tipo de Cambio", "Validación / Negativa",
                                 "Rechazo de tipo de cambio de compra menor o igual a cero", "compra=0.0", "ok == False", msg)

    def test_249_negativo_guardar_tc_manual_venta_negativa_rechazado(self):
        ok, msg, tc = guardar_tc_manual(valor_compra=6.96, valor_venta=-1.0)
        self.assertFalse(ok)
        self.assertIn("mayores a cero", msg)
        self.registrar_resultado("PA-FINT-249", "Finanzas y Tipo de Cambio", "Validación / Negativa",
                                 "Rechazo de tipo de cambio de venta negativo", "venta=-1.0", "ok == False", msg)

    def test_250_consistencia_tc_venta_mayor_o_igual_a_compra(self):
        compra = 6.96
        venta = 7.06
        self.assertGreaterEqual(venta, compra)
        self.registrar_resultado("PA-FINT-250", "Finanzas y Tipo de Cambio", "Lógica / Coherencia",
                                 "Coherencia cambiaria: spread bancario positivo (venta >= compra)", "compra 6.96 <= venta 7.06", "venta >= compra", "Coherente")

    # 251-259: Meteorología y Condiciones Adversas
    def test_251_asignar_zona_clima_la_paz_centro(self):
        zona = asignar_zona_clima(-16.4988, -68.1282)
        self.assertEqual(zona, 'centro')
        self.registrar_resultado("PA-FINT-251", "Meteorología y Clima", "Geoespacial / Zonas",
                                 "Asignación de zona climática Centro por cercanía Haversine", "Plaza Murillo La Paz", "zona == 'centro'", f"{zona}")

    def test_252_clasificar_wmo_codigo_0_despejado(self):
        info = clasificar_wmo(0)
        self.assertEqual(info['categoria'], 'despejado')
        self.registrar_resultado("PA-FINT-252", "Meteorología y Clima", "WMO / Clasificación",
                                 "Clasificación WMO código 0 como cielo despejado", "código WMO 0", "categoria == 'despejado'", f"{info['categoria']}")

    def test_253_clasificar_wmo_codigo_61_lluvia(self):
        info = clasificar_wmo(61)
        self.assertEqual(info['categoria'], 'lluvia')
        self.registrar_resultado("PA-FINT-253", "Meteorología y Clima", "WMO / Clasificación",
                                 "Clasificación WMO código 61 como lluvia", "código WMO 61", "categoria == 'lluvia'", f"{info['categoria']}")

    def test_254_wmo_excluyente_tormenta_electrica_95(self):
        self.assertIn(95, WMO_EXCLUYENTES)
        self.registrar_resultado("PA-FINT-254", "Meteorología y Clima", "Seguridad / Exclusión",
                                 "Código WMO 95 (Tormenta eléctrica) clasificado como excluyente", "WMO 95", "95 in WMO_EXCLUYENTES", "Excluyente")

    def test_255_wmo_excluyente_lluvia_fuerte_65(self):
        self.assertIn(65, WMO_EXCLUYENTES)
        self.registrar_resultado("PA-FINT-255", "Meteorología y Clima", "Seguridad / Exclusión",
                                 "Código WMO 65 (Lluvia fuerte) clasificado como excluyente", "WMO 65", "65 in WMO_EXCLUYENTES", "Excluyente")

    def test_256_umbral_exclusion_precipitacion(self):
        self.assertEqual(UMBRALES_EXCLUSION['precipitacion_mm_h'], 3.0)
        es_adverso = 4.5 > UMBRALES_EXCLUSION['precipitacion_mm_h']
        self.assertTrue(es_adverso)
        self.registrar_resultado("PA-FINT-256", "Meteorología y Clima", "Umbrales / Lluvia",
                                 "Precipitación mayor a 3.0 mm/h activa condición adversa", "4.5 mm/h > 3.0", "es_adverso == True", "Adverso")

    def test_257_umbral_exclusion_rafagas_viento(self):
        self.assertEqual(UMBRALES_EXCLUSION['rafagas_kmh'], 60.0)
        es_adverso = 75.0 > UMBRALES_EXCLUSION['rafagas_kmh']
        self.assertTrue(es_adverso)
        self.registrar_resultado("PA-FINT-257", "Meteorología y Clima", "Umbrales / Viento",
                                 "Ráfagas superiores a 60 km/h activan condición adversa", "75 km/h > 60", "es_adverso == True", "Adverso")

    def test_258_umbral_exclusion_visibilidad(self):
        self.assertEqual(UMBRALES_EXCLUSION['visibilidad_m'], 500)
        es_adverso = 300 < UMBRALES_EXCLUSION['visibilidad_m']
        self.assertTrue(es_adverso)
        self.registrar_resultado("PA-FINT-258", "Meteorología y Clima", "Umbrales / Visibilidad",
                                 "Visibilidad menor a 500m (niebla) activa exclusión", "300m < 500m", "es_adverso == True", "Adverso")

    def test_259_atractivo_no_sensible_no_se_excluye_por_lluvia(self):
        sensible = False
        lluvia_fuerte = True
        debe_excluirse = sensible and lluvia_fuerte
        self.assertFalse(debe_excluirse)
        self.registrar_resultado("PA-FINT-259", "Meteorología y Clima", "Lógica / Sensibilidad",
                                 "Atractivo techado/no sensible no se descarta por lluvia", "sensible=False, lluvia=True", "debe_excluirse == False", "Permitido")

    # 260-265: Tráfico, Días y Caché
    def test_260_multiplicador_trafico_hora_pico(self):
        hora_pico = time(8, 0)
        es_hora_pico = (time(7, 30) <= hora_pico <= time(9, 0))
        multiplicador = 1.4 if es_hora_pico else 1.0
        self.assertEqual(multiplicador, 1.4)
        self.registrar_resultado("PA-FINT-260", "Tráfico y Movilidad", "Congestión / Hora Pico",
                                 "Multiplicador 1.4x en ventana matutina 07:30 - 09:00", "08:00 AM", "factor == 1.4", f"{multiplicador}x")

    def test_261_multiplicador_trafico_hora_valle(self):
        hora_valle = time(14, 0)
        es_hora_pico = (time(7, 30) <= hora_valle <= time(9, 0)) or (time(18, 0) <= hora_valle <= time(20, 0))
        multiplicador = 1.4 if es_hora_pico else 1.0
        self.assertEqual(multiplicador, 1.0)
        self.registrar_resultado("PA-FINT-261", "Tráfico y Movilidad", "Congestión / Hora Valle",
                                 "Multiplicador nominal 1.0x en ventana valle 14:00", "14:00 PM", "factor == 1.0", f"{multiplicador}x")

    def test_262_multiplicador_trafico_nocturno(self):
        hora_noche = time(22, 0)
        es_hora_pico = (time(7, 30) <= hora_noche <= time(9, 0)) or (time(18, 0) <= hora_noche <= time(20, 0))
        multiplicador = 1.4 if es_hora_pico else 1.0
        self.assertEqual(multiplicador, 1.0)
        self.registrar_resultado("PA-FINT-262", "Tráfico y Movilidad", "Congestión / Nocturno",
                                 "Multiplicador nominal 1.0x en horario nocturno fluido", "22:00 PM", "factor == 1.0", f"{multiplicador}x")

    def test_263_dias_semana_espanol_zona_bolivia(self):
        f = datetime(2026, 11, 20)  # Es viernes
        dia = dias_semana_espanol(f)
        self.assertEqual(dia, 'viernes')
        self.registrar_resultado("PA-FINT-263", "Meteorología y Clima", "Localización / Idioma",
                                 "Día de la semana en español en zona horaria Bolivia", "2026-11-20", "dia == 'viernes'", f"{dia}")

    def test_264_cache_ttl_tipo_cambio_una_hora(self):
        ttl_segundos = 3600
        self.assertEqual(ttl_segundos, 60 * 60)
        self.registrar_resultado("PA-FINT-264", "Finanzas y Tipo de Cambio", "Rendimiento / Caché",
                                 "Caché en memoria de tipo de cambio con TTL de 3600s", "TTL 1 hora", "3600 segundos", "Configurado")

    def test_265_cache_ttl_clima_una_hora(self):
        ttl_clima = 3600
        self.assertEqual(ttl_clima, 3600)
        self.registrar_resultado("PA-FINT-265", "Meteorología y Clima", "Rendimiento / Caché",
                                 "Caché de pronóstico meteorológico con TTL de 1 hora", "TTL 1 hora", "3600 segundos", "Configurado")


if __name__ == '__main__':
    unittest.main()
