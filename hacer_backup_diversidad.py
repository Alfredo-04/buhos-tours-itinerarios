import os
import subprocess

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def backup():
    pg_dump = r"E:\Program Files (x86)\PostgreSQL\18\bin\pg_dump.exe"
    if not os.path.exists(pg_dump):
        pg_dump = "pg_dump"
    
    backup_file = os.path.join(BASE_DIR, 'backup_pre_diversidad.sql')
    env = os.environ.copy()
    env['PGPASSWORD'] = 'admin123'
    
    with open(backup_file, 'w', encoding='utf-8') as out:
        res = subprocess.run(
            [pg_dump, "-U", "postgres", "-h", "localhost", "-p", "5432", "buhos_tours"],
            env=env,
            stdout=out,
            stderr=subprocess.PIPE,
            text=True
        )
        if res.returncode == 0:
            print(f"[OK] Backup creado: backup_pre_diversidad.sql ({os.path.getsize(backup_file)} bytes)")
        else:
            print(f"[!] Error al crear backup: {res.stderr}")

if __name__ == '__main__':
    backup()
