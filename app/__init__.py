from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import logging
from logging.handlers import RotatingFileHandler
import os
import firebase_admin
from firebase_admin import credentials
from instance.config.firebase_config import config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Konfiguration
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dartochsen.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Firebase Initialisierung
    cred = credentials.Certificate("instance/config/serviceAccountKey.json")
    firebase_admin.initialize_app(cred, config)

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
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        return render_template('500.html'), 500

    @app.route('/test')
    def test():
        return "Test route works!"

    # Neue direkte Route für die Startseite
    @app.route('/')
    def home():
        return "Willkommen auf der Startseite"

    # Blueprints registrieren
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Weitere Blueprints hier registrieren
    
    return app

# Importieren Sie Ihre Modelle hier
from app import models
