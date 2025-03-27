from app.extensions import db
from datetime import datetime

class Activity(db.Model):
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(128), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='activities')

    def __repr__(self):
        return f'<Activity {self.action}>'
