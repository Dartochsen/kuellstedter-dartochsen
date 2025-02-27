import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_sslify import SSLify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from logging.config import dictConfig
import firebase_admin
from firebase_admin import credentials
from config import Config
from .extensions import db, bcrypt
from .firebase_manager import initialize_event_structure, initialize_firebase

# Initialisierung der Erweiterungen
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379",
    storage_options={"socket_connect_timeout": 30},
    strategy="fixed-window"
)

def configure_logging():
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }},
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/dartochsen.log',
                'maxBytes': 10240,
                'backupCount': 10,
                'formatter': 'default'
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi', 'file']
        }
    })

def print_routes(app):
    print("Alle registrierten Routen:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(config_class)
    
    configure_logging()
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)

    # Initialisiere Flask-SSLify nur in der Produktionsumgebung
    if not app.debug and not app.testing:
        SSLify(app)

    initialize_firebase(app)

    # Registriere Blueprints
    from app.main import bp as main_bp
    from app.admin import bp as admin_bp
    from app.api import bp as api_bp
    from app.auth import bp as auth_bp
    from app.errors import errors_bp, register_error_handlers

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(errors_bp)
    
    # Registriere Fehlerbehandler
    register_error_handlers(app)

    # Konfiguriere Login-Manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Bitte melden Sie sich an, um auf diese Seite zuzugreifen.'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    # Event_Struktur initialisieren
    with app.app_context():
        initialize_event_structure()

    # Debug-Routen
    @app.route('/test')
    def test_route():
        return "Test-Route funktioniert!"

    # Debug-Ausgabe der registrierten Routen
    with app.app_context():
        print_routes(app)

    app.logger.info('Dartochsen startup')

    return app

# Importiere Modelle
from app import models