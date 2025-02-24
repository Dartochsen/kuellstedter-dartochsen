import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import logging
from logging.handlers import RotatingFileHandler
import firebase_admin
from firebase_admin import credentials

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Konfiguration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///dartochsen.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Firebase Initialisierung
    firebase_config = {
        "apiKey": os.environ.get("FIREBASE_API_KEY"),
        "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
        "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.environ.get("FIREBASE_APP_ID")
    }
    
    firebase_service_account = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT_KEY', '{}'))
    if 'type' not in firebase_service_account:
        firebase_service_account['type'] = 'service_account'
    
    try:
        cred = credentials.Certificate(firebase_service_account)
        firebase_admin.initialize_app(cred, firebase_config)
    except Exception as e:
        app.logger.error(f"Failed to initialize Firebase: {str(e)}")

    # Initialisierung der Erweiterungen
    db.init_app(app)

    # Logging-Konfiguration
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/dartochsen.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Dartochsen startup')
    app.logger.info(f"Firebase app config: {firebase_config}")
    # Entfernen Sie sensible Informationen aus den Logs
    safe_firebase_service_account = {k: v for k, v in firebase_service_account.items() if k != 'private_key'}
    app.logger.info(f"Firebase credentials config: {safe_firebase_service_account}")

    # Fehlerbehandlung
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"500 error: {str(error)}", exc_info=True)
        return render_template('500.html'), 500

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f"404 error: {str(error)}", exc_info=True)
        return render_template('404.html'), 404

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        return render_template('500.html'), 500

    @app.route('/test')
    def test():
        return "Test route works!"

    @app.route('/')
    def home():
        return "Willkommen auf der Startseite"

    # Blueprints registrieren
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app

# Importieren Sie Ihre Modelle hier
from app import models
