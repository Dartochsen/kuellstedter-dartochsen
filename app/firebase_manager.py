import firebase_admin
from firebase_admin import credentials, db, messaging
from flask import jsonify
import logging
logging.basicConfig(level=logging.DEBUG)

cred = credentials.Certificate("instance/config/serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://dartochsenapp.firebaseio.com'
})

def push_data(path, data):
    try:
        ref = db.reference(path)
        ref.push(data)
    except Exception as e:
        logging.error(f"Fehler beim Pushen von Daten: {str(e)}")
        raise

def get_data(path):
    try:
        ref = db.reference(path)
        return ref.get()
    except Exception as e:
        logging.error(f"Fehler beim Abrufen von Daten: {str(e)}")
        raise

def get_realtime_data(path):
    ref = db.reference(path)
    return ref

def push_realtime_data(path, data):
    ref = db.reference(path)
    new_ref = ref.push(data)
    return new_ref.key

def update_realtime_data(path, data):
    ref = db.reference(path)
    ref.update(data)

def remove_realtime_data(path):
    ref = db.reference(path)
    ref.delete()
    
def create_tournament(data):
    tournament_ref = db.reference('turniere').push(data)
    return tournament_ref.key

def update_tournament(tournament_id, data):
    db.reference(f'turniere/{tournament_id}').update(data)

def get_tournament(tournament_id):
    return db.reference(f'turniere/{tournament_id}').get()

def add_team_to_tournament(tournament_id, team_data):
    teams_ref = db.reference(f'turniere/{tournament_id}/teams')
    teams_ref.push(team_data)

def update_match_result(tournament_id, match_id, result):
    match_ref = db.reference(f'turniere/{tournament_id}/matches/{match_id}')
    match_ref.update(result)

def search_data(query):
    all_data = db.reference('/').get()
    results = []
    for category, items in all_data.items():
        for item_id, item in items.items():
            if isinstance(item, dict) and any(query.lower() in str(value).lower() for value in item.values()):
                results.append({
                    'category': category,
                    'id': item_id,
                    'data': item
                })
    return results

def get_analytics_data():
    return {
        'total_users': len(db.reference('mitglieder').get() or {}),
        'total_tournaments': len(db.reference('turniere').get() or {}),
        'active_discussions': len(db.reference('diskussionsforum').get() or {})
    }

def send_push_notification(token, title, body):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=token,
    )
    response = messaging.send(message)
    return response

def test_db_connection():
    try:
        ref = db.reference('/')
        ref.get()
        return True
    except Exception as e:
        logging.error(f"Datenbankverbindungsfehler: {str(e)}")
        return False

# Implementieren Sie hier weitere Firebase-Funktionen bei Bedarf
