from app.extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Index

class ForumThema(db.Model):
    __tablename__ = 'forum_themen'

    id = db.Column(db.Integer, primary_key=True)
    titel = db.Column(db.String(100), nullable=False)
    inhalt = db.Column(db.Text, nullable=False)
    erstellungsdatum = db.Column(db.DateTime, default=datetime.utcnow)
    autor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    autor = relationship('User', back_populates='forum_themen')
    antworten = relationship('ForumAntwort', back_populates='thema', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_forum_thema_titel', 'titel'),
        Index('idx_forum_thema_erstellungsdatum', 'erstellungsdatum'),
    )

    def __repr__(self):
        return f'<ForumThema "{self.titel}">'

    @classmethod
    def get_recent_themes(cls, limit=10):
        return cls.query.order_by(cls.erstellungsdatum.desc()).limit(limit).all()

    def to_dict(self):
        return {
            'id': self.id,
            'titel': self.titel,
            'inhalt': self.inhalt,
            'erstellungsdatum': self.erstellungsdatum.isoformat(),
            'autor': self.autor.username,
            'antworten_count': self.antworten.count()
        }

class ForumAntwort(db.Model):
    __tablename__ = 'forum_antworten'

    id = db.Column(db.Integer, primary_key=True)
    inhalt = db.Column(db.Text, nullable=False)
    erstellungsdatum = db.Column(db.DateTime, default=datetime.utcnow)
    autor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    thema_id = db.Column(db.Integer, db.ForeignKey('forum_themen.id'), nullable=False)

    autor = relationship('User', back_populates='forum_antworten')
    thema = relationship('ForumThema', back_populates='antworten')

    __table_args__ = (
        Index('idx_forum_antwort_erstellungsdatum', 'erstellungsdatum'),
        Index('idx_forum_antwort_thema', 'thema_id'),
    )

    def __repr__(self):
        return f'<ForumAntwort {self.id}>'

    @classmethod
    def get_recent_answers(cls, thema_id, limit=20):
        return cls.query.filter_by(thema_id=thema_id).order_by(cls.erstellungsdatum.desc()).limit(limit).all()

    def to_dict(self):
        return {
            'id': self.id,
            'inhalt': self.inhalt,
            'erstellungsdatum': self.erstellungsdatum.isoformat(),
            'autor': self.autor.username,
            'thema_id': self.thema_id
        }
