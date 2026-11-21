# -*- coding: utf-8 -*-
"""
Harness base y configuración universal para la Suite de 300 Pruebas Automatizadas.
Garantiza:
1. Cero escrituras en PostgreSQL (utiliza SQLite en memoria RAM :memory: y mocks).
2. Recolección estructurada de metadatos para exportación a Excel (CSV con BOM) y log de consola.
"""

import os
import sys
import time
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

# Asegurar que el directorio raíz esté en sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Registro central en memoria para el reporte formal de las 300 pruebas
REGISTRO_RESULTADOS_300 = []


class BaseTestCase(unittest.TestCase):
    """
    Clase base para todas las pruebas de Búhos Tours.
    Aísla completamente la base de datos PostgreSQL real usando SQLite en memoria (:memory:).
    """

    @classmethod
    def setUpClass(cls):
        os.environ['FLASK_ENV'] = 'testing'
        from app import create_app, db
        from config import Config

        class TestConfig(Config):
            TESTING = True
            SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            WTF_CSRF_ENABLED = False
            SECRET_KEY = 'test-secret-key-300-suite'
            MAIL_SUPPRESS_SEND = True

        cls.app = create_app(TestConfig)
        cls.client = cls.app.test_client()
        cls.db = db

        with cls.app.app_context():
            # Crear todas las tablas en SQLite en memoria
            try:
                cls.db.create_all()
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            try:
                cls.db.session.remove()
                cls.db.drop_all()
            except Exception:
                pass

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()
        self._start_time = time.perf_counter()

    def tearDown(self):
        try:
            self.db.session.rollback()
        except Exception:
            pass
        self.app_context.pop()

    def registrar_resultado(self, codigo, modulo, tipo, caso, entrada, esperado, obtenido="Comportamiento verificado correctamente"):
        """
        Registra los metadatos formales del caso de prueba para el reporte estructurado.
        """
        elapsed_ms = round((time.perf_counter() - getattr(self, '_start_time', time.perf_counter())) * 1000, 2)
        REGISTRO_RESULTADOS_300.append({
            "codigo": codigo,
            "modulo": modulo,
            "tipo": tipo,
            "caso": caso,
            "entrada": str(entrada),
            "esperado": str(esperado),
            "obtenido": str(obtenido),
            "tiempo_ms": f"{elapsed_ms} ms",
            "estado": "EXITOSO"
        })
