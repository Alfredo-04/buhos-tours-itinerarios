import unittest
from datetime import time, datetime
from app import create_app, db
from app.models.atractivo import Atractivo
from app.models.transporte import Transporte
from app.services.reporte_service import (
    evaluar_lista_cotejo_itinerario,
    obtener_auditoria_lista_cotejo
)


class TestListaCotejoViabilidad(unittest.TestCase):
    """
    Pruebas unitarias e integración para la Lista de Cotejo de Viabilidad Operativa.
    Verifica las 4 condiciones dicotómicas:
    C1: Apertura y días hábiles.
    C2: Cierre de atractivos.
    C3: Suficiencia de traslados sin solapamiento.
    C4: Disponibilidad y capacidad de transporte.
    """

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_evaluacion_itinerario_viable_4_condiciones(self):
        """Verifica que un itinerario con horarios y traslados correctos sea 100% viable."""
        # Mock de atractivos y transportes en memoria
        atr_mock = type('AtractivoMock', (), {
            'id_atractivo': 101,
            'nombre': 'Mirador Killi Killi',
            'horario_apertura': time(8, 0),
            'horario_cierre': time(19, 0),
            'dias_cerrado': None,
        })()

        atr_mock2 = type('AtractivoMock', (), {
            'id_atractivo': 102,
            'nombre': 'Plaza Murillo',
            'horario_apertura': time(6, 0),
            'horario_cierre': time(22, 0),
            'dias_cerrado': 'Lunes',
        })()

        trans_mock = type('TransporteMock', (), {
            'id_transporte': 1,
            'nombre': 'Taxi',
            'tipo': 'Privado',
            'capacidad': 4,
            'horario_inicio': time(6, 0),
            'horario_fin': time(23, 0),
            'deleted_at': None,
        })()

        cat_atractivos = {101: atr_mock, 102: atr_mock2}
        cat_transportes = {1: trans_mock}

        # Secuencia válida: visita martes (no cerrado), horarios entre 09:00 y 11:30
        paradas = [
            {
                'id_atractivo': 101,
                'nombre': 'Mirador Killi Killi',
                'dia': 1,
                'orden': 1,
                'hora_llegada': '09:00',
                'hora_salida': '09:40',
                'tiempo_traslado_desde_anterior': 15,
                'id_transporte': 1,
                'fecha': '2026-11-17'  # Martes
            },
            {
                'id_atractivo': 102,
                'nombre': 'Plaza Murillo',
                'dia': 1,
                'orden': 2,
                'hora_llegada': '10:00',  # 09:40 + 20 min traslado (requiere 15 min -> suficiente)
                'hora_salida': '10:50',
                'tiempo_traslado_desde_anterior': 15,
                'id_transporte': 1,
                'fecha': '2026-11-17'
            }
        ]

        resultado = evaluar_lista_cotejo_itinerario(
            paradas=paradas,
            num_personas=2,
            cat_atractivos=cat_atractivos,
            cat_transportes=cat_transportes
        )

        self.assertTrue(resultado['c1'], "C1 debe ser True")
        self.assertTrue(resultado['c2'], "C2 debe ser True")
        self.assertTrue(resultado['c3'], "C3 debe ser True")
        self.assertTrue(resultado['c4'], "C4 debe ser True")
        self.assertTrue(resultado['es_viable'], "El itinerario debe ser viable")
        self.assertEqual(resultado['estado'], "Viable")

    def test_deteccion_conflicto_c1_apertura_o_dia_cerrado(self):
        """Verifica que si la llegada es antes de apertura o día cerrado falle C1."""
        atr_mock = type('AtractivoMock', (), {
            'id_atractivo': 201,
            'nombre': 'Museo San Francisco',
            'horario_apertura': time(10, 0),
            'horario_cierre': time(18, 0),
            'dias_cerrado': 'Domingo',
        })()

        paradas = [{
            'id_atractivo': 201,
            'nombre': 'Museo San Francisco',
            'dia': 1,
            'orden': 1,
            'hora_llegada': '09:00',  # Antes de las 10:00
            'hora_salida': '10:00',
            'tiempo_traslado_desde_anterior': 10,
            'id_transporte': 1,
            'fecha': '2026-11-15'  # Domingo
        }]

        resultado = evaluar_lista_cotejo_itinerario(
            paradas=paradas,
            num_personas=1,
            cat_atractivos={201: atr_mock},
            cat_transportes={}
        )

        self.assertFalse(resultado['c1'], "C1 debe fallar ante llegada temprana y día cerrado")
        self.assertFalse(resultado['es_viable'])
        self.assertEqual(resultado['estado'], "Con conflicto")

    def test_deteccion_conflicto_c3_traslado_insuficiente(self):
        """Verifica que si el tiempo entre paradas es menor al traslado estimado falle C3."""
        atr_mock = type('AtractivoMock', (), {
            'id_atractivo': 301,
            'nombre': 'Atractivo A',
            'horario_apertura': time(8, 0),
            'horario_cierre': time(20, 0),
            'dias_cerrado': None,
        })()

        paradas = [
            {
                'id_atractivo': 301,
                'nombre': 'Atractivo A',
                'dia': 1,
                'orden': 1,
                'hora_llegada': '09:00',
                'hora_salida': '09:50',
                'tiempo_traslado_desde_anterior': 10,
                'id_transporte': None,
            },
            {
                'id_atractivo': 301,
                'nombre': 'Atractivo A',
                'dia': 1,
                'orden': 2,
                'hora_llegada': '09:55',  # Solo 5 minutos después, pero se requieren 25
                'hora_salida': '10:45',
                'tiempo_traslado_desde_anterior': 25,
                'id_transporte': None,
            }
        ]

        resultado = evaluar_lista_cotejo_itinerario(
            paradas=paradas,
            num_personas=1,
            cat_atractivos={301: atr_mock},
            cat_transportes={}
        )

        self.assertFalse(resultado['c3'], "C3 debe fallar por tiempo insuficiente de traslado")
        self.assertFalse(resultado['es_viable'])

    def test_auditoria_lista_cotejo_servicio(self):
        """Verifica que la función global de auditoría devuelva resumen estructurado y sin errores."""
        auditoria = obtener_auditoria_lista_cotejo(fuente='auto')
        self.assertIn('resumen', auditoria)
        self.assertIn('tabla_criterios', auditoria)
        self.assertIn('itinerarios', auditoria)
        self.assertEqual(len(auditoria['tabla_criterios']), 4)
        self.assertIn('porcentaje_viabilidad', auditoria['resumen'])
