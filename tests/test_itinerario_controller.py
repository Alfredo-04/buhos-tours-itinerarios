import unittest
import uuid
from datetime import datetime
from app import create_app, db
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.atractivo import Atractivo
from app.models.transporte import Transporte


class TestItinerarioController(unittest.TestCase):
    """
    Tests de integración para el controlador de generación de itinerarios turísticos.
    Valida control de acceso por roles (Admin, Agente, Turista, No autenticado),
    renderizado de vistas y procesamiento POST asíncrono con datos reales de la BD.
    """

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        # Crear usuarios temporales de prueba para cada rol
        self.rol_admin = Rol.query.filter_by(nombre='admin').first()
        self.rol_agente = Rol.query.filter_by(nombre='agente').first()
        self.rol_turista = Rol.query.filter_by(nombre='turista').first()

        self.admin_user = Usuario(
            nombres='Admin', apellidos='Itinerario',
            email=f'admin_itin_{uuid.uuid4().hex[:6]}@test.com',
            contrasenia='testpass', id_rol=self.rol_admin.id_rol,
            two_factor_enabled=True, two_factor_confirmed_at=datetime.utcnow(),
            must_change_password=False
        )

        self.agente_user = Usuario(
            nombres='Agente', apellidos='Itinerario',
            email=f'agente_itin_{uuid.uuid4().hex[:6]}@test.com',
            contrasenia='testpass', id_rol=self.rol_agente.id_rol,
            two_factor_enabled=True, two_factor_confirmed_at=datetime.utcnow(),
            must_change_password=False
        )

        self.turista_user = Usuario(
            nombres='Turista', apellidos='Itinerario',
            email=f'turista_itin_{uuid.uuid4().hex[:6]}@test.com',
            contrasenia='testpass', id_rol=self.rol_turista.id_rol,
            two_factor_enabled=False,
            must_change_password=False
        )

        db.session.add_all([self.admin_user, self.agente_user, self.turista_user])
        db.session.commit()

    def tearDown(self):
        # Limpiar usuarios de prueba
        Usuario.query.filter(Usuario.id_usuario.in_([
            self.admin_user.id_usuario,
            self.agente_user.id_usuario,
            self.turista_user.id_usuario
        ])).delete()
        db.session.commit()
        self.app_context.pop()

    def test_get_generar_no_autenticado(self):
        """Usuarios no autenticados deben ser redirigidos al login."""
        res = self.client.get('/itinerarios/generar')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))

    def test_get_generar_rol_turista_prohibido(self):
        """Usuarios con rol turista deben recibir 403 Forbidden."""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.turista_user.id_usuario)
            sess['_fresh'] = True

        res = self.client.get('/itinerarios/generar')
        self.assertEqual(res.status_code, 403)

    def test_get_generar_rol_agente_permitido(self):
        """Agentes deben poder cargar la vista del generador (200 OK)."""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.agente_user.id_usuario)
            sess['_fresh'] = True

        res = self.client.get('/itinerarios/generar')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Generaci\xc3\xb3n de Itinerarios', res.data)
        self.assertIn(b'Par\xc3\xa1metros de Entrada', res.data)

    def test_get_generar_rol_admin_permitido(self):
        """Administradores deben poder cargar la vista del generador (200 OK)."""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.admin_user.id_usuario)
            sess['_fresh'] = True

        res = self.client.get('/itinerarios/generar')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Generaci\xc3\xb3n de Itinerarios', res.data)
        self.assertIn(b'chartPareto', res.data)

    def test_post_generar_validaciones_fallidas(self):
        """Validar respuestas de error 400 ante payloads inválidos."""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.admin_user.id_usuario)
            sess['_fresh'] = True

        # 1. Payload vacío o no JSON
        res = self.client.post('/itinerarios/generar', data='not json')
        self.assertEqual(res.status_code, 400)

        # 2. Menos de 2 atractivos
        res = self.client.post('/itinerarios/generar', json={
            'atractivos_ids': [1],
            'transporte_ids': [7],
            'presupuesto_max': 100,
            'tiempo_disponible_horas': 5
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("al menos 2 atractivos", res.get_json()['error'])

        # 3. Sin transportes
        res = self.client.post('/itinerarios/generar', json={
            'atractivos_ids': [13, 14],
            'transporte_ids': [],
            'presupuesto_max': 100,
            'tiempo_disponible_horas': 5
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("medio de transporte", res.get_json()['error'])

    def test_post_generar_ejecucion_exitosa(self):
        """Verifica la ejecución exitosa de NSGA-II mediante POST con datos reales de la BD."""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.admin_user.id_usuario)
            sess['_fresh'] = True

        atractivos = Atractivo.query.filter_by(deleted_at=None).limit(4).all()
        atractivos_ids = [a.id_atractivo for a in atractivos]

        transportes = Transporte.query.filter_by(deleted_at=None).all()
        transporte_ids = [t.id_transporte for t in transportes]

        payload = {
            'atractivos_ids': atractivos_ids,
            'transporte_ids': transporte_ids,
            'presupuesto_max': 300.0,
            'tiempo_disponible_horas': 8.0,
            'intereses': {'Cultural': 0.85, 'Naturaleza': 0.5, 'Urbano': 0.6},
            'tamano_poblacion': 30,
            'generaciones': 15,
            'prob_cruce': 0.9,
            'prob_mutacion': 0.1
        }

        res = self.client.post('/itinerarios/generar', json=payload)
        self.assertEqual(res.status_code, 200)

        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('soluciones', data['data'])
        self.assertIn('frente_pareto', data['data'])
        self.assertIn('historial_convergencia', data['data'])
        self.assertIn('historial_diversidad', data['data'])
        self.assertGreater(len(data['data']['soluciones']), 0)


if __name__ == '__main__':
    unittest.main()
