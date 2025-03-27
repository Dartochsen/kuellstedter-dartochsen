from flask import Blueprint

bp = Blueprint('questions', __name__)

from . import routes
