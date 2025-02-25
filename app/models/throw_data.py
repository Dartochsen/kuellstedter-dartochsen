from app.extensions import db
from datetime import datetime

class ThrowData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    angle = db.Column(db.Float, nullable=False)
    velocity = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    game_type = db.Column(db.String(50), nullable=True)
    target_segment = db.Column(db.String(20), nullable=True)

    player = db.relationship('Player', backref=db.backref('throws', lazy='dynamic'))

    def __repr__(self):
        return f'<ThrowData {self.id} for Player {self.player_id}>'
