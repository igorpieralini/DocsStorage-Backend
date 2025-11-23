class Config:
    SECRET_KEY = "sua_chave_secreta"
    SQLALCHEMY_DATABASE_URI = "sqlite:///db.sqlite3"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "sua_chave_jwt"
