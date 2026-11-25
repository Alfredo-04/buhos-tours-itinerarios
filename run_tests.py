# -*- coding: utf-8 -*-
"""
Orquestador Central de Pruebas Automatizadas (Suite de 300 Pruebas - Búhos Tours).
Ejecuta los 10 módulos de pruebas sin tocar la base de datos de producción (SQLite en memoria).

Regla de Generación Condicional de Reportes:
- Si alguna prueba falla: NO se crea ningún archivo.
- Si todas las pruebas (300) pasan Y los archivos de reporte no existen:
  Genera automáticamente:
  1. reports/matriz_pruebas_300.csv (Matriz limpia UTF-8 con BOM para Excel).
  2. reports/ejecucion_consola.log (Registro completo de la consola).
- Si los archivos de reporte ya existen: ejecuta las pruebas normalmente sin sobreescribir.
"""

import sys
import os
import io
import csv
import unittest
import time

# Asegurar path raíz del proyecto
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Importar lista compartida de resultados
from tests.conftest_base import REGISTRO_RESULTADOS_300
from tests.benchmark_optimizacion import generar_graficos_cientificos_optimizacion
from tests.benchmark_sqa import generar_graficos_sqa


class DualOutput(io.StringIO):
    """Duplica la salida estándar hacia la consola real y hacia un buffer en memoria."""
    def __init__(self, terminal_stream):
        super().__init__()
        self.terminal = terminal_stream

    def write(self, s):
        super().write(s)
        self.terminal.write(s)
        self.terminal.flush()

    def flush(self):
        super().flush()
        self.terminal.flush()


def main():
    print("=" * 80)
    print("      SISTEMA BÚHOS TOURS - SUITE DE 300 PRUEBAS AUTOMATIZADAS")
    print("  Entorno de Pruebas: Aislamiento Total en Memoria (SQLite In-Memory)")
    print("=" * 80)

    # Limpiar lista de resultados en memoria
    REGISTRO_RESULTADOS_300.clear()

    # Módulos ordenados de pruebas
    modulos = [
        "tests.test_01_nsga2_optimizacion",
        "tests.test_02_itinerarios_vouchers_qr",
        "tests.test_03_autenticacion_seguridad_2fa",
        "tests.test_04_control_acceso_rbac",
        "tests.test_05_usuarios_gestion_admin",
        "tests.test_06_atractivos_catalogo_geoespacial",
        "tests.test_07_proveedores_transportes",
        "tests.test_08_finanzas_clima_trafico",
        "tests.test_09_analitica_reportes_kpis",
        "tests.test_10_pruebas_no_funcionales"
    ]

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    for mod_name in modulos:
        try:
            mod_suite = loader.loadTestsFromName(mod_name)
            suite.addTests(mod_suite)
        except Exception as e:
            print(f"[ERROR CARGANDO MÓDULO] {mod_name}: {e}")
            sys.exit(1)

    total_pruebas_cargadas = suite.countTestCases()
    print(f"Total de pruebas descubiertas y programadas: {total_pruebas_cargadas}")
    print("-" * 80)

    # Interceptar salida para el archivo de log
    terminal_out = sys.stdout
    terminal_err = sys.stderr
    captured_stream = DualOutput(terminal_out)

    sys.stdout = captured_stream
    sys.stderr = captured_stream

    tiempo_inicio = time.time()
    runner = unittest.TextTestRunner(stream=captured_stream, verbosity=2)
    result = runner.run(suite)
    tiempo_total = time.time() - tiempo_inicio

    # Restaurar streams originales
    sys.stdout = terminal_out
    sys.stderr = terminal_err

    print("\n" + "=" * 80)
    print(f"Resumen de Ejecución:")
    print(f" - Pruebas Ejecutadas: {result.testsRun}")
    print(f" - Fallos (Failures): {len(result.failures)}")
    print(f" - Errores (Errors):   {len(result.errors)}")
    print(f" - Tiempo Total:       {tiempo_total:.2f} segundos")
    print(f" - Estado General:     {'EXITOSO (OK)' if result.wasSuccessful() else 'FALLIDO'}")
    print("=" * 80)

    reports_dir = os.path.join(BASE_DIR, 'reports')
    csv_file = os.path.join(reports_dir, 'matriz_pruebas_300.csv')
    log_file = os.path.join(reports_dir, 'ejecucion_consola.log')

    # Regla: Si falla alguna prueba, no crear ningún archivo
    if not result.wasSuccessful():
        print("\n[ATENCIÓN] Una o más pruebas fallaron.")
        print("[CONDICIÓN] No se ha creado ni modificado ningún archivo de reporte (matriz o log).")
        sys.exit(1)

    # Regla: Si todas pasaron Y los archivos NO existen -> Crear
    if not os.path.exists(csv_file) and not os.path.exists(log_file):
        os.makedirs(reports_dir, exist_ok=True)

        # 1. Guardar log de consola
        with open(log_file, 'w', encoding='utf-8') as f_log:
            f_log.write(captured_stream.getvalue())
        print(f"[GENERADO] Log de consola guardado exitosamente en: {log_file}")

        # 2. Guardar matriz limpia CSV en UTF-8 con BOM (para compatibilidad total con Excel)
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f_csv:
            writer = csv.writer(f_csv)
            # Cabecera
            writer.writerow([
                "Código",
                "Módulo",
                "Tipo de Prueba",
                "Caso de Prueba",
                "Entrada / Precondición",
                "Resultado Esperado",
                "Resultado Obtenido",
                "Tiempo (ms)",
                "Estado"
            ])
            # Filas registradas
            for fila in REGISTRO_RESULTADOS_300:
                writer.writerow([
                    fila.get("codigo", ""),
                    fila.get("modulo", ""),
                    fila.get("tipo", ""),
                    fila.get("caso", ""),
                    fila.get("entrada", ""),
                    fila.get("esperado", ""),
                    fila.get("obtenido", ""),
                    fila.get("tiempo_ms", ""),
                    fila.get("estado", "")
                ])
        print(f"[GENERADO] Matriz de pruebas CSV generada exitosamente en: {csv_file}")
        print(f"           (Total de casos documentados en matriz: {len(REGISTRO_RESULTADOS_300)})")

        # 3. Generar Gráficos Científicos de Optimización Multiobjetivo (300 DPI)
        try:
            graficos_creados = generar_graficos_cientificos_optimizacion(reports_dir)
            if graficos_creados:
                print(f"[GENERADO] {len(graficos_creados)} Gráficos científicos de optimización guardados en reports/:")
                for g in graficos_creados:
                    print(f"           • {os.path.basename(g)}")
        except Exception as e_graf:
            print(f"[ADVERTENCIA] Error generando gráficos científicos: {e_graf}")

        # 4. Generar Gráficos Formales de Calidad de Software (SQA - ISO/IEC 25010) (300 DPI)
        try:
            graficos_sqa_creados = generar_graficos_sqa(reports_dir, REGISTRO_RESULTADOS_300)
            if graficos_sqa_creados:
                print(f"[GENERADO] {len(graficos_sqa_creados)} Gráficos de Aseguramiento de Calidad (SQA) guardados en reports/:")
                for g in graficos_sqa_creados:
                    print(f"           • {os.path.basename(g)}")
        except Exception as e_sqa:
            print(f"[ADVERTENCIA] Error generando gráficos SQA: {e_sqa}")
    else:
        print("\n[INFO] Los archivos de reporte ya existen en la carpeta 'reports/'.")
        print("       Las pruebas se ejecutaron correctamente sin sobreescribir los archivos existentes.")

        # Verificar si falta algún gráfico en reports/ y crearlo de forma complementaria sin sobreescribir los demás
        try:
            graficos_faltantes = generar_graficos_cientificos_optimizacion(reports_dir)
            if graficos_faltantes:
                print(f"[GENERADO] {len(graficos_faltantes)} Gráficos de optimización faltantes generados en reports/:")
                for g in graficos_faltantes:
                    print(f"           • {os.path.basename(g)}")
            
            graficos_sqa_faltantes = generar_graficos_sqa(reports_dir, REGISTRO_RESULTADOS_300)
            if graficos_sqa_faltantes:
                print(f"[GENERADO] {len(graficos_sqa_faltantes)} Gráficos SQA faltantes generados en reports/:")
                for g in graficos_sqa_faltantes:
                    print(f"           • {os.path.basename(g)}")
        except Exception as e_graf:
            pass

    print("\nProceso finalizado con éxito.")


if __name__ == '__main__':
    main()
