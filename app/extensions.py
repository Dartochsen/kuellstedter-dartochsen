from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_sslify import SSLify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_socketio import SocketIO
from celery import Celery

db = SQLAlchemy()
migrate = Migrate()
cache = Cache(config={'CACHE_TYPE': 'simple'})
limiter = Limiter(key_func=get_remote_address)
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()
mail = Mail()
socketio = SocketIO()
celery = Celery(__name__)

def init_sslify(app):
    if not app.debug and not app.testing:
        SSLify(app)

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    socketio.init_app(app)  # Hinzugefügt
    init_sslify(app)

    # Celery Konfiguration
    celery.conf.update(app.config)
