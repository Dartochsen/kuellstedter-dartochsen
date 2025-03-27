from app.models import Player, ThrowData
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
import numpy as np

def analyze_player_data():
    players = Player.query.all()
    data = [[p.average_score, p.games_played, p.training_hours] for p in players]
    
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data)
    
    kmeans = KMeans(n_clusters=3)
    kmeans.fit(scaled_data)
    
    for i, player in enumerate(players):
        player.cluster = kmeans.labels_[i]
    
    return players

def get_recommendation(player):
    if player.cluster == 0:
        return "Fokussieren Sie sich auf die Verbesserung Ihrer Wurftechnik."
    elif player.cluster == 1:
        return "Erhöhen Sie Ihre Trainingszeit, um Ihre Konsistenz zu verbessern."
    else:
        return "Arbeiten Sie an Ihrer mentalen Stärke für Wettkampfsituationen."

def analyze_player_trend(player_id, stat='average_score', days=30):
    player = Player.query.get(player_id)
    if not player:
        return None

    throw_data = ThrowData.query.filter_by(player_id=player_id).order_by(ThrowData.timestamp.desc()).limit(days).all()
    
    if not throw_data:
        return "Nicht genügend Daten für eine Trendanalyse."

    dates = np.array(range(len(throw_data))).reshape(-1, 1)
    scores = np.array([getattr(throw, stat) for throw in throw_data])

    model = LinearRegression()
    model.fit(dates, scores)

    trend = model.coef_[0]
    
    if trend > 0:
        return f"Positive Entwicklung: +{trend:.2f} pro Tag"
    elif trend < 0:
        return f"Negative Entwicklung: {trend:.2f} pro Tag"
    else:
        return "Stabile Leistung"

def generate_training_recommendation(player_id):
    player = Player.query.get(player_id)
    if not player:
        return None

    if player.checkout_percentage < 40:
        return "Fokussieren Sie sich auf das Üben von Checkouts, insbesondere die häufigen wie 32, 40, 36."
    elif player.average_score < 60:
        return "Arbeiten Sie an Ihrer Konsistenz. Üben Sie das Treffen von Triple 20, 19 und 18."
    else:
        return "Ihre Leistung ist gut. Konzentrieren Sie sich auf mentales Training und Wettkampfvorbereitung."
