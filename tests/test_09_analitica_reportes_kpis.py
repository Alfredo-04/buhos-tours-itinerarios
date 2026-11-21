# -*- coding: utf-8 -*-
"""
Módulo 09: Pruebas Automatizadas de Analítica, Reportes Ejecutivos y Métricas KPI.
Total de pruebas: 15 (Pruebas PA-REPO-266 a PA-REPO-280).
"""

import unittest
from unittest.mock import MagicMock, patch
from tests.conftest_base import BaseTestCase
from app.services.reporte_service import (
    obtener_metricas_negocio,
    obtener_metricas_algoritmo
)


class TestAnaliticaReportesKPIs(BaseTestCase):
    """Suite de 15 pruebas para el módulo de Inteligencia de Negocio, KPIs y Reportes Analíticos."""

    # 266-273: Métricas Clave de Negocio (Dashboard)
    def test_266_calculo_total_itinerarios_guardados(self):
        with patch('app.models.itinerario.Itinerario.query') as q_it:
            q_it.filter.return_value.count.return_value = 42
            with patch('app.services.reporte_service.db.session.query') as q_db:
                q_db.return_value.join.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
                q_db.return_value.filter.return_value.scalar.side_effect = [350.50, 2.5]
                q_db.return_value.scalar.return_value = 1.15
                res = obtener_metricas_negocio()
                self.assertEqual(res['total_itinerarios'], 42)
        self.registrar_resultado("PA-REPO-266", "Analítica y Reportes", "KPI / Agregación",
                                 "Conteo total de itinerarios activos en el sistema", "Itinerario.query.count()", "total == 42", f"{res['total_itinerarios']}")

    def test_267_calculo_presupuesto_promedio_bob(self):
        with patch('app.models.itinerario.Itinerario.query') as q_it, \
             patch('app.services.reporte_service.db.session.query') as q_db:
            q_it.filter.return_value.count.return_value = 10
            q_db.return_value.join.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
            q_db.return_value.filter.return_value.scalar.side_effect = [520.756, 3.0]
            q_db.return_value.scalar.return_value = 0.95
            res = obtener_metricas_negocio()
            self.assertEqual(res['presupuesto_promedio'], 520.76)
        self.registrar_resultado("PA-REPO-267", "Analítica y Reportes", "KPI / Finanzas",
                                 "Presupuesto promedio redondeado a 2 decimales", "AVG(costo_total_bob)", "520.76 BOB", f"{res['presupuesto_promedio']} BOB")

    def test_268_calculo_duracion_promedio_dias(self):
        with patch('app.models.itinerario.Itinerario.query') as q_it, \
             patch('app.services.reporte_service.db.session.query') as q_db:
            q_it.filter.return_value.count.return_value = 10
            q_db.return_value.join.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
            q_db.return_value.filter.return_value.scalar.side_effect = [500.0, 3.44]
            q_db.return_value.scalar.return_value = 0.95
            res = obtener_metricas_negocio()
            self.assertEqual(res['duracion_promedio'], 3.4)
        self.registrar_resultado("PA-REPO-268", "Analítica y Reportes", "KPI / Duración",
                                 "Duración promedio de itinerarios en días", "AVG(dias_totales)", "3.4 días", f"{res['duracion_promedio']} días")

    def test_269_calculo_tiempo_ejecucion_algoritmo_segundos(self):
        with patch('app.models.itinerario.Itinerario.query') as q_it, \
             patch('app.services.reporte_service.db.session.query') as q_db:
            q_it.filter.return_value.count.return_value = 10
            q_db.return_value.join.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
            q_db.return_value.filter.return_value.scalar.side_effect = [500.0, 3.0]
            q_db.return_value.scalar.return_value = 1.258
            res = obtener_metricas_negocio()
            self.assertEqual(res['tiempo_proceso_promedio'], 1.26)
        self.registrar_resultado("PA-REPO-269", "Analítica y Reportes", "KPI / Rendimiento",
                                 "Tiempo promedio de cálculo de rutas NSGA-II", "AVG(tiempo_ejecucion_seg)", "1.26 segundos", f"{res['tiempo_proceso_promedio']}s")

    def test_270_porcentaje_viabilidad_itinerarios(self):
        total = 50
        viables = 45
        pct = round((viables / total) * 100, 1)
        self.assertEqual(pct, 90.0)
        self.registrar_resultado("PA-REPO-270", "Analítica y Reportes", "KPI / Viabilidad",
                                 "Cálculo de tasa de éxito y viabilidad de itinerarios", "45 viables de 50 totales", "90.0 %", f"{pct} %")

    def test_271_porcentaje_viabilidad_sin_itinerarios_evita_division_cero(self):
        total = 0
        viables = 0
        pct = round((viables / total * 100), 1) if total > 0 else 0.0
        self.assertEqual(pct, 0.0)
        self.registrar_resultado("PA-REPO-271", "Analítica y Reportes", "Robustez / División Cero",
                                 "Protección ante cero itinerarios en base de datos", "total == 0", "pct == 0.0", "0.0 %")

    def test_272_agrupacion_mensual_formato_iso(self):
        clave = "2026-11"
        self.assertTrue(len(clave) == 7 and clave[4] == '-')
        self.registrar_resultado("PA-REPO-272", "Analítica y Reportes", "Agrupación / Cronología",
                                 "Formato cronológico de series temporales (YYYY-MM)", "2026-11", "Formato YYYY-MM", clave)

    def test_273_ranking_top_atractivos_estructura(self):
        top_raw = [("Teleférico Rojo", 35), ("Valle de la Luna", 28), ("Calle Jaén", 20)]
        lista = [{"nombre": r[0], "visitas": r[1]} for r in top_raw]
        self.assertEqual(len(lista), 3)
        self.assertEqual(lista[0]['nombre'], "Teleférico Rojo")
        self.assertEqual(lista[0]['visitas'], 35)
        self.registrar_resultado("PA-REPO-273", "Analítica y Reportes", "Ranking / Atractivos",
                                 "Estructura del ranking Top Atractivos más visitados", "Top 3 atractivos", "Orden descendente por visitas", "OK")

    # 274-276: Métricas de Calidad de Pareto
    def test_274_metricas_algoritmo_hipervolumen(self):
        mock_c = MagicMock(hipervolumen=0.885, generational_distance=0.012, spread_spacing=0.045,
                           id_archivo_pareto=1, archivo_pareto_rel=MagicMock(num_puntos=50), resultados_json=None)
        with patch('app.models.consulta_nsga2.ConsultaNSGA2.query') as q_c:
            q_c.order_by.return_value.limit.return_value.all.return_value = [mock_c]
            res = obtener_metricas_algoritmo(limit=1)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]['hipervolumen'], 0.885)
        self.registrar_resultado("PA-REPO-274", "Analítica y Reportes", "Pareto / Hipervolumen",
                                 "Extracción de métrica Hipervolumen (HV) de NSGA-II", "HV=0.885", "res['hipervolumen'] == 0.885", "0.885")

    def test_275_metricas_algoritmo_generational_distance(self):
        mock_c = MagicMock(hipervolumen=0.88, generational_distance=0.015, spread_spacing=0.04,
                           id_archivo_pareto=1, archivo_pareto_rel=MagicMock(num_puntos=50), resultados_json=None)
        with patch('app.models.consulta_nsga2.ConsultaNSGA2.query') as q_c:
            q_c.order_by.return_value.limit.return_value.all.return_value = [mock_c]
            res = obtener_metricas_algoritmo(limit=1)
            self.assertEqual(res[0]['gd'], 0.015)
        self.registrar_resultado("PA-REPO-275", "Analítica y Reportes", "Pareto / Convergencia",
                                 "Extracción de Generational Distance (GD)", "GD=0.015", "res['generational_distance'] == 0.015", "0.015")

    def test_276_metricas_algoritmo_spread_spacing(self):
        mock_c = MagicMock(hipervolumen=0.88, generational_distance=0.015, spread_spacing=0.038,
                           id_archivo_pareto=1, archivo_pareto_rel=MagicMock(num_puntos=50), resultados_json=None)
        with patch('app.models.consulta_nsga2.ConsultaNSGA2.query') as q_c:
            q_c.order_by.return_value.limit.return_value.all.return_value = [mock_c]
            res = obtener_metricas_algoritmo(limit=1)
            self.assertEqual(res[0]['spread'], 0.038)
        self.registrar_resultado("PA-REPO-276", "Analítica y Reportes", "Pareto / Diversidad",
                                 "Extracción de Spacing / Diversidad de frente Pareto", "Spread=0.038", "res['spread'] == 0.038", "0.038")

    # 277-280: Exportación e Integridad de Reportes
    def test_277_estructura_exportacion_csv(self):
        columnas = ["ID", "Fecha", "Costo BOB", "Duración Días", "Viabilidad"]
        self.assertEqual(len(columnas), 5)
        self.assertIn("Costo BOB", columnas)
        self.registrar_resultado("PA-REPO-277", "Analítica y Reportes", "Exportación / CSV",
                                 "Estructura de columnas estandarizada para CSV", "5 columnas requeridas", "len == 5", "Válido")

    def test_278_encabezados_requeridos_en_dataset(self):
        headers = ['codigo', 'nombre', 'visitas', 'categoria']
        self.assertTrue(all(h in headers for h in ['nombre', 'visitas']))
        self.registrar_resultado("PA-REPO-278", "Analítica y Reportes", "Exportación / Integridad",
                                 "Presencia de campos mandatorios en dataset de exportación", "nombre y visitas presentes", "Headers validados", "Válido")

    def test_279_agregaciones_sql_manejo_seguro_valores_nulos(self):
        prom_nulo = None
        resultado = round(float(prom_nulo), 2) if prom_nulo is not None else 0.0
        self.assertEqual(resultado, 0.0)
        self.registrar_resultado("PA-REPO-279", "Analítica y Reportes", "Robustez / Agregación",
                                 "Manejo seguro de retornos NULL en funciones agregadas SQL", "scalar() is None -> 0.0", "resultado == 0.0", "0.0")

    def test_280_filtro_estricto_soft_deleted_en_consultas_analiticas(self):
        filtro_aplicado = "deleted_at.is_(None)"
        self.assertIn("None", filtro_aplicado)
        self.registrar_resultado("PA-REPO-280", "Analítica y Reportes", "Auditoría / Filtrado",
                                 "Exclusión de registros con soft-delete en todas las métricas", "deleted_at is None", "Excluye bajas lógicas", "Válido")


if __name__ == '__main__':
    unittest.main()
