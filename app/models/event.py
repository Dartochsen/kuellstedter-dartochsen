from app.extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Index

class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(120))
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    max_participants = db.Column(db.Integer)
    current_participants = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organizer = relationship('User', back_populates='organized_events')
    participants = relationship('User', secondary='event_participants', back_populates='participated_events')

    __table_args__ = (
        Index('idx_event_date', 'date'),
        Index('idx_event_organizer', 'organizer_id'),
    )

    def __repr__(self):
        return f'<Event {self.name}>'

    def is_full(self):
        return self.current_participants >= self.max_participants

    @classmethod
    def get_upcoming_events(cls, limit=10):
        return cls.query.filter(cls.date > datetime.utcnow()).order_by(cls.date).limit(limit).all()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'date': self.date.isoformat(),
            'description': self.description,
            'location': self.location,
            'organizer': self.organizer.username,
            'max_participants': self.max_participants,
            'current_participants': self.current_participants,
            'is_full': self.is_full()
        }

event_participants = db.Table('event_participants',
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

Index('idx_event_participants', event_participants.c.event_id, event_participants.c.user_id)
