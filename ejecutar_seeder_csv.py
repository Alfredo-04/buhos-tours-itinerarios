import os
import sys
import subprocess
import psycopg2

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

def log(msg):
    print(f"\n========================================\n{msg}\n========================================")

def backup():
    log("1. Generando Backup: backup_pre_seed.sql...")
    pg_dump = r"E:\Program Files (x86)\PostgreSQL\18\bin\pg_dump.exe"
    if not os.path.exists(pg_dump):
        pg_dump = "pg_dump"
    
    backup_file = os.path.join(BASE_DIR, 'backup_pre_seed.sql')
    env = os.environ.copy()
    env['PGPASSWORD'] = 'admin123'
    
    try:
        with open(backup_file, 'w', encoding='utf-8') as out:
            res = subprocess.run(
                [pg_dump, "-U", "postgres", "-h", "localhost", "-p", "5432", "buhos_tours"],
                env=env,
                stdout=out,
                stderr=subprocess.PIPE,
                text=True
            )
            if res.returncode == 0:
                print(f" [OK] Backup creado: backup_pre_seed.sql ({os.path.getsize(backup_file)} bytes)")
            else:
                print(f" [!] Advertencia al crear backup: {res.stderr}")
    except Exception as e:
        print(f" [!] Error en backup: {e}")

def run_seeder():
    log("2. Ejecutando Seeder desde CSV...")
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.seeds.catalogo_seeder import seed_catalogo
        seed_catalogo()

def verify():
    log("3. Verificación de Tablas en la Base de Datos...")
    conn = psycopg2.connect('postgresql://postgres:admin123@localhost:5432/buhos_tours')
    cur = conn.cursor()

    tablas_dataset = [
        'categoria', 'subcategoria', 'proveedor', 'transporte',
        'atractivo', 'zona_trafico', 'patron_trafico'
    ]
    tablas_seguridad = ['rol', 'usuario']
    tablas_operativas = [
        'turista', 'generacion', 'itinerario', 'itinerario_detalle',
        'viaje_turista', 'itinerario_detalle_trafico', 'tipo_cambio', 'consulta_nsga2'
    ]

    print("\n--- TABLAS DATASET (SEEDEADAS) ---")
    for t in tablas_dataset:
        cur.execute(f'SELECT COUNT(*) FROM "{t}";')
        cnt = cur.fetchone()[0]
        print(f"  [CSV] {t:<26}: {cnt} registros")

    print("\n--- TABLAS SEGURIDAD ---")
    for t in tablas_seguridad:
        cur.execute(f'SELECT COUNT(*) FROM "{t}";')
        cnt = cur.fetchone()[0]
        print(f"  [SEG] {t:<26}: {cnt} registros")

    print("\n--- TABLAS OPERATIVAS (DEBEN ESTAR VACÍAS) ---")
    for t in tablas_operativas:
        cur.execute(f'SELECT COUNT(*) FROM "{t}";')
        cnt = cur.fetchone()[0]
        status = "VACÍA (OK)" if cnt == 0 else f"ATENCIÓN: {cnt} registros"
        print(f"  [OPE] {t:<26}: {cnt} registros -> {status}")

    cur.close()
    conn.close()

if __name__ == '__main__':
    backup()
    run_seeder()
    verify()
    print("\n[PROCESO FINALIZADO EXITOSAMENTE]")
