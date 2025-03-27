from flask import current_app
import firebase_admin
from firebase_admin import messaging

def send_notification(title, body, token):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=token,
        )
        response = messaging.send(message)
        current_app.logger.info("Benachrichtigung erfolgreich gesendet: %s", response)
        return True
    except Exception as e:
        current_app.logger.error("Fehler beim Senden der Benachrichtigung: %s", str(e))
        return False
