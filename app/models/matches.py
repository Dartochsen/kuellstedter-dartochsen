from app.extensions import db
from datetime import datetime

class Match(db.Model):
    __tablename__ = 'matches'

    id = db.Column(db.Integer, primary_key=True)
    stage_id = db.Column(db.Integer, db.ForeignKey('stages.id'), nullable=False)
    player1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='Scheduled')  # 'Scheduled', 'In Progress', 'Completed'

    stage = db.relationship('Stage', back_populates='matches')
    player1 = db.relationship('User', foreign_keys=[player1_id])
    player2 = db.relationship('User', foreign_keys=[player2_id])
    winner = db.relationship('User', foreign_keys=[winner_id])

    def __repr__(self):
        return f'<Match {self.player1.username} vs {self.player2.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'stage_id': self.stage_id,
            'player1': self.player1.username,
            'player2': self.player2.username,
            'winner': self.winner.username if self.winner else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status
        }
