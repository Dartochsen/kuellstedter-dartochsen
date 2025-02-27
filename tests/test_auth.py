import unittest
from app import create_app, db
from app.models.user import User
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    WTF_CSRF_ENABLED = False

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_login_and_logout(self):
        # Registriere einen neuen Benutzer
        response = self.client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword',
            'password2': 'testpassword'
        })
        self.assertEqual(response.status_code, 302)  # Redirect nach erfolgreicher Registrierung

        # Login
        response = self.client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Willkommen', response.get_data(as_text=True))

        # Logout
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Sie wurden erfolgreich abgemeldet', response.get_data(as_text=True))

    def test_invalid_login(self):
        response = self.client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Ungültiger Benutzername oder Passwort', response.get_data(as_text=True))

    def test_protected_route(self):
        response = self.client.get('/profile', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Bitte melden Sie sich an', response.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main()
