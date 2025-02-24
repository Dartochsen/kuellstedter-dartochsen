from app.models import Player
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

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
