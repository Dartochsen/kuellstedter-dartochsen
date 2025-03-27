from app.extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Index, func

class Game(db.Model):
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    player1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    start_score = db.Column(db.Integer, default=501)
    player1_score = db.Column(db.Integer)
    player2_score = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    game_type = db.Column(db.String(50), default='501')
    duration = db.Column(db.Integer)  # Duration in seconds

    player1 = relationship('User', foreign_keys=[player1_id], backref='games_as_player1')
    player2 = relationship('User', foreign_keys=[player2_id], backref='games_as_player2')
    winner = relationship('User', foreign_keys=[winner_id], backref='games_won')
    players = relationship('Player', secondary='game_players', back_populates='games')
    throws = relationship('ThrowData', back_populates='game', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_game_players', 'player1_id', 'player2_id'),
        Index('idx_game_date_winner', 'date', 'winner_id'),
        Index('idx_game_type', 'game_type'),
    )

    def __repr__(self):
        return f'<Game {self.id}: {self.player1.username} vs {self.player2.username}>'

    @classmethod
    def get_recent_games(cls, limit=10):
        return cls.query.order_by(cls.date.desc()).limit(limit).all()

    @classmethod
    def get_player_game_stats(cls, player_id):
        return db.session.query(
            func.count(cls.id).label('total_games'),
            func.sum(cls.winner_id == player_id).label('wins'),
            func.avg(func.case([(cls.player1_id == player_id, cls.player1_score),
                                (cls.player2_id == player_id, cls.player2_score)])).label('avg_score')
        ).filter((cls.player1_id == player_id) | (cls.player2_id == player_id)).first()

    def to_dict(self):
        return {
            'id': self.id,
            'player1': self.player1.username,
            'player2': self.player2.username,
            'winner': self.winner.username if self.winner else None,
            'player1_score': self.player1_score,
            'player2_score': self.player2_score,
            'date': self.date.isoformat(),
            'game_type': self.game_type,
            'duration': self.duration
        }

game_players = db.Table('game_players',
    db.Column('game_id', db.Integer, db.ForeignKey('games.id'), primary_key=True),
    db.Column('player_id', db.Integer, db.ForeignKey('players.id'), primary_key=True),
    db.Column('score', db.Integer)
)

Index('idx_game_players_score', game_players.c.game_id, game_players.c.player_id, game_players.c.score)
