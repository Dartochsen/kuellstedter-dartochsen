import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              f'sqlite:///{os.path.join(basedir, "app.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Firebase Konfiguration
    FIREBASE_CONFIG = {
        "type": "service_account",
        "project_id": os.environ.get('FIREBASE_PROJECT_ID'),
        "private_key_id": os.environ.get('FIREBASE_PRIVATE_KEY_ID'),
        "private_key": os.environ.get('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
        "client_email": os.environ.get('FIREBASE_CLIENT_EMAIL'),
        "client_id": os.environ.get('FIREBASE_CLIENT_ID'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.environ.get('FIREBASE_CLIENT_X509_CERT_URL')
    }
    FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL', 'https://dartochsenapp.firebaseio.com')

    # Logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')

    # HTTPS Konfiguration
    PREFERRED_URL_SCHEME = 'https'
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    # In der Entwicklungsumgebung können wir HTTPS deaktivieren
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # Logging to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    # In der Testumgebung können wir HTTPS deaktivieren
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
