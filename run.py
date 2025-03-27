import os
import logging
from importlib.metadata import distributions
from app import create_app
from app.extensions import socketio

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    # Konfiguriere Logging
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(os.path.join(log_dir, 'error.log'))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.DEBUG)

    # Überprüfe installierte Pakete
    installed_packages = {dist.metadata['Name'].lower() for dist in distributions()}
    required_packages = {'flask', 'flask-sqlalchemy', 'flask-socketio'}
    for package in required_packages:
        app.logger.info(f'{package} installiert: {package in installed_packages}')

    # Konfiguriere Debug-Modus und Port
    debug = app.config.get('DEBUG', False)
    port = int(os.environ.get('PORT', 5000))

    # Starte die Anwendung mit SocketIO
    if debug:
        app.logger.warning("Debug-Modus ist aktiviert. Deaktivieren Sie ihn für die Produktion.")
    socketio.run(app, debug=debug, host='0.0.0.0', port=port)
