import os
import sys

# Agregar la raíz del proyecto al sys.path para ejecución directa
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import db
from app.models.rol import Rol

ROLES_INICIALES = ['admin', 'agente', 'turista']

def seed_roles():
    """
    Inserta los roles básicos (admin, agente, turista) garantizando idempotencia.
    """
    creados = 0
    existentes = 0

    for rol_nombre in ROLES_INICIALES:
        rol = Rol.query.filter_by(nombre=rol_nombre).first()
        if not rol:
            nuevo_rol = Rol(nombre=rol_nombre)
            db.session.add(nuevo_rol)
            creados += 1
            print(f" [+] Rol creado: {rol_nombre}")
        else:
            existentes += 1
            print(f" [~] Rol ya existe: {rol_nombre}")

    db.session.commit()
    print(f"\n[OK] Seeder de roles finalizado: {creados} creados, {existentes} existentes.")
    return creados, existentes

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_roles()
