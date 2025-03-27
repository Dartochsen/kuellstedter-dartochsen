from app.models.event import Event
from app.models import User
from app.extensions import db
from app.models import Event

def register_user_for_event(user_id, event_id):
    user = User.query.get(user_id)
    event = Event.query.get(event_id)
    
    if not user or not event:
        return False, "Benutzer oder Event nicht gefunden"
    
    if event in user.registered_events:
        return False, "Benutzer ist bereits für dieses Event registriert"
    
    if event.is_full():
        return False, "Das Event ist bereits ausgebucht"
    
    user.registered_events.append(event)
    db.session.commit()
    
    return True, "Erfolgreich für das Event registriert"

def is_event_full(event_id):
    event = Event.query.get(event_id)
    if not event:
        return True
    return event.current_participants >= event.max_participants

def get_event_details(event_id):
    event = Event.query.get(event_id)
    if not event:
        return None
    return {
        "id": event.id,
        "name": event.name,
        "date": event.date,
        "description": event.description,
        "current_participants": event.current_participants,
        "max_participants": event.max_participants
    }

def generate_knockout_matches(teams):
    matches = []
    num_teams = len(teams)
    num_rounds = (num_teams - 1).bit_length()
    
    for round in range(num_rounds):
        round_matches = []
        num_matches = 2 ** (num_rounds - round - 1)
        for match in range(num_matches):
            if round == 0 and match < num_teams // 2:
                round_matches.append([teams[match * 2], teams[match * 2 + 1]])
            else:
                round_matches.append([None, None])
        matches.append(round_matches)
    
    return matches
