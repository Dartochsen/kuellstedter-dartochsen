import os
import pymysql
pymysql.install_as_MySQLdb()
from flask import Flask, jsonify, render_template, request, g
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from celery import Celery
from config import config
from .extensions import init_extensions, socketio, db
from app.models.user import User, Role
from app.models.question import Question
import logging
from logging.handlers import RotatingFileHandler
import werkzeug.exceptions
from dotenv import load_dotenv

# Laden der Umgebungsvariablen aus .env und .flaskenv
load_dotenv()

# Initialisierung von Erweiterungen
login_manager = LoginManager()
migrate = Migrate()
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")

# Konfiguration des Login-Managers
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bitte melden Sie sich an, um diese Seite zu sehen.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def make_celery(app):
    """Initialisiert Celery mit Flask-Kontext."""
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

def configure_logging(app):
    """Konfiguriert das Logging für die Anwendung."""
    os.makedirs('logs', exist_ok=True)
    file_handler = RotatingFileHandler('logs/dartochsen.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Dartochsen startup')

class CustomError(Exception):
    """Benutzerdefinierte Fehlerklasse."""
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code

def register_error_handlers(app):
    """Registriert Fehlerbehandlungsroutinen für die Anwendung."""
    @app.errorhandler(404)
    def not_found_error(error):
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify(error="Not Found", message="The requested resource was not found.", status=404), 404
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        app.logger.error('Server Error: %s', (error))
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify(error="Internal Server Error", message="An unexpected error occurred.", status=500), 500
        return render_template('500.html'), 500

    @app.errorhandler(CustomError)
    def handle_custom_error(error):
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify(error="Custom Error", message=error.message, status=error.status_code), error.status_code
        return render_template('error.html', message=error.message), error.status_code

    @app.errorhandler(werkzeug.exceptions.BadRequest)
    def handle_bad_request(e):
        return jsonify(error="Bad Request", message=str(e), status=400), 400

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        app.logger.error('Unhandled Exception: %s', (e))
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify(error="Unexpected Error", message="An unknown error occurred. Please contact support.", status=500), 500
        return render_template('500.html'), 500

def create_default_roles(app):
    """Erstellt Standardrollen in der Datenbank."""
    with app.app_context():
        default_roles = ['user', 'admin', 'trainer']
        for role_name in default_roles:
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name)
                db.session.add(role)
        db.session.commit()

def create_app(config_name='default'):
    """Erstellt und konfiguriert die Flask-Anwendung."""
    app = Flask(__name__)

    # Laden der Konfigurationen
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Laden zusätzlicher Umgebungsvariablen aus .env-Dateien
    app.config.from_prefixed_env()

    # Setzen der Datenbankverbindungs-URL
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://myuser:mypassword@myuser.mysql.pythonanywhere-services.com/myuser$default'

    # Initialisierung der App-Erweiterungen und Konfigurationen
    configure_logging(app)
    
    init_extensions(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    cache.init_app(app)

    # Initialisierung von Celery und Hinzufügen zur App-Instanz
    celery = make_celery(app)
    app.extensions['celery'] = celery

    with app.app_context():
        # Registrierung der Blueprints
        from app.main import bp as main_bp
        from app.auth import bp as auth_bp
        from app.admin import bp as admin_bp
        from app.api import bp as api_bp
        from app.questions import bp as questions_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(questions_bp, url_prefix='/questions')

        # Erstellen Sie die Standardrollen in der Datenbank
        create_default_roles(app)

    @app.before_request
    def before_request():
        g.app = app

    @app.after_request
    def after_request(response):
        app.logger.info(f"Antwort gesendet: {response.status}")
        return response

    if app.debug:
        for rule in app.url_map.iter_rules():
            app.logger.debug(f"{rule.endpoint}: {rule.rule}")

    # Registrierung von Fehlerhandlern
    register_error_handlers(app)

    # Beispielroute mit Caching für Testzwecke
    @app.route('/test')
    @cache.cached(timeout=300)  # Cache für 5 Minuten aktivieren.
    def test():
        return 'Test Route funktioniert'

    # Debug-Informationen im Template verfügbar machen.
    @app.context_processor
    def inject_debug():
        return dict(debug=app.debug)

    return app
