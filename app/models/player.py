from app.extensions import db
from datetime import datetime

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    average_score = db.Column(db.Float, nullable=False)
    games_played = db.Column(db.Integer, nullable=False)
    training_hours = db.Column(db.Float, nullable=False)

class ThrowData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    angle = db.Column(db.Float, nullable=False)
    velocity = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    player = db.relationship('Player', backref=db.backref('throws', lazy=True))
