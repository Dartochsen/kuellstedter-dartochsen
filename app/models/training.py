from app.extensions import db
from datetime import datetime

class Training(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(200))
    # Fügen Sie hier weitere benötigte Felder hinzu

    def __repr__(self):
        return f'<Training {self.id}>'
