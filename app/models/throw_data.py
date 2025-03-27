from app.extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Index, func

class ThrowData(db.Model):
    __tablename__ = 'throw_data'

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)
    angle = db.Column(db.Float, nullable=False)
    velocity = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    game_type = db.Column(db.String(50), nullable=True)
    target_segment = db.Column(db.String(20), nullable=True)

    player = relationship('Player', back_populates='throws')
    game = relationship('Game', back_populates='throws')

    __table_args__ = (
        Index('idx_throw_data_player_game', 'player_id', 'game_id'),
        Index('idx_throw_data_timestamp', 'timestamp'),
    )

    def __repr__(self):
        return f'<ThrowData {self.id} for Player {self.player_id}>'

    @classmethod
    def get_player_average_stats(cls, player_id):
        return db.session.query(
            func.avg(cls.angle).label('avg_angle'),
            func.avg(cls.velocity).label('avg_velocity'),
            func.avg(cls.accuracy).label('avg_accuracy'),
            func.avg(cls.score).label('avg_score')
        ).filter_by(player_id=player_id).first()

    @classmethod
    def get_recent_throws(cls, player_id, limit=10):
        return cls.query.filter_by(player_id=player_id).order_by(cls.timestamp.desc()).limit(limit).all()
