from app.extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Index

class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)

    author = relationship('User', back_populates='posts')

    __table_args__ = (
        Index('idx_post_title', 'title'),
        Index('idx_post_created_at', 'created_at'),
        Index('idx_post_is_published', 'is_published'),
    )

    def __repr__(self):
        return f'<Post "{self.title}">'

    @classmethod
    def get_recent_posts(cls, limit=5):
        return cls.query.filter_by(is_published=True).order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_posts_by_author(cls, author_id, include_unpublished=False):
        query = cls.query.filter_by(author_id=author_id)
        if not include_unpublished:
            query = query.filter_by(is_published=True)
        return query.order_by(cls.created_at.desc()).all()

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author_id': self.author_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_published': self.is_published
        }
