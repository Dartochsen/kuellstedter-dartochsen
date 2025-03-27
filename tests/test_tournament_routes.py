import pytest
from app.models import Tournament, db
from app.schemas import TournamentSchema

@pytest.fixture
def tournament_data():
    return {
        'name': 'Test Tournament',
        'date': '2025-03-15',
        'location': 'Test Location',
        'format': 'Single Elimination'
    }

def test_create_tournament(client, tournament_data):
    response = client.post('/api/tournaments/tournament', json=tournament_data)
    assert response.status_code == 201
    assert 'id' in response.json
    assert response.json['name'] == tournament_data['name']

def test_get_tournaments(client, tournament_data):
    # Create a tournament first
    client.post('/api/tournaments/tournament', json=tournament_data)
    
    response = client.get('/api/tournaments/tournaments')
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) > 0

def test_get_tournament(client, app, tournament_data):
    # Create a tournament
    response = client.post('/api/tournaments/tournament', json=tournament_data)
    tournament_id = response.json['id']
    
    response = client.get(f'/api/tournaments/tournament/{tournament_id}')
    assert response.status_code == 200
    assert response.json['name'] == tournament_data['name']

def test_update_tournament(client, app, tournament_data):
    # Create a tournament
    response = client.post('/api/tournaments/tournament', json=tournament_data)
    tournament_id = response.json['id']
    
    # Update the tournament
    updated_data = {
        'name': 'Updated Tournament Name',
        'location': 'Updated Location'
    }
    response = client.put(f'/api/tournaments/tournament/{tournament_id}', json=updated_data)
    assert response.status_code == 200
    assert response.json['name'] == updated_data['name']
    assert response.json['location'] == updated_data['location']

def test_delete_tournament(client, app, tournament_data):
    # Create a tournament
    response = client.post('/api/tournaments/tournament', json=tournament_data)
    tournament_id = response.json['id']
    
    # Delete the tournament
    response = client.delete(f'/api/tournaments/tournament/{tournament_id}')
    assert response.status_code == 204
    
    # Verify the tournament is deleted
    response = client.get(f'/api/tournaments/tournament/{tournament_id}')
    assert response.status_code == 404

# Add more tests as needed
