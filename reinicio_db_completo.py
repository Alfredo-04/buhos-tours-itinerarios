import os
import sys
import shutil
import subprocess
import psycopg2

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

VENV_PYTHON = os.path.join(BASE_DIR, 'venv', 'Scripts', 'python.exe')
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = sys.executable

def log(msg):
    print(f"\n========================================\n{msg}\n========================================")

def step1_reset_schema():
    log("PASO 1.2: Limpiando esquema en PostgreSQL...")
    conn = psycopg2.connect('postgresql://postgres:admin123@localhost:5432/buhos_tours')
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("""
        DROP SCHEMA public CASCADE;
        CREATE SCHEMA public;
        GRANT ALL ON SCHEMA public TO postgres;
        GRANT ALL ON SCHEMA public TO public;
    """)
    cur.close()
    conn.close()
    print(" [OK] Schema public recreado desde cero con éxito.")

def step2_clean_migrations_and_catalogo_seeder():
    log("PASO 1.3 & 2: Eliminando migraciones y catalogo_seeder.py...")
    migrations_dir = os.path.join(BASE_DIR, 'migrations')
    if os.path.exists(migrations_dir):
        shutil.rmtree(migrations_dir, ignore_errors=True)
        print(" [OK] Directorio migrations eliminado.")
    
    catalogo_seeder = os.path.join(BASE_DIR, 'app', 'seeds', 'catalogo_seeder.py')
    if os.path.exists(catalogo_seeder):
        os.remove(catalogo_seeder)
        print(" [OK] catalogo_seeder.py eliminado.")
    else:
        print(" [~] catalogo_seeder.py ya no existe.")

    reset_temp = os.path.join(BASE_DIR, 'reset_schema.py')
    if os.path.exists(reset_temp):
        os.remove(reset_temp)

def run_flask_cmd(args, phase=None):
    env = os.environ.copy()
    if phase:
        env['MIGRATION_PHASE'] = str(phase)
    cmd = [VENV_PYTHON, '-m', 'flask'] + args
    print(f" -> Ejecutando: {' '.join(cmd)}" + (f" (MIGRATION_PHASE={phase})" if phase else ""))
    result = subprocess.run(cmd, cwd=BASE_DIR, env=env, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if result.returncode != 0:
        raise RuntimeError(f"Error al ejecutar: {' '.join(cmd)}\n{result.stderr}")

def step3_run_phased_migrations():
    log("PASO 1.4: Inicializando Flask-Migrate...")
    run_flask_cmd(['db', 'init'])

    phases = [
        (1, "Fase 1: ROL, CATEGORIA, PROVEEDOR, ZONA_TRAFICO"),
        (2, "Fase 2: USUARIO, SUBCATEGORIA, PATRON_TRAFICO, TRANSPORTE"),
        (3, "Fase 3: TURISTA, ATRACTIVO"),
        (4, "Fase 4: GENERACION, TIPO_CAMBIO, CONSULTA_NSGA2"),
        (5, "Fase 5: ITINERARIO, VIAJE_TURISTA"),
        (6, "Fase 6: ITINERARIO_DETALLE"),
        (7, "Fase 7: ITINERARIO_DETALLE_TRAFICO"),
    ]

    for phase_num, msg in phases:
        log(f"PASO 4: {msg}")
        run_flask_cmd(['db', 'migrate', '-m', msg], phase=phase_num)
        run_flask_cmd(['db', 'upgrade'], phase=phase_num)
        print(f" [OK] {msg} aplicada correctamente.")

def step4_run_seeders():
    log("PASO 5: Ejecutando seeders existentes (rol_seeder y user_seeder)...")
    # Ejecutar exactamente con el contexto de la aplicación
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.seeds.rol_seeder import seed_roles
        from app.seeds.user_seeder import seed_usuarios
        print("Ejecutando seed_roles()...")
        seed_roles()
        print("Ejecutando seed_usuarios()...")
        seed_usuarios()

def step5_verify():
    log("VERIFICACIÓN FINAL DE LA BASE DE DATOS...")
    conn = psycopg2.connect('postgresql://postgres:admin123@localhost:5432/buhos_tours')
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cur.fetchall()]
    print(f"Total tablas encontradas en public: {len(tables)}")
    for t in tables:
        cur.execute(f'SELECT COUNT(*) FROM "{t}";')
        count = cur.fetchone()[0]
        print(f"  - {t:<28}: {count} filas")
    cur.close()
    conn.close()

if __name__ == '__main__':
    step1_reset_schema()
    step2_clean_migrations_and_catalogo_seeder()
    step3_run_phased_migrations()
    step4_run_seeders()
    step5_verify()
    print("\n[ÉXITO TOTAL] El nuevo esquema de 17 tablas y los seeders han sido aplicados.")
