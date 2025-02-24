from app import create_app
import logging
import os

app = create_app()

if __name__ == '__main__':
    # Konfiguriere Logging
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logging.basicConfig(
        filename=os.path.join(log_dir, 'error.log'),
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )

    # Überprüfe installierte Pakete
    import pkg_resources
    installed_packages = [pkg.key for pkg in pkg_resources.working_set]
    print('Flask installiert:', 'flask' in installed_packages)
    print('Flask-SQLAlchemy installiert:', 'flask-sqlalchemy' in installed_packages)

    # Starte die Anwendung
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
