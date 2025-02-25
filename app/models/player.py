from app.extensions import db
from datetime import datetime

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    average_score = db.Column(db.Float, default=0.0)
    games_played = db.Column(db.Integer, default=0)
    training_hours = db.Column(db.Float, default=0.0)
    highest_score = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Player {self.name}>'
