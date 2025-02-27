import firebase_admin
from firebase_admin import credentials, db, messaging
from flask import jsonify, current_app
import logging
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_firebase_config():
    return {
        "type": os.environ.get("FIREBASE_TYPE"),
        "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
        "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": os.environ.get("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
        "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
        "auth_uri": os.environ.get("FIREBASE_AUTH_URI"),
        "token_uri": os.environ.get("FIREBASE_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.environ.get("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL")
    }

def initialize_firebase(app=None):
    if not firebase_admin._apps:
        try:
            firebase_config = get_firebase_config()
            
            if not firebase_config:
                raise ValueError("Firebase configuration is not available")

            if 'type' not in firebase_config or firebase_config['type'] != 'service_account':
                firebase_config['type'] = 'service_account'

            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred, {
                'databaseURL': os.environ.get('FIREBASE_DATABASE_URL', 'https://dartochsenapp.firebaseio.com')
            })
            logger.info("Firebase erfolgreich initialisiert")
        except Exception as e:
            logger.error(f"Fehler bei der Firebase-Initialisierung: {str(e)}")
            raise
    else:
        logger.info("Firebase-App bereits initialisiert")

def push_data(path, data):
    try:
        ref = db.reference(path)
        ref.push(data)
        logger.info(f"Daten erfolgreich zu {path} gepusht")
    except Exception as e:
        logger.error(f"Fehler beim Pushen von Daten zu {path}: {str(e)}")
        raise

def get_data(path, limit=None, order_by=None):
    try:
        ref = db.reference(path)
        if order_by:
            ref = ref.order_by_child(order_by)
        if limit:
            ref = ref.limit_to_last(limit)
        data = ref.get()
        
        if data is None:
            return []
        
        if isinstance(data, dict):
            data = list(data.values())
        
        if order_by == 'date':
            data.sort(key=lambda x: x['date'], reverse=True)
        
        return data
    except Exception as e:
        logger.error(f"Fehler beim Abrufen von Daten von {path}: {str(e)}")
        return []

def get_realtime_data(path):
    return db.reference(path)

def push_realtime_data(path, data):
    try:
        ref = db.reference(path)
        new_ref = ref.push(data)
        logger.info(f"Echtzeitdaten erfolgreich zu {path} gepusht")
        return new_ref.key
    except Exception as e:
        logger.error(f"Fehler beim Pushen von Echtzeitdaten zu {path}: {str(e)}")
        raise

def update_realtime_data(path, data):
    try:
        ref = db.reference(path)
        ref.update(data)
        logger.info(f"Echtzeitdaten erfolgreich in {path} aktualisiert")
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren von Echtzeitdaten in {path}: {str(e)}")
        raise

def remove_realtime_data(path):
    try:
        ref = db.reference(path)
        ref.delete()
        logger.info(f"Echtzeitdaten erfolgreich aus {path} entfernt")
    except Exception as e:
        logger.error(f"Fehler beim Entfernen von Echtzeitdaten aus {path}: {str(e)}")
        raise

def create_tournament(data):
    try:
        tournament_ref = db.reference('turniere').push(data)
        logger.info(f"Turnier erfolgreich erstellt mit ID: {tournament_ref.key}")
        return tournament_ref.key
    except Exception as e:
        logger.error(f"Fehler beim Erstellen eines Turniers: {str(e)}")
        raise

def update_tournament(tournament_id, data):
    try:
        db.reference(f'turniere/{tournament_id}').update(data)
        logger.info(f"Turnier {tournament_id} erfolgreich aktualisiert")
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren des Turniers {tournament_id}: {str(e)}")
        raise

def get_tournament(tournament_id):
    try:
        tournament = db.reference(f'turniere/{tournament_id}').get()
        logger.info(f"Turnier {tournament_id} erfolgreich abgerufen")
        return tournament
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Turniers {tournament_id}: {str(e)}")
        raise

def add_team_to_tournament(tournament_id, team_data):
    try:
        teams_ref = db.reference(f'turniere/{tournament_id}/teams')
        teams_ref.push(team_data)
        logger.info(f"Team erfolgreich zum Turnier {tournament_id} hinzugefügt")
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen eines Teams zum Turnier {tournament_id}: {str(e)}")
        raise

def update_match_result(tournament_id, match_id, result):
    try:
        match_ref = db.reference(f'turniere/{tournament_id}/matches/{match_id}')
        match_ref.update(result)
        logger.info(f"Spielergebnis für Match {match_id} im Turnier {tournament_id} aktualisiert")
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren des Spielergebnisses für Match {match_id} im Turnier {tournament_id}: {str(e)}")
        raise

def search_data(query):
    try:
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
        
        logger.info(f"Suchanfrage '{query}' erfolgreich durchgeführt")
        
    except Exception as e:
         logger.error(f"Fehler bei der Suchanfrage '{query}': {str(e)}")

def get_analytics_data():
    try:
       analytics = {
           'total_users': len(db.reference('mitglieder').get() or {}),
           'total_tournaments': len(db.reference('turniere').get() or {}),
           'active_discussions': len(db.reference('diskussionsforum').get() or {})
       }
       logger.info("Analysedaten erfolgreich abgerufen")
       return analytics
    except Exception as e:
       logger.error(f"Fehler beim Abrufen der Analysedaten: {str(e)}")

def send_push_notification(token, title, body):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=token,
        )
        response = messaging.send(message)
        logger.info(f"Push-Benachrichtigung erfolgreich gesendet: {response}")
        return response
    except Exception as e:
        logger.error(f"Fehler beim Senden der Push-Benachrichtigung: {str(e)}")
        raise

def test_db_connection():
    try:
        ref = db.reference('/')
        ref.get()
        logger.info("Datenbankverbindung erfolgreich getestet")
        return True
    except Exception as e:
        logger.error(f"Datenbankverbindungsfehler: {str(e)}")
        return False

def get_event(event_id):
    event_ref = db.reference(f'events/{event_id}')
    return event_ref.get()

def delete_event(event_id):
    event_ref = db.reference(f'events/{event_id}')
    event_ref.delete()
    return True

def update_event(event_id, updated_event):
    event_ref = db.reference(f'events/{event_id}')
    event_ref.update(updated_event)
    return True

def get_news_item(news_id):
    news_ref = db.reference(f'news/{news_id}')
    return news_ref.get()

def delete_news_item(news_id):
    news_ref = db.reference(f'news/{news_id}')
    news_ref.delete()
    return True

def update_news_item(news_id, updated_news):
    news_ref = db.reference(f'news/{news_id}')
    news_ref.update(updated_news)
    return True

def register_user_for_event(user_id, event_id):
    try:
        # Überprüfen, ob der Benutzer bereits für das Event registriert ist
        user_events_ref = db.reference(f'user_events/{user_id}')
        user_events = user_events_ref.get()
        
        if user_events and event_id in user_events:
            return False  # Benutzer ist bereits registriert
        
        # Benutzer für das Event registrieren
        user_events_ref.update({event_id: True})
        
        # Teilnehmerzahl des Events erhöhen
        event_ref = db.reference(f'events/{event_id}')
        event_ref.update({
            'participants': db.reference(f'events/{event_id}/participants').get() + 1
        })
        
        return True
    except Exception as e:
        logger.error(f"Fehler bei der Registrierung des Benutzers für das Event: {str(e)}")
        return False

def initialize_event_structure():
    events_ref = db.reference('events')
    if not events_ref.get():
        events_ref.set({
            'example_event_id': {
                'title': 'Beispiel Event',
                'description': 'Dies ist ein Beispiel-Event',
                'date': '2025-03-15',
                'location': 'Küllstedt',
                'organizerId': 'example_user_id',
                'participants': 0
            }
        })
    
    user_events_ref = db.reference('user_events')
    if not user_events_ref.get():
        user_events_ref.set({
            'example_user_id': {
                'example_event_id': True
            }
        })

def add_event(event_data):
    events_ref = db.reference('events')
    new_event_ref = events_ref.push()
    new_event_ref.set(event_data)
    return new_event_ref.key

def get_news():
    return get_data('news')

def add_news(news_data):
    news_ref = db.reference('news')
    new_news_ref = news_ref.push()
    new_news_ref.set(news_data)
    return new_news_ref.key

# Fügen Sie diese Funktion hinzu, um die Firebase-Initialisierung aufzurufen
initialize_firebase()
