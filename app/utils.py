from flask import request
import json

def get_data(data_type, limit=None, order_by=None):
    # Hier würde normalerweise die Logik zur Datenbankabfrage stehen
    # Da wir keine spezifischen Informationen über Ihre Datenstruktur haben,
    # verwenden wir ein Beispiel-Dictionary
    
    sample_data = {
        'news': [
            {'id': 1, 'title': 'Neuigkeit 1', 'date': '2025-02-28'},
            {'id': 2, 'title': 'Neuigkeit 2', 'date': '2025-02-27'},
        ],
        'events': [
            {'id': 1, 'name': 'Event 1', 'date': '2025-03-01'},
            {'id': 2, 'name': 'Event 2', 'date': '2025-03-02'},
        ]
    }
    
    data = sample_data.get(data_type, [])
    
    if order_by:
        data.sort(key=lambda x: x.get(order_by, ''), reverse=True)
    
    if limit:
        data = data[:limit]
    
    return data

def parse_request_data():
    if request.is_json:
        return request.get_json()
    elif request.form:
        return request.form.to_dict()
    elif request.data:
        return json.loads(request.data.decode('utf-8'))
    else:
        return {}
