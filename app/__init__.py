import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from logging.config import dictConfig
import firebase_admin
from firebase_admin import credentials
from config import Config

# Initialisierung der Erweiterungen
db = SQLAlchemy()
migrate = Migrate()

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

def initialize_firebase(app):
    if not firebase_admin._apps:
        try:
            private_key = os.environ.get('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n')
            if not private_key:
                raise ValueError("FIREBASE_PRIVATE_KEY is not set")

            firebase_config = app.config['FIREBASE_CONFIG']
            firebase_config['private_key'] = private_key

            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred, {
                'databaseURL': os.environ.get('FIREBASE_DATABASE_URL', 'https://dartochsenapp.firebaseio.com')
            })
        except Exception as e:
            app.logger.error(f"Failed to initialize Firebase: {str(e)}")

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(config_class)

    # Konfiguriere Logging
    configure_logging()

    # Initialisiere Datenbank
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialisiere Firebase
    initialize_firebase(app)

    # Registriere Blueprints
    from app.main import bp as main_bp
    app.logger.info(f"Versuche, Blueprint zu registrieren: {main_bp.name}")
    app.register_blueprint(main_bp)
    app.logger.info(f"Blueprint {main_bp.name} erfolgreich registriert")
    app.logger.info(f"Registrierte Routen: {[str(rule) for rule in app.url_map.iter_rules()]}")
    app.logger.info(f"Alle Routen des main Blueprints: {[rule for rule in app.url_map.iter_rules() if rule.endpoint.startswith('main.')]}")

    @app.route('/test')
    def test_route():
        return "Test-Route funktioniert!"

    # Fehlerbehandlung
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f"404 error: {str(error)}")
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"500 error: {str(error)}", exc_info=True)
        return render_template('500.html'), 500

    app.logger.info('Dartochsen startup')

    return app

# Importiere Modelle
from app import models
