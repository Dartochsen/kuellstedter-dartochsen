from app.extensions import db, cache
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Index, func

class Player(db.Model):
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    name = db.Column(db.String(64), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    average_score = db.Column(db.Float, default=0.0)
    games_played = db.Column(db.Integer, default=0)
    training_hours = db.Column(db.Float, default=0.0)
    highest_score = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    checkout_percentage = db.Column(db.Float, default=0.0)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    highest_checkout = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='player_profile')
    games = relationship('Game', secondary='game_players', back_populates='players')
    throws = relationship('ThrowData', back_populates='player', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_player_name', 'name'),
        Index('idx_player_stats', 'average_score', 'games_played', 'wins'),
        Index('idx_player_active', 'active'),
    )

    def __repr__(self):
        return f'<Player {self.name}>'

    def update_stats(self, game_result):
        self.games_played += 1
        if game_result['winner'] == self:
            self.wins += 1
        else:
            self.losses += 1
        
        self.average_score = (self.average_score * (self.games_played - 1) + game_result['score']) / self.games_played
        
        if game_result['score'] > self.highest_score:
            self.highest_score = game_result['score']
        
        if game_result['checkout'] > self.highest_checkout:
            self.highest_checkout = game_result['checkout']
        
        self.checkout_percentage = (self.wins / self.games_played) * 100
        self.last_updated = datetime.utcnow()
        
        cache.delete(f'player_stats_{self.id}')
        cache.delete_memoized(Player.get_top_players)

    @classmethod
    @cache.memoize(timeout=3600)
    def get_top_players(cls, limit=10):
        return cls.query.order_by(cls.average_score.desc()).limit(limit).all()

    @classmethod
    @cache.memoize(timeout=300)
    def get_player_stats(cls, player_id):
        return db.session.query(
            func.avg(cls.average_score).label('avg_score'),
            func.sum(cls.games_played).label('total_games'),
            func.sum(cls.wins).label('total_wins'),
            func.max(cls.highest_score).label('max_score')
        ).filter(cls.id == player_id).first()

    def calculate_win_rate(self):
        return (self.wins / self.games_played) * 100 if self.games_played > 0 else 0

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'average_score': self.average_score,
            'games_played': self.games_played,
            'wins': self.wins,
            'losses': self.losses,
            'highest_score': self.highest_score,
            'highest_checkout': self.highest_checkout,
            'win_rate': self.calculate_win_rate()
        }
