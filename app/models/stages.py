from app.extensions import db
from datetime import datetime

class Stage(db.Model):
    __tablename__ = 'stages'

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # e.g., 'Group Stage', 'Quarter Finals', 'Semi Finals', 'Final'
    order = db.Column(db.Integer, nullable=False)  # To maintain the order of stages
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # 'Pending', 'In Progress', 'Completed'

    tournament = db.relationship('Tournament', back_populates='stages')
    matches = db.relationship('Match', back_populates='stage', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Stage {self.name} of Tournament {self.tournament_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'tournament_id': self.tournament_id,
            'name': self.name,
            'order': self.order,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'status': self.status
        }
