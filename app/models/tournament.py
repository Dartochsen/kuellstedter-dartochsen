from app.extensions import db
from datetime import datetime

class Tournament(db.Model):
    __tablename__ = 'tournaments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(120), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    phase = db.Column(db.String(50), default='Registration')
    format = db.Column(db.String(50), nullable=False)  # e.g., '1vs1' or 'team-based'
    type = db.Column(db.String(50), nullable=False)  # e.g., 'tournament', 'league', 'ladder'

    organizer = db.relationship('User', back_populates='organized_tournaments')
    stages = db.relationship('Stage', back_populates='tournament', cascade='all, delete-orphan')
    teams = db.relationship('Team', back_populates='tournament', cascade='all, delete-orphan')
    entries = db.relationship('TournamentEntry', back_populates='tournament', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Tournament {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'date': self.date.isoformat(),
            'location': self.location,
            'organizer': self.organizer.username,
            'phase': self.phase,
            'format': self.format,
            'type': self.type
        }
