import os
from dotenv import load_dotenv

load_dotenv()  # Carga las variables del archivo .env

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-buhos-tours-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:admin123@localhost:5432/buhos_tours'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # === FLASK-MAIL ===
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'alfredocortez12god@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'qwxd mnql fpjm tzrk')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME', 'alfredocortez12god@gmail.com'))
    MAIL_DEBUG = False
    MAIL_SUPPRESS_SEND = False  # Poner True para tests y no enviar correos reales
