from datetime import datetime
from app.models import Player, ThrowData
from app.extensions import db

def collect_player_data(player_id, performance_metrics):
    data = {
        'player_id': player_id,
        'metrics': performance_metrics,
        'timestamp': datetime.now()
    }
    return store_data(data)

def store_data(data):
    player = Player.query.get(data['player_id'])
    if not player:
        raise ValueError("Player not found")

    throw_data = ThrowData(
        player=player,
        angle=data['metrics'].get('throw_angle'),
        velocity=data['metrics'].get('speed'),
        accuracy=data['metrics'].get('accuracy'),
        score=data['metrics'].get('score', 0),  # Assuming a default score of 0 if not provided
        timestamp=data['timestamp']
    )
    db.session.add(throw_data)
    db.session.commit()
    
    return throw_data

def get_player_performance(player_id, start_date=None, end_date=None):
    query = ThrowData.query.filter_by(player_id=player_id)
    if start_date:
        query = query.filter(ThrowData.timestamp >= start_date)
    if end_date:
        query = query.filter(ThrowData.timestamp <= end_date)
    return query.all()
