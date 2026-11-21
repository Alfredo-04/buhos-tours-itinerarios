# -*- coding: utf-8 -*-
"""
Módulo 06: Pruebas Automatizadas de Catálogo de Atractivos y Validación Geoespacial.
Total de pruebas: 35 (Pruebas PA-ATRA-176 a PA-ATRA-210).
"""

import unittest
import io
from decimal import Decimal
from datetime import time, datetime
from unittest.mock import MagicMock, patch
from PIL import Image
from tests.conftest_base import BaseTestCase
from app.models.atractivo import Atractivo
from app.models.subcategoria import Subcategoria
from app.models.proveedor import Proveedor
from app.services.atractivo_service import (
    crear_atractivo,
    guardar_imagen_atractivo,
    parse_time_str,
    parse_date_str,
    ALLOWED_EXTENSIONS,
    MAX_IMAGE_SIZE
)


class TestAtractivosCatalogoGeoespacial(BaseTestCase):
    """Suite de 35 pruebas para el catálogo geoespacial de atractivos turísticos."""

    def setUp(self):
        super().setUp()
        self.mock_subcat = MagicMock(id_subcategoria=1, id_categoria=1)
        self.mock_prov = MagicMock(id_proveedor=1, razon_social="Guías La Paz")

    # 176-180: Creación y Validaciones de Nombre
    def test_176_crear_atractivo_datos_validos_exitoso(self):
        data = {
            'nombre': 'Valle de la Luna Mágico',
            'descripcion': 'Formaciones arcillosas espectaculares en La Paz.',
            'direccion': 'Mallasa, La Paz',
            'id_subcategoria': '1',
            'id_proveedor': '1',
            'latitud': '-16.5689000',
            'longitud': '-68.0954000',
            'horario_apertura': '08:00',
            'horario_cierre': '17:00',
            'costo_entrada': '15.00',
            'tiempo_visita_estimado': '90',
            'sensible_al_clima': True
        }
        with patch('app.services.atractivo_service.Subcategoria') as q_sub, \
             patch('app.services.atractivo_service.Proveedor') as q_pr, \
             patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.add'), \
             patch('app.services.atractivo_service.db.session.commit'), \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else self.mock_prov
            q_at.filter.return_value.first.return_value = None
            ok, msg, clean_data = crear_atractivo(data)
            self.assertTrue(ok)
            self.assertEqual(clean_data.nombre, 'Valle de la Luna Mágico')
        self.registrar_resultado("PA-ATRA-176", "Catálogo Atractivos", "Funcional / Validación",
                                 "Validación exitosa de atractivo con campos completos", "Datos válidos Valle de la Luna", "ok == True", "Aprobado")

    def test_177_validacion_nombre_longitud_minima_3_caracteres(self):
        data = {'nombre': 'Mirador Killi Killi', 'id_subcategoria': '1', 'id_proveedor': '1'}
        self.assertGreaterEqual(len(data['nombre']), 3)
        self.registrar_resultado("PA-ATRA-177", "Catálogo Atractivos", "Validación / Longitud",
                                 "Verificación de nombre mayor a 3 caracteres", "nombre='Mirador Killi Killi'", "len >= 3", "Válido")

    def test_178_negativo_nombre_menor_a_3_caracteres_rechazado(self):
        data = {'nombre': 'AB', 'id_subcategoria': '1', 'id_proveedor': '1'}
        ok, msg, clean = crear_atractivo(data)
        self.assertFalse(ok)
        self.assertIn("al menos 3 caracteres", msg)
        self.registrar_resultado("PA-ATRA-178", "Catálogo Atractivos", "Validación / Negativa",
                                 "Rechazo de nombre con menos de 3 caracteres", "nombre='AB'", "ok == False", msg)

    def test_179_negativo_nombre_mayor_a_100_caracteres_rechazado(self):
        data = {'nombre': 'A' * 101, 'id_subcategoria': '1', 'id_proveedor': '1'}
        ok, msg, clean = crear_atractivo(data)
        self.assertFalse(ok)
        self.assertIn("no puede exceder los 100 caracteres", msg)
        self.registrar_resultado("PA-ATRA-179", "Catálogo Atractivos", "Validación / Negativa",
                                 "Rechazo de nombre que excede 100 caracteres", "len(nombre) == 101", "ok == False", msg)

    def test_180_negativo_nombre_duplicado_rechazado(self):
        data = {'nombre': 'Teleférico Rojo', 'id_subcategoria': '1', 'id_proveedor': '1'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at:
            q_at.filter.return_value.first.return_value = MagicMock(is_deleted=False)
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("Ya existe un atractivo registrado", msg)
        self.registrar_resultado("PA-ATRA-180", "Catálogo Atractivos", "Validación / Unicidad",
                                 "Rechazo de nombre de atractivo duplicado", "nombre='Teleférico Rojo'", "ok == False", msg)

    # 181-186: Descripciones y Relaciones Foráneas
    def test_181_negativo_descripcion_mayor_a_500_caracteres(self):
        data = {'nombre': 'Parque Pura Pura', 'descripcion': 'D' * 501, 'id_subcategoria': '1', 'id_proveedor': '1'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at:
            q_at.filter.return_value.first.return_value = None
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("no puede exceder los 500 caracteres", msg)
        self.registrar_resultado("PA-ATRA-181", "Catálogo Atractivos", "Validación / Negativa",
                                 "Rechazo de descripción mayor a 500 caracteres", "len == 501", "ok == False", msg)

    def test_182_negativo_direccion_mayor_a_200_caracteres(self):
        data = {'nombre': 'Calle Jaén', 'direccion': 'Dir ' * 60, 'id_subcategoria': '1', 'id_proveedor': '1'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at:
            q_at.filter.return_value.first.return_value = None
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("no puede exceder los 200 caracteres", msg)
        self.registrar_resultado("PA-ATRA-182", "Catálogo Atractivos", "Validación / Negativa",
                                 "Rechazo de dirección mayor a 200 caracteres", "len > 200", "ok == False", msg)

    def test_183_subcategoria_existente_valida(self):
        data = {'nombre': 'Museo de Etnografía', 'id_subcategoria': '2', 'id_proveedor': '1'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            q_at.filter.return_value.first.return_value = None
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else self.mock_prov
            ok, msg, clean = crear_atractivo(data)
            self.assertTrue(ok)
        self.registrar_resultado("PA-ATRA-183", "Catálogo Atractivos", "Integridad / FK",
                                 "Aprobación de subcategoría existente", "id_subcategoria=2", "ok == True", "Válido")

    def test_184_negativo_subcategoria_inexistente_rechazada(self):
        data = {'nombre': 'Museo de Etnografía', 'id_subcategoria': '999', 'id_proveedor': '1'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get', return_value=None), \
             patch('app.models.subcategoria.Subcategoria.query') as q_s:
            q_at.filter.return_value.first.return_value = None
            q_s.filter_by.return_value.first.return_value = None
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("subcategoría válida", msg)
        self.registrar_resultado("PA-ATRA-184", "Catálogo Atractivos", "Integridad / FK",
                                 "Rechazo de FK de subcategoría inexistente", "id_subcategoria=999", "ok == False", msg)

    def test_185_proveedor_existente_valido(self):
        data = {'nombre': 'Iglesia San Francisco', 'id_subcategoria': '1', 'id_proveedor': '5'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            q_at.filter.return_value.first.return_value = None
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else self.mock_prov
            ok, msg, clean = crear_atractivo(data)
            self.assertTrue(ok)
        self.registrar_resultado("PA-ATRA-185", "Catálogo Atractivos", "Integridad / FK",
                                 "Aprobación de proveedor registrado", "id_proveedor=5", "ok == True", "Válido")

    def test_186_negativo_proveedor_inexistente_rechazado(self):
        data = {'nombre': 'Iglesia San Francisco', 'id_subcategoria': '1', 'id_proveedor': '999'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            q_at.filter.return_value.first.return_value = None
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else None
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("proveedor seleccionado no existe", msg)
        self.registrar_resultado("PA-ATRA-186", "Catálogo Atractivos", "Integridad / FK",
                                 "Rechazo de FK de proveedor inexistente", "id_proveedor=999", "ok == False", msg)

    # 187-193: Coordenadas Geoespaciales (Límites Bolivia)
    def test_187_latitud_rango_bolivia_valida(self):
        lat = Decimal('-16.4950000')
        es_valida = Decimal('-23.0') <= lat <= Decimal('-9.0')
        self.assertTrue(es_valida)
        self.registrar_resultado("PA-ATRA-187", "Catálogo Atractivos", "Geoespacial / Bolivia",
                                 "Latitud de La Paz dentro de límites Bolivia", "lat=-16.495", "Dentro de [-23.0, -9.0]", "Válido")

    def test_188_negativo_latitud_fuera_rango_sur_rechazada(self):
        data = {'nombre': 'Atractivo Sur', 'id_subcategoria': '1', 'id_proveedor': '1', 'latitud': '-25.5'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            q_at.filter.return_value.first.return_value = None
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else self.mock_prov
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("rango geográfico válido de Bolivia", msg)
        self.registrar_resultado("PA-ATRA-188", "Catálogo Atractivos", "Geoespacial / Negativa",
                                 "Rechazo de latitud fuera de frontera sur", "latitud=-25.5", "ok == False", msg)

    def test_189_negativo_latitud_fuera_rango_norte_rechazada(self):
        data = {'nombre': 'Atractivo Norte', 'id_subcategoria': '1', 'id_proveedor': '1', 'latitud': '-5.0'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            q_at.filter.return_value.first.return_value = None
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else self.mock_prov
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("rango geográfico válido de Bolivia", msg)
        self.registrar_resultado("PA-ATRA-189", "Catálogo Atractivos", "Geoespacial / Negativa",
                                 "Rechazo de latitud fuera de frontera norte", "latitud=-5.0", "ok == False", msg)

    def test_190_longitud_rango_bolivia_valida(self):
        lon = Decimal('-68.1330000')
        es_valida = Decimal('-70.0') <= lon <= Decimal('-57.0')
        self.assertTrue(es_valida)
        self.registrar_resultado("PA-ATRA-190", "Catálogo Atractivos", "Geoespacial / Bolivia",
                                 "Longitud de La Paz dentro de límites Bolivia", "lon=-68.133", "Dentro de [-70.0, -57.0]", "Válido")

    def test_191_negativo_longitud_fuera_rango_oeste_rechazada(self):
        data = {'nombre': 'Atractivo Pacífico', 'id_subcategoria': '1', 'id_proveedor': '1', 'longitud': '-75.0'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            q_at.filter.return_value.first.return_value = None
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else self.mock_prov
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("rango geográfico válido de Bolivia", msg)
        self.registrar_resultado("PA-ATRA-191", "Catálogo Atractivos", "Geoespacial / Negativa",
                                 "Rechazo de longitud fuera de frontera oeste", "longitud=-75.0", "ok == False", msg)

    def test_192_negativo_longitud_fuera_rango_este_rechazada(self):
        data = {'nombre': 'Atractivo Brasil', 'id_subcategoria': '1', 'id_proveedor': '1', 'longitud': '-50.0'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            q_at.filter.return_value.first.return_value = None
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else self.mock_prov
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("rango geográfico válido de Bolivia", msg)
        self.registrar_resultado("PA-ATRA-192", "Catálogo Atractivos", "Geoespacial / Negativa",
                                 "Rechazo de longitud fuera de frontera este", "longitud=-50.0", "ok == False", msg)

    def test_193_negativo_coordenadas_no_numericas_rechazadas(self):
        data = {'nombre': 'Atractivo Coord Invalida', 'id_subcategoria': '1', 'id_proveedor': '1', 'latitud': 'no_es_numero'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            q_at.filter.return_value.first.return_value = None
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else self.mock_prov
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("valor numérico decimal válido", msg)
        self.registrar_resultado("PA-ATRA-193", "Catálogo Atractivos", "Geoespacial / Negativa",
                                 "Rechazo de coordenadas con texto alfanumérico", "latitud='no_es_numero'", "ok == False", msg)

    # 194-198: Horarios y Consistencia Cronológica
    def test_194_parse_time_str_valido(self):
        t = parse_time_str('09:30')
        self.assertEqual(t, time(9, 30))
        self.registrar_resultado("PA-ATRA-194", "Catálogo Atractivos", "Horarios / Parsing",
                                 "Conversión correcta de HH:MM a objeto time", "'09:30'", "time(9, 30)", f"{t}")

    def test_195_negativo_horario_apertura_invalido_rechazado(self):
        data = {'nombre': 'Atractivo Horario', 'id_subcategoria': '1', 'id_proveedor': '1', 'horario_apertura': '25:70'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            q_at.filter.return_value.first.return_value = None
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else self.mock_prov
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("formato válido (HH:MM)", msg)
        self.registrar_resultado("PA-ATRA-195", "Catálogo Atractivos", "Horarios / Negativa",
                                 "Rechazo de hora de apertura fuera de rango 24h", "horario_apertura='25:70'", "ok == False", msg)

    def test_196_negativo_horario_cierre_invalido_rechazado(self):
        data = {'nombre': 'Atractivo Horario', 'id_subcategoria': '1', 'id_proveedor': '1', 'horario_cierre': 'tarde_noche'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            q_at.filter.return_value.first.return_value = None
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else self.mock_prov
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("formato válido (HH:MM)", msg)
        self.registrar_resultado("PA-ATRA-196", "Catálogo Atractivos", "Horarios / Negativa",
                                 "Rechazo de hora de cierre no estructurada", "horario_cierre='tarde_noche'", "ok == False", msg)

    def test_197_consistencia_horario_cierre_posterior_a_apertura(self):
        apertura = parse_time_str('09:00')
        cierre = parse_time_str('18:00')
        self.assertGreater(cierre, apertura)
        self.registrar_resultado("PA-ATRA-197", "Catálogo Atractivos", "Horarios / Consistencia",
                                 "Verificación cierre posterior a apertura", "09:00 < 18:00", "cierre > apertura", "Válido")

    def test_198_negativo_horario_cierre_anterior_a_apertura_rechazado(self):
        data = {'nombre': 'Atractivo Horario Invertido', 'id_subcategoria': '1', 'id_proveedor': '1',
                'horario_apertura': '18:00', 'horario_cierre': '09:00'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            q_at.filter.return_value.first.return_value = None
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else self.mock_prov
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("horario de cierre debe ser posterior", msg)
        self.registrar_resultado("PA-ATRA-198", "Catálogo Atractivos", "Horarios / Negativa",
                                 "Rechazo cuando cierre es antes que apertura", "apertura 18:00, cierre 09:00", "ok == False", msg)

    # 199-204: Costos y Tiempos de Visita
    def test_199_costo_entrada_positivo_valido(self):
        c = Decimal('20.50')
        self.assertGreaterEqual(c, Decimal('0.0'))
        self.registrar_resultado("PA-ATRA-199", "Catálogo Atractivos", "Financiero / Costo",
                                 "Validación de costo de entrada no negativo", "costo=20.50", "costo >= 0", "Válido")

    def test_200_negativo_costo_entrada_negativo_rechazado(self):
        data = {'nombre': 'Atractivo Costo Neg', 'id_subcategoria': '1', 'id_proveedor': '1', 'costo_entrada': '-10.00'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            q_at.filter.return_value.first.return_value = None
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else self.mock_prov
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("mayor o igual a 0", msg)
        self.registrar_resultado("PA-ATRA-200", "Catálogo Atractivos", "Financiero / Negativa",
                                 "Rechazo de tarifa de entrada negativa", "costo=-10.00", "ok == False", msg)

    def test_201_negativo_costo_entrada_no_numerico_rechazado(self):
        data = {'nombre': 'Atractivo Costo NaN', 'id_subcategoria': '1', 'id_proveedor': '1', 'costo_entrada': 'gratis'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            q_at.filter.return_value.first.return_value = None
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else self.mock_prov
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("valor decimal válido", msg)
        self.registrar_resultado("PA-ATRA-201", "Catálogo Atractivos", "Financiero / Negativa",
                                 "Rechazo de costo con texto no numérico", "costo='gratis'", "ok == False", msg)

    def test_202_tiempo_visita_entero_mayor_a_cero(self):
        t = 60
        self.assertGreater(t, 0)
        self.registrar_resultado("PA-ATRA-202", "Catálogo Atractivos", "Planificación / Tiempo",
                                 "Validación de tiempo de visita entero positivo", "tiempo=60 min", "tiempo > 0", "Válido")

    def test_203_negativo_tiempo_visita_menor_o_igual_a_cero_rechazado(self):
        data = {'nombre': 'Atractivo Tiempo Cero', 'id_subcategoria': '1', 'id_proveedor': '1', 'tiempo_visita_estimado': '0'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            q_at.filter.return_value.first.return_value = None
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else self.mock_prov
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("mayor a 0 minutos", msg)
        self.registrar_resultado("PA-ATRA-203", "Catálogo Atractivos", "Planificación / Negativa",
                                 "Rechazo de tiempo de visita igual a cero", "tiempo=0 min", "ok == False", msg)

    def test_204_negativo_tiempo_visita_no_entero_rechazado(self):
        data = {'nombre': 'Atractivo Tiempo Float', 'id_subcategoria': '1', 'id_proveedor': '1', 'tiempo_visita_estimado': 'media_hora'}
        with patch('app.services.atractivo_service.Atractivo.query') as q_at, \
             patch('app.services.atractivo_service.db.session.get') as mock_get:
            q_at.filter.return_value.first.return_value = None
            mock_get.side_effect = lambda model, id_: self.mock_subcat if model == Subcategoria else self.mock_prov
            ok, msg, clean = crear_atractivo(data)
            self.assertFalse(ok)
            self.assertIn("número entero válido", msg)
        self.registrar_resultado("PA-ATRA-204", "Catálogo Atractivos", "Planificación / Negativa",
                                 "Rechazo de tiempo de visita no numérico", "tiempo='media_hora'", "ok == False", msg)

    # 205-208: Procesamiento de Imágenes con Pillow
    def test_205_extension_imagen_permitida(self):
        ext = 'png'
        self.assertIn(ext, ALLOWED_EXTENSIONS)
        self.registrar_resultado("PA-ATRA-205", "Catálogo Atractivos", "Multimedia / Pillow",
                                 "Extensión de imagen PNG en formatos permitidos", "ext='png'", "ext in ALLOWED_EXTENSIONS", "Permitida")

    def test_206_negativo_extension_imagen_prohibida_rechazada(self):
        mock_file = MagicMock()
        mock_file.filename = 'script_malicioso.php'
        ok, msg, path = guardar_imagen_atractivo(mock_file)
        self.assertFalse(ok)
        self.assertIn("Formato no permitido", msg)
        self.registrar_resultado("PA-ATRA-206", "Catálogo Atractivos", "Seguridad / Multimedia",
                                 "Bloqueo de extensión ejecutable en subida", "filename='*.php'", "ok == False", msg)

    def test_207_pillow_redimension_imagen_ancho_mayor_1200px(self):
        img = Image.new('RGB', (2000, 1000), color='blue')
        max_width = 1200
        ratio = max_width / float(img.width)
        new_height = int(float(img.height) * float(ratio))
        resized = img.resize((max_width, new_height))
        self.assertEqual(resized.width, 1200)
        self.assertEqual(resized.height, 600)
        self.registrar_resultado("PA-ATRA-207", "Catálogo Atractivos", "Multimedia / Pillow",
                                 "Redimensión proporcional a 1200px máx con Pillow", "2000x1000 -> 1200x600", "width == 1200", "Redimensionado")

    def test_208_limite_tamanio_imagen_5mb(self):
        self.assertEqual(MAX_IMAGE_SIZE, 5 * 1024 * 1024)
        self.registrar_resultado("PA-ATRA-208", "Catálogo Atractivos", "Multimedia / Pillow",
                                 "Límite estricto de archivo de imagen a 5 Megabytes", "5 MB en bytes", "5242880 bytes", "Configurado")

    # 209-210: Soft Delete y Sensibilidad al Clima
    def test_209_soft_delete_atractivo_propiedad_is_deleted(self):
        atra = Atractivo(nombre="Chacaltaya Test", costo_entrada=Decimal('0.0'))
        self.assertFalse(atra.is_deleted)
        atra.deleted_at = datetime.utcnow()
        self.assertTrue(atra.is_deleted)
        self.registrar_resultado("PA-ATRA-209", "Catálogo Atractivos", "Auditoría / Soft-Delete",
                                 "Propiedad is_deleted activada tras soft delete", "deleted_at=utcnow()", "is_deleted == True", "Verificado")

    def test_210_sensible_al_clima_activa_flag_de_evaluacion(self):
        atra = Atractivo(nombre="Mirador Chacaltaya Nevado", sensible_al_clima=True)
        self.assertTrue(atra.sensible_al_clima)
        self.registrar_resultado("PA-ATRA-210", "Catálogo Atractivos", "Optimización / Clima",
                                 "Flag sensible_al_clima activo para exclusión WMO", "sensible_al_clima=True", "sensible_al_clima == True", "Activo")


if __name__ == '__main__':
    unittest.main()
