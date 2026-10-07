from app import create_app, db
from app.models.distancia_atractivo import DistanciaAtractivo

app = create_app()

with app.app_context():
    # Crear la tabla distancia_atractivo si no existe
    db.create_all()
    print("[OK] Tabla 'distancia_atractivo' creada o verificada exitosamente en la base de datos.")
