print("routes.py wird geladen")

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, current_app
from app.models import Player, ThrowData, Event
from app.services.event_management import register_user_for_event
from app.data_collection.data_collection import collect_player_data, get_player_performance
from app.analysis import analyze_player_data, get_recommendation
from app.firebase_manager import (
    push_data, get_data, get_realtime_data, create_tournament, 
    update_tournament, get_tournament, add_team_to_tournament, 
    update_match_result, search_data, get_analytics_data, test_db_connection
)
from app.chatbot import get_chatbot_response
from flask_login import login_required, current_user
import logging
from datetime import datetime
import random

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    print("Index-Funktion wurde aufgerufen")
    current_app.logger.info("Index-Route aufgerufen")
    try:
        news_items = get_data('news', limit=5)
        current_app.logger.info(f"News items: {news_items}")
        upcoming_events = get_data('events', limit=5)
        current_app.logger.info(f"Upcoming events: {upcoming_events}")
        return render_template('index.html', news_items=news_items, upcoming_events=upcoming_events)
    except Exception as e:
        current_app.logger.error(f"Fehler beim Laden der Startseite: {str(e)}")
        return render_template('error.html', error="Fehler beim Laden der Startseite"), 500

@bp.route('/test-firebase')
def test_firebase():
    try:
        ref = db.reference('/')
        ref.set({'test': 'Erfolgreich mit Firebase verbunden!'})
        return 'Firebase-Test erfolgreich!'
    except Exception as e:
        logger.error(f"Fehler beim Firebase-Test: {str(e)}")
        return 'Firebase-Test fehlgeschlagen.'

@bp.route('/news')
def news():
    try:
        news_items = get_data('news')
        return render_template('news.html', news_items=news_items)
    except Exception as e:
        logger.error(f"Fehler beim Laden der News: {str(e)}")
        return render_template('error.html', error="Fehler beim Laden der News"), 500

@bp.route('/events')
def events():
    events = get_data('events')
    return render_template('events.html', events=events)

@bp.route('/suche')
def suche():
    query = request.args.get('q', '')
    results = search_data(query)
    return render_template('suchergebnisse.html', query=query, results=results)

@bp.route('/admin/analytics')
@login_required
def admin_analytics():
    analytics_data = get_analytics_data()
    return render_template('admin_analytics.html', data=analytics_data)

@bp.route('/mitgliederbereich', methods=['GET', 'POST'])
@login_required
def mitgliederbereich():
    try:
        if request.method == 'POST':
            neues_mitglied = {
                'name': request.form['name'],
                'email': request.form['email'],
                'team': request.form['team']
            }
            push_data('mitglieder', neues_mitglied)
            flash('Neues Mitglied erfolgreich hinzugefügt!', 'success')
            return redirect(url_for('main.mitgliederbereich'))
        
        mitglieder = get_data('mitglieder')
        return render_template('members.html', mitglieder=mitglieder)
    except Exception as e:
        logger.error(f"Fehler im Mitgliederbereich: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@bp.route('/mitgliederbereich/neu', methods=['GET', 'POST'])
@login_required
def neues_mitglied():
    if request.method == 'POST':
        neues_mitglied = {
            'name': request.form['name'],
            'email': request.form['email'],
            'team': request.form['team']
        }
        push_data('mitglieder', neues_mitglied)
        flash('Neues Mitglied erfolgreich hinzugefügt!', 'success')
        return redirect(url_for('main.mitgliederbereich'))
    return render_template('neues_mitglied.html')

@bp.route('/termine')
def termine():
    termine = get_data('termine')
    return render_template('events.html', termine=termine)

@bp.route('/termine/neu', methods=['GET', 'POST'])
@login_required
def neuer_termin():
    if request.method == 'POST':
        termin_data = {
            'titel': request.form['titel'],
            'datum': request.form['datum'],
            'uhrzeit': request.form['uhrzeit'],
            'beschreibung': request.form['beschreibung'],
            'typ': request.form['typ']
        }
        push_data('termine', termin_data)
        flash('Neuer Termin erfolgreich hinzugefügt!')
        return redirect(url_for('main.termine'))
    return render_template('neuer_termin.html')

@bp.route('/turniere')
def turniere():
    try:
        turniere = get_data('turniere')
        return render_template('tournaments.html', turniere=turniere)
    except Exception as e:
        logger.error(f"Fehler in der Turniere-Route: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@bp.route('/turniere/neu', methods=['POST'])
@login_required
def neues_turnier():
    turnier_data = {
        'name': request.form['name'],
        'datum': request.form['datum'],
        'ort': request.form['ort'],
        'modus': 'Jeder gegen jeden mit K.O.',
        'phase': 'Anmeldung',
        'teams': [],
        'matches': []
    }
    turnier_id = create_tournament(turnier_data)
    return jsonify({'success': True, 'id': turnier_id})

@bp.route('/turnier/<turnier_id>/team_hinzufuegen', methods=['POST'])
@login_required
def team_hinzufuegen(turnier_id):
    team_data = {
        'name': request.form['team_name'],
        'punkte': 0
    }
    add_team_to_tournament(turnier_id, team_data)
    return jsonify({'success': True})

@bp.route('/turnier/<turnier_id>/start_round_robin', methods=['POST'])
@login_required
def start_round_robin(turnier_id):
    try:
        turnier = get_tournament(turnier_id)
        teams = turnier['teams']
        matches = generate_round_robin_matches(teams)
        update_tournament(turnier_id, {'phase': 'Round Robin', 'matches': matches})
        logger.info("Round Robin für Turnier %s gestartet", turnier_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error("Fehler beim Starten des Round Robin für Turnier %s: %s", turnier_id, str(e))
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_round_robin_matches(teams):
    matches = []
    for i in range(len(teams)):
        for j in range(i+1, len(teams)):
            matches.append({
                'team1': teams[i]['name'],
                'team2': teams[j]['name'],
                'score1': None,
                'score2': None
            })
    random.shuffle(matches)
    return matches

@bp.route('/turnier/<turnier_id>/update_match', methods=['POST'])
@login_required
def update_match(turnier_id):
    match_id = request.form['match_id']
    result = {
        'score1': int(request.form['score1']),
        'score2': int(request.form['score2'])
    }
    update_match_result(turnier_id, match_id, result)
    return jsonify({'success': True})

@bp.route('/turnier/<turnier_id>/start_knockout', methods=['POST'])
@login_required
def start_knockout(turnier_id):
    turnier = get_tournament(turnier_id)
    sorted_teams = sorted(turnier['teams'], key=lambda x: x['punkte'], reverse=True)
    knockout_teams = sorted_teams[:8]  # Top 8 Teams für K.O.-Phase
    knockout_matches = generate_knockout_matches(knockout_teams)
    update_tournament(turnier_id, {'phase': 'Knockout', 'knockout_matches': knockout_matches})
    return jsonify({'success': True})

def generate_knockout_matches(teams):
    matches = []
    for i in range(0, len(teams), 2):
        matches.append({
            'team1': teams[i]['name'],
            'team2': teams[i+1]['name'],
            'score1': None,
            'score2': None
        })
    return matches

@bp.route('/turnier/<turnier_id>')
def turnier_details(turnier_id):
    turnier = get_tournament(turnier_id)
    if turnier:
        return render_template('turnier_details.html', turnier=turnier)
    else:
        flash('Turnier nicht gefunden', 'error')
        return redirect(url_for('main.turniere'))

@bp.route('/training')
def training():
    trainings = get_data('trainings')
    return render_template('training.html', trainings=trainings)

@bp.route('/training/neu', methods=['GET', 'POST'])
@login_required
def neues_training():
    if request.method == 'POST':
        training_data = {
            'datum': request.form['datum'],
            'uhrzeit': request.form['uhrzeit'],
            'dauer': request.form['dauer'],
            'thema': request.form['thema'],
            'trainer': request.form['trainer']
        }
        push_data('trainings', training_data)
        flash('Neues Training erfolgreich hinzugefügt!')
        return redirect(url_for('main.training'))
    return render_template('neues_training.html')

@bp.route('/diskussionsforum')
def diskussionsforum():
    themen = get_data('forum_themen')
    return render_template('forum.html', themen=themen)

@bp.route('/diskussionsforum/neues_thema', methods=['GET', 'POST'])
@login_required
def neues_thema():
    if request.method == 'POST':
        thema_data = {
            'titel': request.form['titel'],
            'inhalt': request.form['inhalt'],
            'autor': current_user.name,
            'datum': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'antworten': []
        }
        push_data('forum_themen', thema_data)
        flash('Neues Thema erfolgreich erstellt!')
        return redirect(url_for('main.diskussionsforum'))
    return render_template('neues_thema.html')

@bp.route('/marktplatz')
def marktplatz():
    angebote = get_data('marktplatz_angebote')
    return render_template('marketplace.html', angebote=angebote)

@bp.route('/marktplatz/neues_angebot', methods=['GET', 'POST'])
@login_required
def neues_angebot():
    if request.method == 'POST':
        angebot_data = {
            'titel': request.form['titel'],
            'beschreibung': request.form['beschreibung'],
            'preis': float(request.form['preis']),
            'verkäufer': current_user.name,
            'datum': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        push_data('marktplatz_angebote', angebot_data)
        flash('Neues Angebot erfolgreich erstellt!')
        return redirect(url_for('main.marktplatz'))
    return render_template('neues_angebot.html')

@bp.route('/api/updates/<path>')
def get_updates(path):
    data = get_realtime_data(path).get()
    return jsonify(data)

@bp.route('/send_notification', methods=['POST'])
@login_required
def send_notification():
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title='Neue Nachricht',
                body='Sie haben eine neue Nachricht erhalten.'
            ),
            token='DEVICE_TOKEN_HERE',
        )
        response = messaging.send(message)
        logger.info("Benachrichtigung erfolgreich gesendet: %s", response)
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        logger.error("Fehler beim Senden der Benachrichtigung: %s", str(e))
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/test_db')
@login_required
def test_db():
    try:
        if test_db_connection():
            return "Datenbankverbindung erfolgreich!"
        else:
            raise Exception("Datenbankverbindung fehlgeschlagen")
    except Exception as e:
        logger.error("Fehler bei der Datenbankverbindung: %s", str(e))
        return "Fehler bei der Datenbankverbindung", 500

@bp.route('/chatbot', methods=['POST'])
def chatbot():
    user_input = request.json['message']
    response = get_chatbot_response(user_input)
    return jsonify({'response': response})

@bp.route('/player_data', methods=['GET', 'POST'])
@login_required
def player_data():
    if request.method == 'POST':
        try:
            performance_metrics = {
                'throw_angle': float(request.form['throw_angle']),
                'speed': float(request.form['speed']),
                'accuracy': float(request.form['accuracy']),
                'score': int(request.form['score'])
            }
            throw_data = collect_player_data(int(request.form['player_id']), performance_metrics)
            flash('Wurfdaten erfolgreich hinzugefügt!', 'success')
        except ValueError as e:
            flash(str(e), 'error')
        return redirect(url_for('main.player_data'))
    players = Player.query.all()
    return render_template('player_data.html', players=players)

@bp.route('/player_analysis')
@login_required
def player_analysis():
    players = Player.query.all()
    analyzed_data = analyze_player_data()
    for player in players:
        player.recommendation = get_recommendation(player)
    return render_template('player_analysis.html', players=players, analyzed_data=analyzed_data)

@bp.route('/player_performance/<int:player_id>')
@login_required
def player_performance(player_id):
    player = Player.query.get_or_404(player_id)
    performance_data = get_player_performance(player_id)
    return render_template('player_performance.html', player=player, performance_data=performance_data)

@bp.route('/api/throw_data', methods=['POST'])
@login_required
def add_throw_data():
    data = request.json
    try:
        throw_data = collect_player_data(
            data['player_id'],
            {
                'throw_angle': data['angle'],
                'speed': data['velocity'],
                'accuracy': data['accuracy'],
                'score': data['score']
            }
        )
        return jsonify({"message": "Wurfdaten erfolgreich hinzugefügt", "id": throw_data.id}), 201
    except ValueError as e:
        logger.error("Fehler beim Hinzufügen von Wurfdaten: %s", str(e))
        return jsonify({"error": str(e)}), 400

# Fehlerbehandlung
@bp.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@bp.errorhandler(500)
def internal_server_error(error):
    logger.error('Server Error: %s', str(error))
    return render_template('500.html'), 500

@bp.errorhandler(Exception)
def handle_exception(error):
    if isinstance(error, HTTPException):
        return render_template('error.html', error=error), error.code
    logger.error("Unerwarteter Fehler: %s", str(error))
    return render_template('500.html'), 500

@bp.route('/simulate_error/<int:error_code>')
@login_required
def simulate_error(error_code):
    abort(error_code)

@bp.route('/register-event', methods=['POST'])
@login_required
def register_event():
    event_id = request.json.get('eventId')
    try:
        success, message = register_user_for_event(current_user.id, event_id)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        logger.error(f"Fehler bei der Event-Registrierung: {str(e)}")
        return jsonify({'success': False, 'message': 'Ein Fehler ist aufgetreten'}), 500

@bp.route('/test-blueprint')
def test_blueprint():
    return "Blueprint Test Route"