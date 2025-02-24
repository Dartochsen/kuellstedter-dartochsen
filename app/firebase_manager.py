import firebase_admin
from firebase_admin import credentials, db, messaging
from flask import jsonify
import logging
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_firebase():
    try:
        # Laden der Firebase-Konfiguration aus Umgebungsvariablen
        firebase_config = {
            "apiKey": os.environ.get("FIREBASE_API_KEY"),
            "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
            "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
            "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
            "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.environ.get("FIREBASE_APP_ID")
        }
        firebase_service_account = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT_KEY', '{}'))
        cred = credentials.Certificate(firebase_service_account)
        firebase_admin.initialize_app(cred, {
            'databaseURL': os.environ.get('FIREBASE_DATABASE_URL', 'https://dartochsenapp.firebaseio.com')
        })
        logger.info("Firebase erfolgreich initialisiert")
    except Exception as e:
        logger.error(f"Fehler bei der Firebase-Initialisierung: {str(e)}")
        raise

initialize_firebase()

def push_data(path, data):
    try:
        ref = db.reference(path)
        ref.push(data)
        logger.info(f"Daten erfolgreich zu {path} gepusht")
    except Exception as e:
        logger.error(f"Fehler beim Pushen von Daten zu {path}: {str(e)}")
        raise

def get_data(path):
    try:
        ref = db.reference(path)
        data = ref.get()
        logger.info(f"Daten erfolgreich von {path} abgerufen")
        return data
    except Exception as e:
        logger.error(f"Fehler beim Abrufen von Daten von {path}: {str(e)}")
        raise

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
        return results
    except Exception as e:
        logger.error(f"Fehler bei der Suchanfrage '{query}': {str(e)}")
        raise

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
        raise

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

# Implementieren Sie hier weitere Firebase-Funktionen bei Bedarf
