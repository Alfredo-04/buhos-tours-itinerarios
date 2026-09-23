import os
import sys

# Agregar la raíz del proyecto al sys.path para ejecución directa
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import db
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.seeds.rol_seeder import seed_roles

SEED_USERS = [
    {
        "nombres": "Administrador",
        "apellidos": "Sistema",
        "email": "admin@buhostours.com",
        "password": "Admin123!Secure",
        "rol": "admin"
    }
]

def seed_usuarios():
    """
    Inserta o actualiza el usuario Administrador maestro inicial
    garantizando idempotencia y asignación de FK a la tabla Rol.
    """
    seed_roles()

    creados = 0
    actualizados = 0

    roles_map = {r.nombre: r for r in Rol.query.all()}

    for user_data in SEED_USERS:
        rol_obj = roles_map.get(user_data["rol"])
        if not rol_obj:
            print(f" [!] Error: Rol {user_data['rol']} no encontrado.")
            continue

        usuario = Usuario.query.filter_by(email=user_data["email"]).first()
        if not usuario:
            nuevo_usuario = Usuario(
                nombres=user_data["nombres"],
                apellidos=user_data["apellidos"],
                email=user_data["email"],
                id_rol=rol_obj.id_rol
            )
            nuevo_usuario.set_password(user_data["password"])
            db.session.add(nuevo_usuario)
            creados += 1
            print(f" [+] Creado {user_data['rol'].upper()}: {user_data['email']}")
        else:
            # Asegurar rol y sincronizar contraseña si es necesario
            usuario.nombres = user_data["nombres"]
            usuario.apellidos = user_data["apellidos"]
            usuario.id_rol = rol_obj.id_rol
            usuario.set_password(user_data["password"])
            actualizados += 1
            print(f" [~] Actualizado {user_data['rol'].upper()}: {user_data['email']}")

    db.session.commit()
    print(f"\n[OK] Proceso de Seeder finalizado: {creados} creados, {actualizados} actualizados.")
    return creados, actualizados

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_usuarios()
