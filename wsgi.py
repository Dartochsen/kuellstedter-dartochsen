from app import create_app

# Erstellen der Flask-Anwendung
application = create_app()

# Dieser Block wird nur ausgeführt, wenn das Skript direkt gestartet wird
if __name__ == '__main__':
    # Konfigurieren Sie hier zusätzliche Einstellungen für die Entwicklungsumgebung, falls nötig
    application.run(debug=True, host='0.0.0.0', port=5000)
