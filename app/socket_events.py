from flask_socketio import emit
from .extensions import socketio

@socketio.on('connect')
def handle_connect():
    emit('connection_response', {'data': 'Connected'})

@socketio.on('tournament_update')
def handle_tournament_update(data):
    emit('update_tournament', data, broadcast=True)

@socketio.on('new_participant')
def handle_new_participant(data):
    emit('participant_added', data, broadcast=True)

@socketio.on('match_result')
def handle_match_result(data):
    emit('update_match', data, broadcast=True)

def init_socket_events(app):
    socketio.init_app(app)
