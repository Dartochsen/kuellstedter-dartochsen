from app import create_app
import logging

app = create_app()

if __name__ == '__main__':
    logging.basicConfig(filename='logs/error.log', level=logging.DEBUG)
    app.run(debug=True, port=5000)

if __name__ == '__main__':
    import pkg_resources
    installed_packages = [pkg.key for pkg in pkg_resources.working_set]
    print('flask' in installed_packages, 'flask-sqlalchemy' in installed_packages)
