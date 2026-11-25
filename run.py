import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    ENABLE_SSL = False

    base_dir = os.path.dirname(os.path.abspath(__file__))
    cert_path = os.path.join(base_dir, 'certs', 'localhost.pem')
    key_path = os.path.join(base_dir, 'certs', 'localhost-key.pem')

    if ENABLE_SSL and os.path.exists(cert_path) and os.path.exists(key_path):
        print(f"\n🔒 [SSL/TLS ACTIVO] Servidor seguro disponible en: https://127.0.0.1:5000")
        print(f"   Certificados cargados desde: certs/localhost.pem\n")
        app.run(debug=True, host='127.0.0.1', port=5000, threaded=True, ssl_context=(cert_path, key_path))
    else:
        print(f"\n🌐 [HTTP ESTÁNDAR] Servidor de desarrollo disponible en: http://127.0.0.1:5000")
        if os.path.exists(cert_path) and os.path.exists(key_path):
            print(f"   ℹ️  Certificados SSL preservados en 'certs/'. (Para activar HTTPS: cambiar ENABLE_SSL = True en run.py)\n")
        app.run(debug=True, host='127.0.0.1', port=5000, threaded=True)
