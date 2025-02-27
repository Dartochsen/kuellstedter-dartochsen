from app.main import bp
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, current_app, session
import time
from werkzeug.exceptions import HTTPException
from urllib.parse import urlparse
from app.models import Player, ThrowData, Event
from app.models.user import User
from app.services.mail_service import send_password_reset_email
from app.extensions import db, bcrypt
from app.forms import *
from app.services.event_management import register_user_for_event
from app.data_collection.data_collection import collect_player_data, get_player_performance
from app.analysis import analyze_player_data, get_recommendation
from app.firebase_manager import (
    push_data, add_news, add_event, get_data, get_realtime_data, create_tournament, 
    update_tournament, get_tournament, add_team_to_tournament, 
    update_match_result, search_data, get_analytics_data, test_db_connection, register_user_for_event, get_event, get_news, get_news_item, delete_event, delete_news_item, update_event, update_news_item
)
from app.chatbot import get_chatbot_response
from flask_login import login_required, login_user, current_user, logout_user
import logging
from datetime import datetime
import random
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME = 600  # 10 Minuten in Sekunden

@bp.route('/')
def index():
    try:
        news_items = get_data('news', limit=5, order_by='date')
        upcoming_events = get_data('events', limit=5, order_by='date')
        
        # Filtern Sie vergangene Ereignisse heraus
        current_date = datetime.now().strftime('%Y-%m-%d')
        upcoming_events = [event for event in upcoming_events if event['date'] >= current_date]

        return render_template('index.html', 
                               news_items=news_items, 
                               upcoming_events=upcoming_events)
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

@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if 'login_attempts' not in session:
        session['login_attempts'] = 0
    
    if session['login_attempts'] >= MAX_LOGIN_ATTEMPTS:
        if 'lockout_time' in session and time.time() < session['lockout_time']:
            flash('Account gesperrt. Bitte versuchen Sie es später erneut.', 'error')
            return render_template('login.html', title='Anmelden', form=form)
        else:
            session['login_attempts'] = 0
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            session['login_attempts'] += 1
            if session['login_attempts'] >= MAX_LOGIN_ATTEMPTS:
                session['lockout_time'] = time.time() + LOCKOUT_TIME
            flash('Ungültiger Benutzername oder Passwort', 'error')
            return redirect(url_for('main.login'))
        
        login_user(user, remember=form.remember_me.data)
        session['login_attempts'] = 0
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    
    return render_template('login.html', title='Anmelden', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sie wurden erfolgreich abgemeldet.')
    return redirect(url_for('main.index'))

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Ihr Passwort wurde erfolgreich geändert.', 'success')
            return redirect(url_for('main.profile'))
        else:
            flash('Falsches aktuelles Passwort. Bitte versuchen Sie es erneut.', 'danger')
    return render_template('change_password.html', form=form)

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Eine E-Mail mit Anweisungen zum Zurücksetzen Ihres Passworts wurde gesendet.', 'info')
        return redirect(url_for('main.login'))
    return render_template('reset_password_request.html', title='Passwort zurücksetzen', form=form)

@bp.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('Das ist ein ungültiger oder abgelaufener Token', 'warning')
        return redirect(url_for('main.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Ihr Passwort wurde aktualisiert! Sie können sich jetzt anmelden', 'success')
        return redirect(url_for('main.login'))
    return render_template('reset_token.html', title='Passwort zurücksetzen', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            flash('Ihr Konto wurde erfolgreich erstellt! Sie können sich jetzt anmelden.', 'success')
            return redirect(url_for('main.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.', 'danger')
    return render_template('register.html', title='Registrieren', form=form)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Ihre Änderungen wurden gespeichert.')
        return redirect(url_for('main.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Profil bearbeiten', form=form)

@bp.route('/events')
def events():
    events_list = get_events()
    return render_template('events.html', title='Events', events=events_list)

@bp.route('/event/<string:event_id>')
def event_detail(event_id):
    event = get_event(event_id)
    if event is None:
        abort(404)
    return render_template('event_detail.html', title=event['title'], event=event)

@bp.route('/event/<string:event_id>/delete', methods=['POST'])
@login_required
def delete_event_route(event_id):
    if delete_event(event_id):
        flash('Event erfolgreich gelöscht', 'success')
    else:
        flash('Fehler beim Löschen des Events', 'error')
    return redirect(url_for('main.events'))

@bp.route('/event/<string:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = get_event(event_id)
    if event is None:
        abort(404)
    form = EditEventForm()
    if form.validate_on_submit():
        updated_event = {
            'title': form.title.data,
            'description': form.description.data,
            'date': form.date.data.strftime('%Y-%m-%d'),
            'location': form.location.data
        }
        if update_event(event_id, updated_event):
            flash('Event erfolgreich aktualisiert', 'success')
            return redirect(url_for('main.event_detail', event_id=event_id))
        else:
            flash('Fehler beim Aktualisieren des Events', 'error')
    elif request.method == 'GET':
        form.title.data = event['title']
        form.description.data = event['description']
        form.date.data = datetime.strptime(event['date'], '%Y-%m-%d')
        form.location.data = event['location']
    return render_template('edit_event.html', title='Event bearbeiten', form=form)

@bp.route('/news')
def news():
    news_list = get_news()
    return render_template('news.html', title='Neuigkeiten', news=news_list)

@bp.route('/news/<string:news_id>')
def news_detail(news_id):
    news_item = get_news_item(news_id)
    if news_item is None:
        abort(404)
    return render_template('news_detail.html', title=news_item['title'], news_item=news_item)

@bp.route('/news/<string:news_id>/delete', methods=['POST'])
@login_required
def delete_news_route(news_id):
    if delete_news_item(news_id):
        flash('Neuigkeit erfolgreich gelöscht', 'success')
    else:
        flash('Fehler beim Löschen der Neuigkeit', 'error')
    return redirect(url_for('main.news'))

@bp.route('/news/<string:news_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_news(news_id):
    news_item = get_news_item(news_id)
    if news_item is None:
        abort(404)
    form = EditNewsForm()
    if form.validate_on_submit():
        updated_news = {
            'title': form.title.data,
            'content': form.content.data
        }
        if update_news_item(news_id, updated_news):
            flash('Neuigkeit erfolgreich aktualisiert', 'success')
            return redirect(url_for('main.news_detail', news_id=news_id))
        else:
            flash('Fehler beim Aktualisieren der Neuigkeit', 'error')
    elif request.method == 'GET':
        form.title.data = news_item['title']
        form.content.data = news_item['content']
    return render_template('edit_news.html', title='Neuigkeit bearbeiten', form=form)

@bp.route('/add_news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = AddNewsForm()
    if form.validate_on_submit():
        news_data = {
            'title': form.title.data,
            'content': form.content.data,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'authorId': current_user.id
        }
        add_news(news_data)
        flash('Neuigkeit erfolgreich hinzugefügt', 'success')
        return redirect(url_for('main.news'))
    return render_template('add_news.html', title='Neuigkeit hinzufügen', form=form)

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
        db.session.execute('SELECT 1')
        return 'Datenbankverbindung erfolgreich!'
    except Exception as e:
        return f'Datenbankfehler: {str(e)}'

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

@bp.route('/register-event', methods=['POST'])
@login_required
def register_event():
    event_id = request.json.get('eventId')
    if not event_id:
        return jsonify({'success': False, 'message': 'Keine Event-ID angegeben'}), 400
    
    try:
        success = register_user_for_event(current_user.id, event_id)
        if success:
            return jsonify({'success': True, 'message': 'Erfolgreich für das Event angemeldet'})
        else:
            return jsonify({'success': False, 'message': 'Anmeldung fehlgeschlagen'}), 400
    except Exception as e:
        current_app.logger.error(f"Fehler bei der Event-Registrierung: {str(e)}")
        return jsonify({'success': False, 'message': 'Ein Fehler ist aufgetreten'}), 500

@bp.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_event():
    form = AddEventForm()
    if form.validate_on_submit():
        event_data = {
            'title': form.title.data,
            'description': form.description.data,
            'date': form.date.data.strftime('%Y-%m-%d'),
            'location': form.location.data,
            'organizerId': current_user.id
        }
        add_event(event_data)
        flash('Event erfolgreich hinzugefügt', 'success')
        return redirect(url_for('main.events'))
    return render_template('add_event.html', title='Event hinzufügen', form=form)

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

@bp.route('/test-blueprint')
def test_blueprint():
    return "Blueprint Test Route"

# Debug-Ausgabe der registrierten Routen
print(f"Routen in main/routes.py: {[f.__name__ for f in bp.deferred_functions if callable(f)]}")