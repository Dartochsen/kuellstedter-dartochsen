from flask import Blueprint

bp = Blueprint('main', __name__)

from . import routes, match_routes, stage_routes, team_routes, tournament_entry_routes, tournament_routes

# Hinweis:
# Die Registrierung der anderen Blueprints (z.B. tournament_routes, stage_routes usw.)
# erfolgt in der Datei `app/__init__.py`, um eine zentrale Verwaltung zu gewährleisten.