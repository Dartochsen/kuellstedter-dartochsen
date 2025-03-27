from app import create_app
from app.models.user import User
from app.extensions import db

def set_user_as_admin(username):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.role = 'admin'
            db.session.commit()
            print(f"Rolle für {user.username} auf 'admin' gesetzt und gespeichert")
        else:
            print(f"Benutzer '{username}' nicht gefunden")

        # Überprüfe die Änderung
        updated_user = User.query.filter_by(username=username).first()
        if updated_user:
            print(f"Aktualisierte Rolle für {updated_user.username}: {updated_user.role}")
        else:
            print("Benutzer nach Update nicht gefunden")

if __name__ == '__main__':
    set_user_as_admin('Martin Scheffel')
