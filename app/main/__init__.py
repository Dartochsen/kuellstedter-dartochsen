from flask import Blueprint

bp = Blueprint('main', __name__)

import logging
logger = logging.getLogger(__name__)
logger.info("Blueprint 'main' wurde erstellt")

from . import routes
print("routes wurden in main/__init__.py importiert")
