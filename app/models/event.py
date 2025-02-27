# app/models/event.py

from app.extensions import db

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    # Fügen Sie hier weitere benötigte Felder hinzu
