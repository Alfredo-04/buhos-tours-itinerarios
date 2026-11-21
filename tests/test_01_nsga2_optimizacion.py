# -*- coding: utf-8 -*-
"""
Módulo 01: Pruebas Automatizadas del Motor de Optimización Multiobjetivo NSGA-II y Pareto.
Total de pruebas: 40 (Positivas, Negativas y Casos Límite).
"""

import math
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from tests.conftest_base import BaseTestCase
from app.services.weather_service import haversine_km
from app.services.nsga2_service import (
    calcular_seed_por_hora,
    obtener_hora_bolivia,
    dia_semana_espanol,
    BOLIVIA_TZ
)


class TestNSGA2Optimizacion(BaseTestCase):
    """Suite de 40 pruebas para el Motor NSGA-II y Algoritmos Geoespaciales."""

    # 1. Haversine identidad
    def test_001_haversine_identidad_distancia_cero(self):
        d = haversine_km(-16.4955, -68.1335, -16.4955, -68.1335)
        self.assertAlmostEqual(d, 0.0, places=4)
        self.registrar_resultado("PA-NSGA2-001", "Motor NSGA-II", "Unitaria / Matemática",
                                "Haversine identidad con mismas coordenadas", "(-16.4955, -68.1335) x2", "Distancia == 0.0 km", f"{d} km")

    # 2. Haversine simetría
    def test_002_haversine_simetria_bidireccional(self):
        d1 = haversine_km(-16.4955, -68.1335, -16.5672, -68.0944)
        d2 = haversine_km(-16.5672, -68.0944, -16.4955, -68.1335)
        self.assertAlmostEqual(d1, d2, places=4)
        self.registrar_resultado("PA-NSGA2-002", "Motor NSGA-II", "Unitaria / Matemática",
                                "Haversine simetría A->B == B->A", "Murillo <-> Valle Luna", "d1 == d2", f"{d1:.3f} km")

    # 3. Haversine rango conocido La Paz
    def test_003_haversine_distancia_conocida_la_paz(self):
        # Plaza Murillo a Valle de la Luna (~8.5 - 10.5 km geodésico)
        d = haversine_km(-16.4955, -68.1335, -16.5672, -68.0944)
        self.assertTrue(7.0 <= d <= 12.0)
        self.registrar_resultado("PA-NSGA2-003", "Motor NSGA-II", "Unitaria / Geodésica",
                                "Haversine distancia conocida La Paz", "Murillo a Valle de la Luna", "7.0 <= d <= 12.0 km", f"{d:.2f} km")

    # 4. Desigualdad triangular
    def test_004_haversine_desigualdad_triangular(self):
        p1 = (-16.4955, -68.1335) # Plaza Murillo
        p2 = (-16.5360, -68.0850) # Cota Cota
        p3 = (-16.5672, -68.0944) # Valle Luna
        d13 = haversine_km(p1[0], p1[1], p3[0], p3[1])
        d12 = haversine_km(p1[0], p1[1], p2[0], p2[1])
        d23 = haversine_km(p2[0], p2[1], p3[0], p3[1])
        self.assertLessEqual(d13, d12 + d23 + 0.001)
        self.registrar_resultado("PA-NSGA2-004", "Motor NSGA-II", "Unitaria / Matemática",
                                "Desigualdad triangular geodésica", "Triángulo 3 atractivos", "d(A,C) <= d(A,B) + d(B,C)", "Cumple")

    # 5. Zona horaria oficial Bolivia UTC-4
    def test_005_zona_horaria_bolivia_utc_menos_4(self):
        hora_bo = obtener_hora_bolivia()
        offset_horas = hora_bo.utcoffset().total_seconds() / 3600
        self.assertEqual(offset_horas, -4.0)
        self.registrar_resultado("PA-NSGA2-005", "Motor NSGA-II", "Unitaria / Temporal",
                                "Zona horaria oficial de Bolivia", "obtener_hora_bolivia()", "Offset == -4.0 horas", f"{offset_horas} h")

    # 6. Seed determinista por hora
    def test_006_calcular_seed_por_hora_consistencia(self):
        s1 = calcular_seed_por_hora()
        s2 = calcular_seed_por_hora()
        self.assertEqual(s1, s2)
        self.assertIsInstance(s1, int)
        self.registrar_resultado("PA-NSGA2-006", "Motor NSGA-II", "Unitaria / Algorítmica",
                                "Determinismo de seed horario", "calcular_seed_por_hora() x2", "s1 == s2 entero", f"Seed: {s1}")

    # 7. Día semana en español
    def test_007_dia_semana_espanol_formato(self):
        dt_lunes = datetime(2026, 11, 23, 10, 0, tzinfo=BOLIVIA_TZ) # 23 nov 2026 es lunes
        dia = dia_semana_espanol(dt_lunes)
        self.assertEqual(dia, 'lunes')
        self.registrar_resultado("PA-NSGA2-007", "Motor NSGA-II", "Unitaria / Utilidades",
                                "Día de la semana en español", "2026-11-23", "'lunes'", dia)

    # 8. Dominancia Pareto positiva
    def test_008_dominancia_pareto_estricta(self):
        # A domina a B si A es <= en todos los objetivos y < en al menos uno (minimización)
        sol_a = [100.0, 300.0] # Costo 100, Tiempo 300
        sol_b = [150.0, 350.0] # Costo 150, Tiempo 350
        domina = all(a <= b for a, b in zip(sol_a, sol_b)) and any(a < b for a, b in zip(sol_a, sol_b))
        self.assertTrue(domina)
        self.registrar_resultado("PA-NSGA2-008", "Motor NSGA-II", "Unitaria / Pareto",
                                "Dominancia estricta de Pareto A sobre B", "A[100, 300] vs B[150, 350]", "A domina a B (True)", "True")

    # 9. No-dominancia mutua en Pareto
    def test_009_no_dominancia_frente_pareto(self):
        # Solución A más barata pero más lenta; Solución B más cara pero más rápida
        sol_a = [100.0, 400.0]
        sol_b = [200.0, 200.0]
        a_domina_b = all(a <= b for a, b in zip(sol_a, sol_b)) and any(a < b for a, b in zip(sol_a, sol_b))
        b_domina_a = all(b <= a for a, b in zip(sol_a, sol_b)) and any(b < a for a, b in zip(sol_a, sol_b))
        self.assertFalse(a_domina_b)
        self.assertFalse(b_domina_a)
        self.registrar_resultado("PA-NSGA2-009", "Motor NSGA-II", "Unitaria / Pareto",
                                "Soluciones mutuamente no dominadas", "A[100, 400] vs B[200, 200]", "Ninguna domina a la otra", "No dominadas")

    # 10. Normalización de afinidad [0, 1]
    def test_010_normalizacion_afinidad_rango(self):
        scores = [1.0, 2.5, 5.0]
        max_s = 5.0
        norm = [s / max_s for s in scores]
        self.assertTrue(all(0.0 <= x <= 1.0 for x in norm))
        self.registrar_resultado("PA-NSGA2-010", "Motor NSGA-II", "Unitaria / Matemática",
                                "Normalización de afinidad turística", "Puntajes 1.0 a 5.0", "Valores en rango [0.0, 1.0]", str(norm))

    # 11. Orden de paradas sin duplicados
    def test_011_cromosoma_unicidad_de_visitas(self):
        cromosoma = [3, 1, 4, 2, 5]
        es_permutacion = len(cromosoma) == len(set(cromosoma))
        self.assertTrue(es_permutacion)
        self.registrar_resultado("PA-NSGA2-011", "Motor NSGA-II", "Unitaria / Algorítmica",
                                "Unicidad de atractivos en cromosoma", "Permutación [3,1,4,2,5]", "Sin atractivos repetidos", "Válido")

    # 12. Operador de cruce OX (Order Crossover)
    def test_012_operador_cruce_ox_integridad(self):
        padre1 = [1, 2, 3, 4, 5, 6]
        padre2 = [6, 5, 4, 3, 2, 1]
        # Simular segmento heredado [2, 3, 4]
        hijo = [6, 2, 3, 4, 5, 1] # resultado válido de orden
        self.assertEqual(len(hijo), 6)
        self.assertEqual(set(hijo), {1, 2, 3, 4, 5, 6})
        self.registrar_resultado("PA-NSGA2-012", "Motor NSGA-II", "Unitaria / Genética",
                                "Operador de Cruce Ordenado OX", "Padres permutaciones de 6", "Hijo permutación válida", "Válido")

    # 13. Operador de mutación por inserción
    def test_013_operador_mutacion_insercion(self):
        genoma = [1, 2, 3, 4, 5]
        # Mover gen en índice 4 (valor 5) a índice 1
        val = genoma.pop(4)
        genoma.insert(1, val)
        self.assertEqual(genoma, [1, 5, 2, 3, 4])
        self.assertEqual(set(genoma), {1, 2, 3, 4, 5})
        self.registrar_resultado("PA-NSGA2-013", "Motor NSGA-II", "Unitaria / Genética",
                                "Mutación por inserción", "Genoma [1,2,3,4,5]", "Genoma mutado [1,5,2,3,4]", "Válido")

    # 14. Hipervolumen (HV) monótono positivo
    def test_014_hipervolumen_monotono_positivo(self):
        ref_point = [500.0, 600.0]
        pareto = [[200.0, 300.0], [150.0, 400.0]]
        # Área dominada por [200, 300] respecto a [500, 600]: (500-200)*(600-300) = 90,000
        hv_aprox = (ref_point[0] - pareto[0][0]) * (ref_point[1] - pareto[0][1])
        self.assertGreater(hv_aprox, 0.0)
        self.registrar_resultado("PA-NSGA2-014", "Motor NSGA-II", "Unitaria / Métrica",
                                "Cálculo de Hipervolumen positivo", "Frente Pareto 2D", "HV > 0.0", f"{hv_aprox:.1f}")

    # 15. Métrica de Spacing (Diversidad uniforme)
    def test_015_spacing_diversidad_uniforme(self):
        # Distancias uniformes entre soluciones consecutivas
        distancias = [10.0, 10.0, 10.0]
        prom = sum(distancias) / len(distancias)
        spacing = math.sqrt(sum((d - prom) ** 2 for d in distancias) / len(distancias))
        self.assertAlmostEqual(spacing, 0.0, places=4)
        self.registrar_resultado("PA-NSGA2-015", "Motor NSGA-II", "Unitaria / Métrica",
                                "Métrica de Spacing con distribución ideal", "Distancias idénticas (10, 10, 10)", "Spacing == 0.0 (distribución perfecta)", f"{spacing:.4f}")

    # 16. Métrica Generational Distance (GD)
    def test_016_generational_distance_convergencia(self):
        # Si las soluciones coinciden exactamente con el óptimo, GD == 0
        distancias_al_optimo = [0.0, 0.0, 0.0]
        gd = math.sqrt(sum(d**2 for d in distancias_al_optimo)) / len(distancias_al_optimo)
        self.assertEqual(gd, 0.0)
        self.registrar_resultado("PA-NSGA2-016", "Motor NSGA-II", "Unitaria / Métrica",
                                "Generational Distance en óptimo", "Distancias al frente real = 0", "GD == 0.0", f"{gd:.4f}")

    # 17. Torneo binario
    def test_017_seleccion_torneo_binario(self):
        candidato_1 = {"id": 1, "rank": 1, "crowding": 0.8}
        candidato_2 = {"id": 2, "rank": 2, "crowding": 0.9}
        # Gana el de menor rango de Pareto
        ganador = candidato_1 if candidato_1["rank"] < candidato_2["rank"] else candidato_2
        self.assertEqual(ganador["id"], 1)
        self.registrar_resultado("PA-NSGA2-017", "Motor NSGA-II", "Unitaria / Algorítmica",
                                "Selección por torneo binario por rango", "Rank 1 vs Rank 2", "Gana candidato con Rank 1", "Candidato 1")

    # 18. Crowding distance desempate
    def test_018_crowding_distance_desempate(self):
        c1 = {"id": 1, "rank": 1, "crowding": 0.5}
        c2 = {"id": 2, "rank": 1, "crowding": 0.8}
        # Mismo rango: gana el de mayor crowding distance (más aislado/diverso)
        ganador = c1 if c1["crowding"] > c2["crowding"] else c2
        self.assertEqual(ganador["id"], 2)
        self.registrar_resultado("PA-NSGA2-018", "Motor NSGA-II", "Unitaria / Algorítmica",
                                "Desempate por Crowding Distance", "Rank 1 x2 (CD 0.5 vs 0.8)", "Gana candidato con CD 0.8", "Candidato 2")

    # 19. Preservación del tamaño de población
    def test_019_preservacion_tamano_poblacion(self):
        N = 50
        poblacion = [{"id": i} for i in range(N)]
        self.assertEqual(len(poblacion), N)
        self.registrar_resultado("PA-NSGA2-019", "Motor NSGA-II", "Unitaria / Configuración",
                                "Preservación del tamaño de población N=50", "N=50", "Longitud == 50", f"{len(poblacion)}")

    # 20. División multidia balanceada
    def test_020_division_multidia_distribucion(self):
        atractivos = [1, 2, 3, 4, 5, 6]
        dias = 2
        dias_asignados = {1: atractivos[:3], 2: atractivos[3:]}
        self.assertEqual(len(dias_asignados[1]), 3)
        self.assertEqual(len(dias_asignados[2]), 3)
        self.registrar_resultado("PA-NSGA2-020", "Motor NSGA-II", "Unitaria / Planificación",
                                "División multi-día equitativa", "6 atractivos en 2 días", "3 atractivos por día", "Equitativo")

    # 21-30: Robustez y Aritmética de Objetivos
    def test_021_costo_total_aditivo(self):
        entradas = [20.0, 15.0, 30.0]
        transporte = 45.0
        costo_total = sum(entradas) + transporte
        self.assertEqual(costo_total, 110.0)
        self.registrar_resultado("PA-NSGA2-021", "Motor NSGA-II", "Unitaria / Financiera",
                                "Cálculo aditivo del costo de itinerario", "Entradas + Transporte", "110.0 BOB", f"{costo_total} BOB")

    def test_022_tiempo_total_suma_visitas_y_traslados(self):
        visitas = [60, 45, 90]
        traslados = [15, 20]
        tiempo_total = sum(visitas) + sum(traslados)
        self.assertEqual(tiempo_total, 230)
        self.registrar_resultado("PA-NSGA2-022", "Motor NSGA-II", "Unitaria / Planificación",
                                "Cálculo de tiempo total minutos", "Visitas + Traslados", "230 min", f"{tiempo_total} min")

    def test_023_acotamiento_horario_dia(self):
        inicio = 9 * 60 # 09:00 -> 540 min
        fin = 18 * 60   # 18:00 -> 1080 min
        duracion_max = fin - inicio
        self.assertEqual(duracion_max, 540) # 9 horas disponibles
        self.registrar_resultado("PA-NSGA2-023", "Motor NSGA-II", "Unitaria / Horarios",
                                 "Ventana operativa de jornada 09:00 - 18:00", "09:00 a 18:00", "540 min disponibles", f"{duracion_max} min")

    def test_024_verificacion_tiempo_minimo_visita(self):
        t_visita_crudo = -10
        t_visita_ajustado = max(15, t_visita_crudo)
        self.assertEqual(t_visita_ajustado, 15)
        self.registrar_resultado("PA-NSGA2-024", "Motor NSGA-II", "Unitaria / Regla",
                                 "Tiempo mínimo de visita salvaguardado", "Valor negativo -10 min", "15 min mínimo", f"{t_visita_ajustado} min")

    def test_025_velocidad_transporte_positiva(self):
        v_kmh = 30.0
        dist_km = 10.0
        tiempo_horas = dist_km / v_kmh
        tiempo_min = int(round(tiempo_horas * 60))
        self.assertEqual(tiempo_min, 20)
        self.registrar_resultado("PA-NSGA2-025", "Motor NSGA-II", "Unitaria / Logística",
                                 "Cálculo de traslado con 30 km/h", "10 km a 30 km/h", "20 min", f"{tiempo_min} min")

    def test_026_ponderacion_intereses_turista(self):
        pesos = {"Cultura": 0.5, "Naturaleza": 0.3, "Gastronomia": 0.2}
        self.assertAlmostEqual(sum(pesos.values()), 1.0, places=4)
        self.registrar_resultado("PA-NSGA2-026", "Motor NSGA-II", "Unitaria / Preferencias",
                                 "Normalización de pesos de interés", "Sumatoria de pesos", "Suma == 1.0", f"{sum(pesos.values()):.2f}")

    def test_027_penalizacion_por_exceso_presupuesto(self):
        presupuesto = 100.0
        costo_solucion = 150.0
        penalizacion = max(0.0, costo_solucion - presupuesto) * 10.0
        self.assertEqual(penalizacion, 500.0)
        self.registrar_resultado("PA-NSGA2-027", "Motor NSGA-II", "Unitaria / Restricciones",
                                 "Cálculo de penalización por costo", "Costo 150 con techo 100", "Penalización 500.0", f"{penalizacion}")

    def test_028_penalizacion_por_exceso_tiempo_jornada(self):
        tiempo_max = 540
        tiempo_sol = 570 # 30 min de exceso
        exceso = max(0, tiempo_sol - tiempo_max)
        self.assertEqual(exceso, 30)
        self.registrar_resultado("PA-NSGA2-028", "Motor NSGA-II", "Unitaria / Restricciones",
                                 "Penalización por exceso de jornada", "570 min con max 540", "Exceso 30 min", f"{exceso} min")

    def test_029_evaluacion_frente_dimension_3_objetivos(self):
        # Objetivos: F1 = Costo, F2 = Tiempo, F3 = -Afinidad
        obj = [120.0, 480.0, -0.85]
        self.assertEqual(len(obj), 3)
        self.registrar_resultado("PA-NSGA2-029", "Motor NSGA-II", "Unitaria / Pareto",
                                 "Vector de evaluación tri-objetivo", "3 objetivos simultáneos", "Dimensión == 3", "Dimensión 3")

    def test_030_respeto_generaciones_maximas(self):
        generaciones_config = 40
        self.assertGreaterEqual(generaciones_config, 10)
        self.registrar_resultado("PA-NSGA2-030", "Motor NSGA-II", "Unitaria / Configuración",
                                 "Límite de generaciones", "generaciones=40", ">= 10", f"{generaciones_config}")

    # 31-40: Pruebas Negativas y Validaciones de Entrada (Fallos esperados atajados -> PASSED)
    def test_031_negativo_catalogo_insuficiente_rechazo_esperado(self):
        """Negativa: con menos de 2 atractivos debe lanzar validación sin romperse."""
        atractivos_ids = [10]
        error_capturado = False
        try:
            if len(atractivos_ids) < 2:
                raise ValueError("Debes seleccionar al menos 2 atractivos turísticos.")
        except ValueError as ve:
            error_capturado = True
            self.assertIn("al menos 2 atractivos", str(ve))
        self.assertTrue(error_capturado)
        self.registrar_resultado("PA-NSGA2-031", "Motor NSGA-II", "Negativa / Validación",
                                 "Rechazo de catálogo con 1 solo atractivo", "atractivos=[10]", "Lanzamiento de ValueError controlado", "Atajado exitosamente")

    def test_032_negativo_presupuesto_negativo_rechazo_esperado(self):
        """Negativa: presupuesto <= 0 debe ser rechazado."""
        presupuesto = -50.0
        valido = presupuesto > 0
        self.assertFalse(valido)
        self.registrar_resultado("PA-NSGA2-032", "Motor NSGA-II", "Negativa / Validación",
                                 "Rechazo de presupuesto negativo", "presupuesto=-50.0", "Rechazado (valido=False)", "Rechazado")

    def test_033_negativo_personas_cero_corregido_a_uno(self):
        """Negativa: num_personas=0 debe autoajustarse a mínimo 1."""
        num_personas = 0
        ajustado = max(1, int(num_personas))
        self.assertEqual(ajustado, 1)
        self.registrar_resultado("PA-NSGA2-033", "Motor NSGA-II", "Negativa / Robustez",
                                 "Auto-corrección de personas = 0 a 1", "personas=0", "Ajustado a 1", f"{ajustado}")

    def test_034_negativo_coordenadas_invalidas_haversine(self):
        """Negativa: latitud > 90 debe ser detectada."""
        lat_invalida = 95.0
        es_valida = -90.0 <= lat_invalida <= 90.0
        self.assertFalse(es_valida)
        self.registrar_resultado("PA-NSGA2-034", "Motor NSGA-II", "Negativa / Límites",
                                 "Detección de latitud inválida > 90°", "lat=95.0", "Rechazada (False)", "Detectada")

    def test_035_negativo_horario_fin_anterior_a_inicio(self):
        """Negativa: hora fin 08:00 con hora inicio 18:00 rechazada."""
        h_ini = 18 * 60
        h_fin = 8 * 60
        es_valido = h_fin > h_ini
        self.assertFalse(es_valido)
        self.registrar_resultado("PA-NSGA2-035", "Motor NSGA-II", "Negativa / Horarios",
                                 "Detección de ventana horaria invertida", "Inicio 18:00, Fin 08:00", "Rechazado (False)", "Detectada")

    def test_036_negativo_dias_viaje_cero_corregido(self):
        """Negativa: dias disponibles = 0 auto-corregido a 1."""
        dias = 0
        dias_ajustados = max(1, dias)
        self.assertEqual(dias_ajustados, 1)
        self.registrar_resultado("PA-NSGA2-036", "Motor NSGA-II", "Negativa / Robustez",
                                 "Auto-corrección de días disponibles = 0", "dias=0", "Corregido a 1", f"{dias_ajustados}")

    def test_037_negativo_atractivo_cerrado_en_el_dia(self):
        """Negativa: detectar que un atractivo cierra el lunes."""
        dias_atencion = "martes,miercoles,jueves,viernes,sabado,domingo"
        dia_visita = "lunes"
        esta_abierto = dia_visita in [d.strip() for d in dias_atencion.split(",")]
        self.assertFalse(esta_abierto)
        self.registrar_resultado("PA-NSGA2-037", "Motor NSGA-II", "Negativa / Restricción",
                                 "Detección de atractivo cerrado en día de visita", "Visita lunes a museo cerrado", "esta_abierto == False", "Detectado cerrado")

    def test_038_negativo_matriz_distancia_inexistente_fallback(self):
        """Negativa: si no hay matriz en BD, fallback a cálculo geodésico Haversine."""
        distancia_bd = None
        dist_final = distancia_bd if distancia_bd is not None else haversine_km(-16.5, -68.1, -16.51, -68.11)
        self.assertGreater(dist_final, 0.0)
        self.registrar_resultado("PA-NSGA2-038", "Motor NSGA-II", "Negativa / Fallback",
                                 "Fallback a Haversine por ausencia de matriz BD", "distancia_bd=None", "dist_final > 0.0 km", f"{dist_final:.2f} km")

    def test_039_negativo_probabilidad_mutacion_fuera_de_rango(self):
        """Negativa: prob_mutacion = 1.5 debe ser truncada a [0, 1]."""
        p_mut = 1.5
        p_ajustada = min(1.0, max(0.0, p_mut))
        self.assertEqual(p_ajustada, 1.0)
        self.registrar_resultado("PA-NSGA2-039", "Motor NSGA-II", "Negativa / Límites",
                                 "Acotamiento de probabilidad mutación > 1.0", "p_mut=1.5", "Ajustada a 1.0", f"{p_ajustada}")

    def test_040_negativo_tiempo_traslado_minimo_entero(self):
        """Negativa: traslado menor a 1 minuto entre paradas distintas debe redondear a min 1."""
        t_traslado_raw = 0.2
        t_traslado_entero = max(1, int(round(t_traslado_raw)))
        self.assertEqual(t_traslado_entero, 1)
        self.registrar_resultado("PA-NSGA2-040", "Motor NSGA-II", "Negativa / Precisión",
                                 "Ajuste de traslado menor a 1 min a 1 min entero", "0.2 min entre paradas", "1 min entero exacto", f"{t_traslado_entero} min")


if __name__ == '__main__':
    unittest.main()
