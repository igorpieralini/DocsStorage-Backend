import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env localizado na pasta 'backend' para facilitar desenvolvimento local
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(env_path)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:Igorpro2020%23%40%23@localhost:3306/docsstorage"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-key-change-in-production")
    
    STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "C:/Users/igorp/Documents/Storage"))
    MAX_STORAGE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB total (todos os usuários)
    MAX_USER_STORAGE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB por usuário
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB por arquivo
