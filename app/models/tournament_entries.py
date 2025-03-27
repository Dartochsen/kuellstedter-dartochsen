from app.extensions import db
from datetime import datetime

class TournamentEntry(db.Model):
    __tablename__ = 'tournament_entries'

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)  # For team tournaments
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')  # 'Pending', 'Approved', 'Rejected'

    tournament = db.relationship('Tournament', back_populates='entries')
    player = db.relationship('User', backref='tournament_entries')
    team = db.relationship('Team', backref='entries')

    def __repr__(self):
        return f'<TournamentEntry {self.player.username} for Tournament {self.tournament_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'tournament_id': self.tournament_id,
            'player': self.player.username,
            'team': self.team.name if self.team else None,
            'registration_date': self.registration_date.isoformat(),
            'status': self.status
        }
