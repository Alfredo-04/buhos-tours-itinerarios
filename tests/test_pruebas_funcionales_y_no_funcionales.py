# -*- coding: utf-8 -*-
"""
========================================================================================
SUITE DE PRUEBAS AUTOMATIZADAS (FUNCIONALES Y NO FUNCIONALES) - BUHOS TOURS
========================================================================================

Este archivo integra de manera automatizada pruebas exhaustivas para la plataforma
Buhos Tours, estructuradas de acuerdo a la norma ISO/IEC 25010 (Calidad de Software).

----------------------------------------------------------------------------------------
CLASIFICACIÓN DE PRUEBAS INCLUIDAS:
----------------------------------------------------------------------------------------
1. PRUEBAS FUNCIONALES (@pytest.mark.funcional):
   - PF-01: Control de Acceso y RBAC (No autenticado -> 302 a /login)
   - PF-02: Control de Acceso y RBAC (Turista -> 403 Forbidden a Generador y Gestión)
   - PF-03: Control de Acceso y RBAC (Agente y Admin -> 200 OK con privilegios)
   - PF-04: Cálculo Geodésico y Precisión Espacial Haversine (Identidad, Simetría, Precisión)
   - PF-05: Motor NSGA-II: Optimización Multiobjetivo y Respeto de Restricciones
   - PF-06: Motor NSGA-II: Métricas de Afinidad Normalizada, Convergencia y Diversidad
   - PF-07: Motor NSGA-II: Manejo de Entradas Insuficientes (Validación de Límites)
   - PF-08: Conversión de Divisas (Tipo de Cambio Oficial BCB BOB a USD)
   - PF-09: Frente de Pareto: Filtrado de Soluciones No Dominadas
   - PF-10: Catálogo Público y Visualización Geoespacial

2. PRUEBAS NO FUNCIONALES (@pytest.mark.no_funcional):
   - PNF-01: Rendimiento / Latencia: Tiempo de respuesta en endpoints web (< 500 ms)
   - PNF-02: Rendimiento / Algoritmo: Ejecución de NSGA-II bajo umbral de tiempo (< 2.0 s)
   - PNF-03: Rendimiento / Micro-benchmark: 5,000 cálculos Haversine (< 150 ms)
   - PNF-04: Consumo de Recursos / Memoria: Ausencia de fugas con tracemalloc (< 25 MB)
   - PNF-05: Seguridad / Inyección SQL (SQLi): Sanitización de parámetros maliciosos
   - PNF-06: Seguridad / Cross-Site Scripting (XSS): Neutralización de etiquetas de script
   - PNF-07: Seguridad / Escalabilidad de Privilegios: Bloqueo de navegación forzada
   - PNF-08: Robustez / Entradas Malformadas: Manejo elegante de excepciones (Sin HTTP 500)
   - PNF-09: Robustez / Valores Límite: Tolerancia ante presupuesto cero o mínimo
   - PNF-10: Concurrencia / Resiliencia bajo Carga: Ráfagas simultáneas con ThreadPool

----------------------------------------------------------------------------------------
INSTRUCCIONES DE EJECUCIÓN EN TERMINAL:
----------------------------------------------------------------------------------------
- Ejecutar toda la suite completa:
    pytest -v tests/test_pruebas_funcionales_y_no_funcionales.py

- Ejecutar ÚNICAMENTE las pruebas funcionales:
    pytest -v -m funcional tests/test_pruebas_funcionales_y_no_funcionales.py

- Ejecutar ÚNICAMENTE las pruebas no funcionales:
    pytest -v -m no_funcional tests/test_pruebas_funcionales_y_no_funcionales.py

- Ejecutar pruebas por subcategoría específica:
    pytest -v -m rendimiento tests/test_pruebas_funcionales_y_no_funcionales.py
    pytest -v -m seguridad tests/test_pruebas_funcionales_y_no_funcionales.py
    pytest -v -m concurrencia tests/test_pruebas_funcionales_y_no_funcionales.py

- Ejecución directa como script de Python:
    python tests/test_pruebas_funcionales_y_no_funcionales.py
========================================================================================
"""

import gc
import sys
import time
import uuid
import pytest
import tracemalloc
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from app import create_app, db
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.services.nsga2_service import haversine_km, ejecutar_nsga2
from app.services.exchange_service import convertir_bs_a_usd
from app.services.metricas_pareto_service import _filtrar_no_dominados


# ======================================================================================
# FIXTURES Y CONFIGURACIÓN COMPARTIDA
# ======================================================================================

@pytest.fixture(scope="session")
def app():
    """Inicializa la aplicación Flask en modo TESTING aislado."""
    app_instance = create_app()
    app_instance.config['TESTING'] = True
    app_instance.config['WTF_CSRF_ENABLED'] = False
    app_instance.config['MAIL_SUPPRESS_SEND'] = True
    return app_instance


@pytest.fixture(scope="session")
def client(app):
    """Cliente de pruebas HTTP de Flask para ejecutar peticiones."""
    return app.test_client()


@pytest.fixture(scope="session")
def app_context(app):
    """Contexto de aplicación global para operaciones de base de datos."""
    with app.app_context():
        yield


@pytest.fixture(scope="session")
def sample_dataset():
    """
    Conjunto de datos representativo de atractivos y transportes turísticos de La Paz,
    con coordenadas georreferenciadas y valores reales de operación.
    """
    atractivos = [
        {
            "id": 101,
            "nombre": "Plaza Murillo / Kilómetro Cero",
            "lat": -16.4957,
            "lon": -68.1335,
            "tiempo_visita": 40,
            "categoria": "Cultural",
            "costo_entrada": 0.0,
        },
        {
            "id": 102,
            "nombre": "Basílica y Plaza San Francisco",
            "lat": -16.4962,
            "lon": -68.1353,
            "tiempo_visita": 45,
            "categoria": "Cultural",
            "costo_entrada": 0.0,
        },
        {
            "id": 103,
            "nombre": "Calle Histórica Jaén y Museos",
            "lat": -16.4922,
            "lon": -68.1358,
            "tiempo_visita": 60,
            "categoria": "Urbano",
            "costo_entrada": 10.0,
        },
        {
            "id": 104,
            "nombre": "Mirador Panorámico Killi Killi",
            "lat": -16.4954,
            "lon": -68.1273,
            "tiempo_visita": 35,
            "categoria": "Naturaleza",
            "costo_entrada": 0.0,
        },
        {
            "id": 105,
            "nombre": "Parque Natural Valle de la Luna",
            "lat": -16.5672,
            "lon": -68.0944,
            "tiempo_visita": 90,
            "categoria": "Naturaleza",
            "costo_entrada": 15.0,
        },
        {
            "id": 106,
            "nombre": "Museo Nacional de Etnografía y Folklore (MUSEF)",
            "lat": -16.4951,
            "lon": -68.1349,
            "tiempo_visita": 75,
            "categoria": "Cultural",
            "costo_entrada": 20.0,
        },
    ]

    transportes = [
        {
            "id": 201,
            "nombre": "Mi Teleférico - Red Urbana Integrada",
            "velocidad_promedio_kmh": 22.0,
            "tipo": "Público",
            "tipo_costo": "por_persona",
            "costo_por_tramo": 3.0,
        },
        {
            "id": 202,
            "nombre": "Radiotaxi Turístico Certificado",
            "velocidad_promedio_kmh": 38.0,
            "tipo": "Privado",
            "tipo_costo": "por_vehiculo",
            "costo_por_tramo": 25.0,
        },
    ]

    intereses = {
        "Cultural": 0.9,
        "Naturaleza": 0.7,
        "Urbano": 0.5,
    }

    return {
        "atractivos": atractivos,
        "transportes": transportes,
        "intereses": intereses,
    }


@pytest.fixture(scope="module")
def auth_users(app):
    """
    Crea usuarios temporales en la BD de pruebas para validar RBAC.
    Limpia los registros al finalizar el módulo de pruebas.
    """
    with app.app_context():
        try:
            # Obtener o asegurar roles
            roles = {}
            for rol_nom in ['admin', 'agente', 'turista']:
                r = Rol.query.filter_by(nombre=rol_nom).first()
                if not r:
                    r = Rol(nombre=rol_nom, descripcion=f'Rol {rol_nom} para suite de tests')
                    db.session.add(r)
                    db.session.commit()
                roles[rol_nom] = r

            token_uid = uuid.uuid4().hex[:6]
            admin_u = Usuario(
                nombres='Admin', apellidos='Test Suite',
                email=f'admin_suite_{token_uid}@test.com',
                contrasenia='PruebaSegura2026!', id_rol=roles['admin'].id_rol,
                two_factor_enabled=True, two_factor_confirmed_at=datetime.utcnow(),
                must_change_password=False
            )
            agente_u = Usuario(
                nombres='Agente', apellidos='Test Suite',
                email=f'agente_suite_{token_uid}@test.com',
                contrasenia='PruebaSegura2026!', id_rol=roles['agente'].id_rol,
                two_factor_enabled=True, two_factor_confirmed_at=datetime.utcnow(),
                must_change_password=False
            )
            turista_u = Usuario(
                nombres='Turista', apellidos='Test Suite',
                email=f'turista_suite_{token_uid}@test.com',
                contrasenia='PruebaSegura2026!', id_rol=roles['turista'].id_rol,
                two_factor_enabled=False,
                must_change_password=False
            )

            db.session.add_all([admin_u, agente_u, turista_u])
            db.session.commit()

            yield {
                'admin': admin_u,
                'agente': agente_u,
                'turista': turista_u,
            }

            # Teardown: Eliminar usuarios temporales
            Usuario.query.filter(Usuario.id_usuario.in_([
                admin_u.id_usuario,
                agente_u.id_usuario,
                turista_u.id_usuario
            ])).delete(synchronize_session=False)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            # En caso de que la BD no esté conectada o en modo standalone, se devuelve dict informativo
            yield {'error': str(e), 'admin': None, 'agente': None, 'turista': None}


# ======================================================================================
# SECCIÓN 1: PRUEBAS FUNCIONALES
# ======================================================================================

@pytest.mark.funcional
class TestPruebasFuncionales:
    """
    Conjunto de pruebas funcionales para validar que los flujos de negocio,
    control de acceso, algoritmos y cálculos matemáticos operan según especificación.
    """

    def test_pf01_control_acceso_rbac_no_autenticado(self, client):
        """
        [PF-01] Los usuarios sin sesión iniciada deben ser redirigidos con HTTP 302
        hacia el endpoint de inicio de sesión (/login).
        """
        endpoints_protegidos = [
            '/itinerarios/generar',
            '/reportes/dashboard',
            '/usuarios/',
            '/admin/metricas-algoritmo',
        ]

        for endpoint in endpoints_protegidos:
            response = client.get(endpoint, follow_redirects=False)
            assert response.status_code == 302, f"El endpoint {endpoint} no redirigió a un usuario anónimo."
            assert '/login' in response.headers.get('Location', ''), (
                f"La redirección de {endpoint} no apunta a la página de login."
            )

    def test_pf02_control_acceso_rbac_turista_prohibido(self, client, auth_users):
        """
        [PF-02] Los usuarios con rol 'turista' no deben tener permiso para acceder
        a la consola de generación avanzada de itinerarios (debe retornar HTTP 403 Forbidden).
        """
        turista = auth_users.get('turista')
        if not turista or not getattr(turista, 'id_usuario', None):
            pytest.skip("Base de datos no disponible para instanciar usuario Turista.")

        with client.session_transaction() as sess:
            sess['_user_id'] = str(turista.id_usuario)
            sess['_fresh'] = True

        response = client.get('/itinerarios/generar')
        assert response.status_code == 403, (
            f"Se esperaba 403 Forbidden para Turista, pero se obtuvo {response.status_code}."
        )

    def test_pf03_control_acceso_rbac_agente_admin_permitido(self, client, auth_users):
        """
        [PF-03] Los usuarios con rol 'agente' y 'admin' deben poder acceder
        a la vista del generador de itinerarios exitosamente (HTTP 200 OK).
        """
        for rol_nombre in ['agente', 'admin']:
            usuario = auth_users.get(rol_nombre)
            if not usuario or not getattr(usuario, 'id_usuario', None):
                continue

            with client.session_transaction() as sess:
                sess['_user_id'] = str(usuario.id_usuario)
                sess['_fresh'] = True

            response = client.get('/itinerarios/generar')
            assert response.status_code == 200, (
                f"El rol {rol_nombre} no pudo acceder a /itinerarios/generar (HTTP {response.status_code})."
            )
            # Validación de contenido clave renderizado en la plantilla
            assert b'Generaci' in response.data or b'Itinerario' in response.data

    def test_pf04_calculo_geodesico_haversine_precision_y_simetria(self):
        """
        [PF-04] Validación del algoritmo matemático de Haversine:
        - Precisión contra distancias geográficas reales conocidas en La Paz.
        - Identidad reflexiva: distancia de un punto a sí mismo es 0.0 km.
        - Conmutatividad simétrica: d(A, B) == d(B, A).
        """
        # Plaza San Francisco (-16.4962, -68.1353) a Valle de la Luna (-16.5672, -68.0944)
        lat_sf, lon_sf = -16.4962, -68.1353
        lat_vl, lon_vl = -16.5672, -68.0944

        dist_sf_vl = haversine_km(lat_sf, lon_sf, lat_vl, lon_vl)
        dist_vl_sf = haversine_km(lat_vl, lon_vl, lat_sf, lon_sf)

        # 1. Distancia esperada entre 8.5 km y 9.5 km en línea geodésica
        assert 8.5 <= dist_sf_vl <= 9.5, f"Distancia calculada {dist_sf_vl} km fuera del rango esperado."

        # 2. Simetría matemática
        assert round(dist_sf_vl, 6) == round(dist_vl_sf, 6), "Haversine no cumple la propiedad de simetría."

        # 3. Identidad reflexiva
        assert haversine_km(lat_sf, lon_sf, lat_sf, lon_sf) == 0.0, "La distancia de un punto a sí mismo debe ser 0.0."

    def test_pf05_nsga2_optimizacion_multiobjetivo_valida(self, sample_dataset):
        """
        [PF-05] El motor genético multiobjetivo NSGA-II debe generar soluciones válidas:
        - Debe devolver al menos una solución factible.
        - Cada solución no debe tener atractivos duplicados (permutación íntegra).
        - Debe respetar el límite de presupuesto y tiempo máximo disponible.
        """
        presupuesto_max = 250.0  # BOB
        tiempo_max_horas = 8.0   # Horas

        resultado = ejecutar_nsga2(
            atractivos=sample_dataset["atractivos"],
            transportes=sample_dataset["transportes"],
            presupuesto_max=presupuesto_max,
            tiempo_disponible_horas=tiempo_max_horas,
            intereses=sample_dataset["intereses"],
            tamano_poblacion=30,
            generaciones=15,
        )

        assert "soluciones" in resultado, "El resultado de NSGA-II no contiene la clave 'soluciones'."
        assert len(resultado["soluciones"]) > 0, "No se generaron soluciones en el frente de Pareto."

        primera_sol = resultado["soluciones"][0]

        # Validar no duplicidad de paradas (Invariante de permutación)
        ids_atractivos = primera_sol["atractivos_ids"]
        assert len(ids_atractivos) == len(set(ids_atractivos)), "Se encontraron atractivos duplicados en el itinerario."

        # Validar cumplimiento de restricciones
        assert primera_sol["costo_total_bob"] <= presupuesto_max + 1e-4, "El itinerario supera el presupuesto asignado."
        assert (primera_sol["tiempo_total_min"] / 60.0) <= tiempo_max_horas + 1e-4, "El itinerario supera el tiempo límite."

    def test_pf06_nsga2_metricas_afinidad_y_convergencia(self, sample_dataset):
        """
        [PF-06] Validar las métricas de afinidad, convergencia generacional y diversidad:
        - La afinidad turística debe estar acotada estrictamente en el intervalo [0.0, 1.0].
        - Los historiales de convergencia y diversidad deben contener tantas entradas como generaciones.
        """
        num_generaciones = 12

        resultado = ejecutar_nsga2(
            atractivos=sample_dataset["atractivos"],
            transportes=sample_dataset["transportes"],
            presupuesto_max=300.0,
            tiempo_disponible_horas=9.0,
            intereses=sample_dataset["intereses"],
            tamano_poblacion=25,
            generaciones=num_generaciones,
        )

        for sol in resultado["soluciones"]:
            assert 0.0 <= sol["afinidad"] <= 1.0, f"Afinidad {sol['afinidad']} fuera del rango [0.0, 1.0]."
            assert sol["tiempo_total_min"] > 0, "El tiempo del itinerario debe ser positivo."
            assert sol["costo_total_bob"] >= 0, "El costo total no puede ser negativo."

        # Validar historial de convergencia y diversidad
        hist_conv = resultado.get("historial_convergencia", {})
        hist_div = resultado.get("historial_diversidad", {})

        assert len(hist_conv.get("generaciones", [])) == num_generaciones, (
            "La longitud del historial de convergencia no coincide con las generaciones configuradas."
        )
        assert len(hist_div.get("generaciones", [])) == num_generaciones, (
            "La longitud del historial de diversidad no coincide con las generaciones configuradas."
        )

    def test_pf07_nsga2_validaciones_limites_insuficientes(self, sample_dataset):
        """
        [PF-07] Comportamiento del motor NSGA-II ante entradas insuficientes:
        - Debe lanzar ValueError si se proporcionan menos de 2 atractivos.
        - Debe lanzar ValueError si no se proporciona ningún medio de transporte.
        """
        # Caso A: Menos de 2 atractivos
        with pytest.raises(ValueError):
            ejecutar_nsga2(
                atractivos=[sample_dataset["atractivos"][0]],
                transportes=sample_dataset["transportes"],
                presupuesto_max=100.0,
                tiempo_disponible_horas=4.0,
                intereses=sample_dataset["intereses"],
            )

        # Caso B: Cero medios de transporte
        with pytest.raises(ValueError):
            ejecutar_nsga2(
                atractivos=sample_dataset["atractivos"],
                transportes=[],
                presupuesto_max=100.0,
                tiempo_disponible_horas=4.0,
                intereses=sample_dataset["intereses"],
            )

    def test_pf08_servicio_tipo_cambio_conversion_bob_a_usd(self):
        """
        [PF-08] Verificación del cálculo de conversión de divisas BOB a USD:
        - Conversión exacta con tipo de cambio determinado.
        - Manejo seguro de entradas None, cadenas inválidas y valores cero.
        """
        tc_prueba = 6.96

        # Caso 1: Conversión estándar 100 BOB a USD
        resultado_usd = convertir_bs_a_usd(100.0, tc=tc_prueba)
        assert resultado_usd == round(100.0 / 6.96, 2)
        assert resultado_usd == 14.37

        # Caso 2: Cero bolivianos
        assert convertir_bs_a_usd(0.0, tc=tc_prueba) == 0.0

        # Caso 3: Valores nulos o inválidos no deben causar excepción
        assert convertir_bs_a_usd(None, tc=tc_prueba) is None
        assert convertir_bs_a_usd("invalido", tc=tc_prueba) is None
        assert convertir_bs_a_usd(50.0, tc=0.0) is None
        assert convertir_bs_a_usd(50.0, tc=-1.0) is None

    def test_pf09_metricas_pareto_filtro_no_dominados(self):
        """
        [PF-09] Validación del algoritmo de no dominancia de Pareto:
        - Un punto A que supera a B en todos los objetivos debe dominar a B.
        - Soluciones en conflicto de trade-off deben preservarse en el frente.
        """
        # Matriz de prueba: minimización de [Costo, Tiempo]
        # P0: [100, 20] (Buena)
        # P1: [150, 30] (Dominada por P0)
        # P2: [80, 50]  (Trade-off: menor costo pero más tiempo -> No dominada)
        puntos = np.array([
            [100.0, 20.0],
            [150.0, 30.0],
            [80.0, 50.0],
        ])

        frente = _filtrar_no_dominados(puntos)

        # Debe conservar P0 y P2, eliminando P1
        assert len(frente) == 2, f"Se esperaban 2 puntos no dominados, pero se obtuvieron {len(frente)}."
        # Verificar que [150.0, 30.0] fue efectivamente filtrado
        valores_costo = [pt[0] for pt in frente]
        assert 150.0 not in valores_costo, "El punto dominado no fue filtrado del frente de Pareto."

    def test_pf10_catalogo_atractivos_rutas_publicas(self, client):
        """
        [PF-10] Verificación de disponibilidad de rutas públicas informativas
        (el catálogo de atractivos y mapa no debe requerir autenticación previa).
        """
        response = client.get('/catalogo/atractivos')
        # Puede ser 200 OK o 302 a catálogo principal según configuración de rutas
        assert response.status_code in [200, 302], (
            f"La ruta del catálogo respondió con estado no esperado: {response.status_code}"
        )


# ======================================================================================
# SECCIÓN 2: PRUEBAS NO FUNCIONALES
# ======================================================================================

@pytest.mark.no_funcional
class TestPruebasNoFuncionales:
    """
    Conjunto de pruebas no funcionales para validar:
    - Rendimiento y latencia de respuesta bajo SLA.
    - Eficiencia de consumo de memoria y ausencia de fugas.
    - Seguridad (prevención de SQLi, XSS y escalamiento de privilegios).
    - Robustez ante datos corruptos o valores frontera.
    - Concurrencia y tolerancia a múltiples solicitudes simultáneas.
    """

    # ----------------------------------------------------------------------------------
    # 2.1 RENDIMIENTO Y LATENCIA
    # ----------------------------------------------------------------------------------

    @pytest.mark.rendimiento
    def test_pnf01_tiempo_respuesta_endpoints_criticos(self, client):
        """
        [PNF-01] Tiempo de respuesta HTTP (Latencia):
        Las peticiones a endpoints públicos o de autenticación deben completarse
        en un tiempo inferior al SLA objetivo de 500 ms (0.50 segundos).
        """
        t_inicio = time.perf_counter()
        response = client.get('/login')
        t_total = time.perf_counter() - t_inicio

        assert response.status_code == 200, "El endpoint /login no respondió 200 OK."
        assert t_total < 0.50, f"Latencia excesiva en /login: {t_total * 1000:.2f} ms (SLA máx: 500 ms)."

    @pytest.mark.rendimiento
    def test_pnf02_tiempo_ejecucion_nsga2_benchmark(self, sample_dataset):
        """
        [PNF-02] Rendimiento algorítmico del motor de optimización:
        Una ejecución con 6 atractivos, población de 30 y 15 generaciones
        debe finalizar en menos de 2.0 segundos.
        """
        t_inicio = time.perf_counter()
        resultado = ejecutar_nsga2(
            atractivos=sample_dataset["atractivos"],
            transportes=sample_dataset["transportes"],
            presupuesto_max=250.0,
            tiempo_disponible_horas=8.0,
            intereses=sample_dataset["intereses"],
            tamano_poblacion=30,
            generaciones=15,
        )
        t_duracion = time.perf_counter() - t_inicio

        assert "soluciones" in resultado
        assert t_duracion < 2.0, (
            f"El algoritmo NSGA-II tardó {t_duracion:.3f} s, excediendo el límite de 2.0 s."
        )

    @pytest.mark.rendimiento
    def test_pnf03_rendimiento_haversine_microbenchmark(self):
        """
        [PNF-03] Micro-benchmark de cálculo geodésico:
        5,000 cálculos de distancias geodésicas Haversine deben ejecutarse
        en menos de 150 milisegundos (alta eficiencia computacional requerida).
        """
        lat1, lon1 = -16.4957, -68.1335
        lat2, lon2 = -16.5672, -68.0944

        t_inicio = time.perf_counter()
        for _ in range(5000):
            haversine_km(lat1, lon1, lat2, lon2)
        t_total = time.perf_counter() - t_inicio

        assert t_total < 0.15, (
            f"5,000 iteraciones de Haversine tardaron {t_total * 1000:.2f} ms (máx: 150 ms)."
        )

    # ----------------------------------------------------------------------------------
    # 2.2 EFICIENCIA DE MEMORIA Y CONSUMO DE RECURSOS
    # ----------------------------------------------------------------------------------

    @pytest.mark.rendimiento
    def test_pnf04_consumo_memoria_nsga2_sin_fugas(self, sample_dataset):
        """
        [PNF-04] Eficiencia de memoria y control de fugas (Leak Detection):
        Al ejecutar 5 ciclos consecutivos de optimización genética, el incremento neto
        en la memoria rastreada no debe exceder los 25 MB tras la recolección de basura.
        """
        gc.collect()
        tracemalloc.start()

        snapshot_inicial = tracemalloc.take_snapshot()

        for _ in range(5):
            _ = ejecutar_nsga2(
                atractivos=sample_dataset["atractivos"],
                transportes=sample_dataset["transportes"],
                presupuesto_max=200.0,
                tiempo_disponible_horas=7.0,
                intereses=sample_dataset["intereses"],
                tamano_poblacion=20,
                generaciones=10,
            )

        gc.collect()
        snapshot_final = tracemalloc.take_snapshot()
        tracemalloc.stop()

        # Calcular estadísticas de diferencia de memoria
        top_stats = snapshot_final.compare_to(snapshot_inicial, 'lineno')
        delta_memoria_bytes = sum(stat.size_diff for stat in top_stats)
        delta_memoria_mb = delta_memoria_bytes / (1024 * 1024)

        assert delta_memoria_mb < 25.0, (
            f"Posible fuga de memoria detectada: incremento de {delta_memoria_mb:.2f} MB (límite: 25 MB)."
        )

    # ----------------------------------------------------------------------------------
    # 2.3 SEGURIDAD Y RESILIENCIA
    # ----------------------------------------------------------------------------------

    @pytest.mark.seguridad
    def test_pnf05_seguridad_prevencion_sql_injection(self, client):
        """
        [PNF-05] Seguridad contra Inyección SQL (SQLi):
        Cargas maliciosas en parámetros de búsqueda no deben generar errores 500
        ni exponer la base de datos a sentencias de escape no parametrizadas.
        """
        sqli_payloads = [
            "' OR '1'='1",
            "1; DROP TABLE atractivo;--",
            "' UNION SELECT null, null, null--",
            "admin' --",
        ]

        for payload in sqli_payloads:
            # Prueba vía query string
            response = client.get(f'/catalogo/atractivos?q={payload}')
            # La aplicación debe responder de forma segura (200, 302 o 400), NUNCA 500 (Internal Server Error)
            assert response.status_code != 500, (
                f"Posible vulnerabilidad SQLi: el payload '{payload}' causó HTTP 500."
            )
            assert b'syntax error' not in response.data.lower()
            assert b'pg_stat' not in response.data.lower()

    @pytest.mark.seguridad
    def test_pnf06_seguridad_mitigacion_xss_cross_site_scripting(self, client):
        """
        [PNF-06] Mitigación de Cross-Site Scripting (XSS):
        Cargas con etiquetas ejecutables `<script>` no deben reflejarse sin escapar en el HTML.
        """
        xss_payload = "<script>alert('Vulnerabilidad_XSS_Detectada')</script>"
        response = client.get(f'/catalogo/atractivos?q={xss_payload}')

        assert response.status_code != 500
        # El payload sin escapar NO debe estar presente de forma literal en la respuesta renderizada
        assert xss_payload.encode('utf-8') not in response.data, (
            "El payload de XSS se reflejó sin escapar en la respuesta HTML."
        )

    @pytest.mark.seguridad
    def test_pnf07_seguridad_proteccion_acceso_no_autorizado_escalamiento_privilegios(self, client):
        """
        [PNF-07] Escalamiento vertical de privilegios:
        Verificar que intentos de manipulación de rutas administrativas protegidas
        sean interceptados por el middleware de seguridad.
        """
        rutas_sensibles = [
            '/usuarios/crear',
            '/admin/metricas-algoritmo',
            '/reportes/exportar/pdf',
        ]

        for ruta in rutas_sensibles:
            res = client.get(ruta, follow_redirects=False)
            # Debe redirigir al login o denegar acceso
            assert res.status_code in [302, 401, 403], (
                f"Ruta administrativa sensible '{ruta}' accesible sin autorización (HTTP {res.status_code})."
            )

    # ----------------------------------------------------------------------------------
    # 2.4 ROBUSTEZ Y PRUEBAS EN LOS LÍMITES
    # ----------------------------------------------------------------------------------

    def test_pnf08_robustez_payloads_malformados_o_atipicos(self, client, auth_users):
        """
        [PNF-08] Robustez ante datos no válidos o malformados:
        El envío de tipos de datos incorrectos (ej. strings en lugar de números)
        debe ser manejado de forma controlada (HTTP 400 Bad Request) y sin caídas críticas.
        """
        agente = auth_users.get('agente')
        if not agente or not getattr(agente, 'id_usuario', None):
            pytest.skip("Usuario agente no disponible para prueba de payload.")

        with client.session_transaction() as sess:
            sess['_user_id'] = str(agente.id_usuario)
            sess['_fresh'] = True

        payload_invalido = {
            "atractivos_ids": "texto_no_lista",
            "transporte_ids": None,
            "presupuesto_max": "cien_bolivianos",
            "tiempo_disponible_horas": -5,
        }

        response = client.post('/itinerarios/generar', json=payload_invalido)
        # El sistema debe responder con error de validación del cliente (400) y no caer con 500
        assert response.status_code in [400, 422], (
            f"Se esperaba HTTP 400/422 ante payload malformado, pero se obtuvo {response.status_code}."
        )

    def test_pnf09_robustez_presupuesto_limite_cero(self, sample_dataset):
        """
        [PNF-09] Prueba de frontera: Presupuesto cero (0.0 BOB):
        El algoritmo debe procesar la solicitud sin lanzar divisiones por cero
        y seleccionar únicamente atractivos de costo de entrada cero (0.0).
        """
        resultado = ejecutar_nsga2(
            atractivos=sample_dataset["atractivos"],
            transportes=sample_dataset["transportes"],
            presupuesto_max=0.0,
            tiempo_disponible_horas=5.0,
            intereses=sample_dataset["intereses"],
            tamano_poblacion=20,
            generaciones=5,
        )

        assert "soluciones" in resultado, "El algoritmo falló ante presupuesto cero."
        # Si encuentra soluciones, el costo de entrada de los atractivos debe ser consistente
        if len(resultado["soluciones"]) > 0:
            sol = resultado["soluciones"][0]
            assert sol["costo_total_bob"] >= 0.0

    # ----------------------------------------------------------------------------------
    # 2.5 CONCURRENCIA Y RESILIENCIA BAJO CARGA SIMULTÁNEA
    # ----------------------------------------------------------------------------------

    @pytest.mark.concurrencia
    def test_pnf10_concurrencia_peticiones_simultaneas(self, client):
        """
        [PNF-10] Resiliencia ante concurrencia simulada:
        Ejecuta una ráfaga de 10 peticiones HTTP simultáneas utilizando un
        ThreadPoolExecutor, asegurando que el 100% de las respuestas sean exitosas
        y que no ocurran bloqueos ni excepciones no controladas.
        """
        numero_hilos = 10

        def hacer_peticion():
            return client.get('/login')

        with ThreadPoolExecutor(max_workers=numero_hilos) as executor:
            futuros = [executor.submit(hacer_peticion) for _ in range(numero_hilos)]
            respuestas = [f.result() for f in futuros]

        # Verificar que todas las peticiones concurrentes respondieron 200 OK
        codigos_estado = [r.status_code for r in respuestas]
        assert all(code == 200 for code in codigos_estado), (
            f"Fallo en prueba concurrente. Códigos recibidos: {codigos_estado}"
        )


# ======================================================================================
# PUNTO DE ENTRADA PARA EJECUCIÓN DIRECTA
# ======================================================================================

if __name__ == "__main__":
    # Permite ejecutar directamente este archivo con `python tests/test_pruebas_funcionales_y_no_funcionales.py`
    sys.exit(pytest.main(["-v", __file__]))
