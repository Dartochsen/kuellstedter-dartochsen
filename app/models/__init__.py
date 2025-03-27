from app.extensions import db
from .user import User, Role
from .player import Player
from .game import Game, game_players
from .throw_data import ThrowData
from .event import Event, event_participants
from .forum import ForumThema, ForumAntwort
from .post import Post
from .tournament import Tournament
from .stages import Stage
from .teams import Team
from .tournament_entries import TournamentEntry
from .matches import Match
from .activity import Activity
from .training import Training

__all__ = [
    'db',
    'User',
    'Role',
    'Player',
    'Game',
    'game_players',
    'ThrowData',
    'Event',
    'event_participants',
    'ForumThema',
    'ForumAntwort',
    'Post',
    'Tournament',
    'Stage',
    'Team',
    'TournamentEntry',
    'Match',
    'Activity',
    'Training'
]

def init_app(app):
    # Hier können Sie zusätzliche Initialisierungen für die Modelle durchführen, falls nötig
    pass
