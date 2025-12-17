from flask import Flask
from .config import Config
from .extensions import db, jwt, cors
from .routes.auth_routes import auth_bp
from .routes.file_routes import file_bp
from .routes.google_drive_routes import google_drive_bp
from .services.storage_service import StorageService

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, origins=["http://localhost:4200"])

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(file_bp, url_prefix="/api/files")
    app.register_blueprint(google_drive_bp)

    @app.route("/")
    def index():
        return {"status": "ok", "message": "DocsStorage API"}
    
    # Inicializa o storage ao iniciar a aplicação (cria pastas para todos os usuários)
    with app.app_context():
        StorageService.initialize_storage()

    return app
