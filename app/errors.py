from flask import render_template, Blueprint
from app import db

errors_bp = Blueprint('errors', __name__)

class CustomError(Exception):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code

@errors_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@errors_bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@errors_bp.app_errorhandler(CustomError)
def handle_custom_error(error):
    return render_template('error.html', message=error.message), error.status_code

def register_error_handlers(app):
    app.register_error_handler(404, not_found_error)
    app.register_error_handler(500, internal_error)
    app.register_error_handler(CustomError, handle_custom_error)
