from app import create_app
from app.extensions import db
from app.models.user import User

def update_user_roles():
    app = create_app()
    with app.app_context():
        users = User.query.all()
        for user in users:
            if user.is_admin:
                user.role = 'admin'
            elif user.is_member:
                user.role = 'member'
            else:
                user.role = 'user'
        db.session.commit()
        print("Benutzerrollen wurden aktualisiert.")

if __name__ == '__main__':
    update_user_roles()
