import unittest
from app.services.nsga2_service import haversine_km, ejecutar_nsga2


class TestNSGA2Service(unittest.TestCase):
    """
    Pruebas unitarias para el motor puro NSGA-II y la función de cálculo geodésico Haversine.
    """

    def setUp(self):
        self.atractivos_muestra = [
            {
                "id": 13,
                "nombre": "Plaza San Francisco",
                "lat": -16.4962,
                "lon": -68.1353,
                "tiempo_visita": 45,
                "categoria": "Cultural",
                "costo_entrada": 0.0,
            },
            {
                "id": 14,
                "nombre": "Calle Jaen",
                "lat": -16.4922,
                "lon": -68.1358,
                "tiempo_visita": 60,
                "categoria": "Urbano",
                "costo_entrada": 0.0,
            },
            {
                "id": 15,
                "nombre": "Mirador Killi Killi",
                "lat": -16.4954,
                "lon": -68.1273,
                "tiempo_visita": 45,
                "categoria": "Naturaleza",
                "costo_entrada": 0.0,
            },
            {
                "id": 16,
                "nombre": "Valle de la Luna",
                "lat": -16.5672,
                "lon": -68.0944,
                "tiempo_visita": 90,
                "categoria": "Naturaleza",
                "costo_entrada": 15.0,
            },
            {
                "id": 17,
                "nombre": "Museo de la Coca",
                "lat": -16.49757,
                "lon": -68.1383,
                "tiempo_visita": 60,
                "categoria": "Cultural",
                "costo_entrada": 20.0,
            },
        ]

        self.transportes_muestra = [
            {
                "id": 7,
                "nombre": "Mi Teleférico - Red Metropolitana",
                "velocidad_promedio_kmh": 20.0,
                "tipo": "Público",
                "tipo_costo": "por_persona",
                "costo_por_tramo": 3.0,
            },
            {
                "id": 10,
                "nombre": "Taxi / Radiotaxi Urbano",
                "velocidad_promedio_kmh": 40.0,
                "tipo": "Privado",
                "tipo_costo": "por_vehiculo",
                "costo_por_tramo": 30.0,
            },
        ]

        self.intereses = {
            "Cultural": 0.9,
            "Naturaleza": 0.6,
            "Urbano": 0.4,
        }

    def test_haversine_accuracy(self):
        """Verifica la precisión de la distancia calculada por la fórmula de Haversine."""
        # Distancia conocida entre Plaza San Francisco y Valle de la Luna (~9.0 km en línea recta)
        distancia = haversine_km(-16.4962, -68.1353, -16.5672, -68.0944)
        self.assertGreater(distancia, 8.5)
        self.assertLess(distancia, 9.5)

        # Distancia del mismo punto a sí mismo es 0.0
        self.assertEqual(haversine_km(-16.4962, -68.1353, -16.4962, -68.1353), 0.0)

    def test_ejecutar_nsga2_minimo_atractivos(self):
        """Verifica la ejecución con el mínimo de 2 atractivos."""
        sub_atractivos = self.atractivos_muestra[:2]
        res = ejecutar_nsga2(
            atractivos=sub_atractivos,
            transportes=self.transportes_muestra,
            presupuesto_max=200.0,
            tiempo_disponible_horas=5.0,
            intereses=self.intereses,
            tamano_poblacion=20,
            generaciones=10,
        )

        self.assertIn("soluciones", res)
        self.assertIn("frente_pareto", res)
        self.assertIn("historial_convergencia", res)
        self.assertIn("historial_diversidad", res)
        self.assertIn("tiempo_ejecucion_seg", res)
        self.assertGreater(len(res["soluciones"]), 0)

        # Verificar que la solución tiene exactamente 2 paradas y sin duplicados
        sol = res["soluciones"][0]
        self.assertEqual(sol["num_atractivos"], 2)
        self.assertEqual(len(set(sol["atractivos_ids"])), 2)

    def test_ejecutar_nsga2_completo(self):
        """Verifica la optimización completa con 5 atractivos."""
        res = ejecutar_nsga2(
            atractivos=self.atractivos_muestra,
            transportes=self.transportes_muestra,
            presupuesto_max=300.0,
            tiempo_disponible_horas=10.0,
            intereses=self.intereses,
            tamano_poblacion=40,
            generaciones=25,
        )

        self.assertGreater(len(res["soluciones"]), 0)
        sol = res["soluciones"][0]

        # Verificar estructura de la solución
        self.assertEqual(sol["num_atractivos"], 5)
        self.assertEqual(len(set(sol["atractivos_ids"])), 5)
        self.assertGreater(sol["afinidad"], 0.0)
        self.assertLessEqual(sol["afinidad"], 1.0)
        self.assertGreater(sol["tiempo_total_min"], 0.0)
        self.assertGreater(sol["costo_total_bob"], 0.0)
        self.assertEqual(len(sol["tramos"]), 4)  # 5 paradas = 4 tramos

        # Verificar que el transporte asignado fue el más rápido (Taxi: 40 km/h)
        self.assertEqual(sol["transporte_asignado"]["velocidad_kmh"], 40.0)

        # Verificar historial de convergencia
        hist_conv = res["historial_convergencia"]
        self.assertEqual(len(hist_conv["generaciones"]), 25)
        self.assertEqual(len(hist_conv["mejor_afinidad"]), 25)
        self.assertEqual(len(hist_conv["mejor_tiempo"]), 25)

        # Verificar historial de diversidad
        hist_div = res["historial_diversidad"]
        self.assertEqual(len(hist_div["generaciones"]), 25)
        self.assertEqual(len(hist_div["diversidad"]), 25)

    def test_validaciones_parametros_insuficientes(self):
        """Verifica que se lancen excepciones con entradas no válidas."""
        # Menos de 2 atractivos
        with self.assertRaises(ValueError):
            ejecutar_nsga2(
                atractivos=[self.atractivos_muestra[0]],
                transportes=self.transportes_muestra,
                presupuesto_max=100.0,
                tiempo_disponible_horas=4.0,
                intereses=self.intereses,
            )

        # Sin medios de transporte
        with self.assertRaises(ValueError):
            ejecutar_nsga2(
                atractivos=self.atractivos_muestra,
                transportes=[],
                presupuesto_max=100.0,
                tiempo_disponible_horas=4.0,
                intereses=self.intereses,
            )


if __name__ == "__main__":
    unittest.main()
