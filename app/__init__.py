# app/__init__.py
from flask import Flask
from .config import Config
from .extensions import db, migrate, jwt, cors
from .routes.auth_routes import auth_bp
from .routes.file_routes import file_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(file_bp, url_prefix="/api/files")

    @app.route("/")
    def index():
        return {"msg": "DocsStorage backend running."}

    return app
