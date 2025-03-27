import pytest
from flask_socketio import SocketIOTestClient, SocketIO
from your_app import create_app  # Importieren Sie Ihre Flask-App-Factory-Funktion

@pytest.fixture
def socketio_client(app):
    from app import socketio
    return SocketIOTestClient(app, socketio)

def test_tournament_update(socketio_client):
    socketio_client.emit('tournament_update', {'id': 1, 'name': 'Updated Tournament'})
    received = socketio_client.get_received()
    assert len(received) == 1
    assert received[0]['name'] == 'update_tournament'
    assert received[0]['args'][0]['name'] == 'Updated Tournament'

# Fügen Sie hier weitere Socket.IO-Tests hinzu
def test_socket_connection():
    app = create_app()
    socketio = SocketIO(app)
    client = socketio.test_client(app)
    assert client.is_connected()