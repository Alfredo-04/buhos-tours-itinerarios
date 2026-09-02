import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'mi_clave_super_secreta_123')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:admin123@localhost:5432/buhos_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
