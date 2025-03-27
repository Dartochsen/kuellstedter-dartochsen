from app.extensions import db

class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    captain_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    tournament = db.relationship('Tournament', back_populates='teams')
    captain = db.relationship('User', backref='captained_teams')
    members = db.relationship('User', secondary='team_members', backref='teams')

    def __repr__(self):
        return f'<Team {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'tournament_id': self.tournament_id,
            'captain': self.captain.username,
            'members': [member.username for member in self.members]
        }

team_members = db.Table('team_members',
    db.Column('team_id', db.Integer, db.ForeignKey('teams.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)
