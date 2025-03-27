import logging
from flask import current_app, g, render_template, request, redirect, url_for, flash, jsonify, abort, session
from flask_login import login_required, login_user, current_user, logout_user
from werkzeug.exceptions import HTTPException
from urllib.parse import urlparse
from datetime import datetime, timedelta
import time
from sqlalchemy.exc import IntegrityError
from sqlalchemy import case, func
from sqlalchemy.orm import joinedload
from celery import group
from celery.result import AsyncResult
from functools import wraps

from . import bp
from .tournament_routes import bp as tournament_bp
from app.tasks import update_player_statistics, generate_weekly_report, clean_old_data, example_task, long_running_task, send_email
from app.models import Player, Game, ThrowData, Event, User, Activity, Team, Training, Role
from app.models.game import Game, game_players
from app.models.player import Player
from app.models.activity import Activity
from app.models.training import Training
from app.models.user import User
from app.models.forum import ForumThema, ForumAntwort
from app.analysis.player_analysis import analyze_player_trend, generate_training_recommendation
from app.utils import get_data
from app.tournament_logic import generate_round_robin_schedule, generate_knockout_matches, update_tournament_standings
from app.extensions import db, bcrypt, cache, limiter
from app.forms import LoginForm, RegistrationForm, ChangePasswordForm, ResetPasswordRequestForm, ResetPasswordForm, EditProfileForm, EditEventForm, AddNewsForm, EditNewsForm, AddEventForm, EditPlayerForm
from app.decorators import member_required, admin_required
from app.services.mail_service import send_password_reset_email
from app.services.event_management import register_user_for_event
from app.data_collection.data_collection import collect_player_data, get_player_performance
from app.analysis import analyze_player_data, get_recommendation
from app.services.analytics import get_analytics_data
from app.tasks import analyze_player_data_task, update_player_statistics, generate_player_analysis, example_task
from app.firebase_manager import (
    push_data, add_news, add_event, get_data, get_realtime_data, create_tournament, 
    update_tournament, get_tournament, add_team_to_tournament, 
    update_match_result, search_data, get_analytics_data, test_db_connection, 
    register_user_for_event, get_event, get_news, get_news_item, delete_event, 
    delete_news_item, update_event, update_news_item, get_events
)
from app.chatbot import get_chatbot_response

logger = logging.getLogger(__name__)

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME = 600  # 10 Minuten in Sekunden

def get_index_cache_timeout():
    return 300  # 5 Minuten Cache als Standardwert

def dynamic_cache(timeout):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f"view//{request.path}"
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout())
            return result
        return decorated_function
    return decorator

@bp.before_request
def before_request():
    g.app = bp.app

# Öffentlicher Bereich
from flask import current_app, g, render_template
from datetime import datetime
from . import bp
from app.utils import get_data

@bp.route('/')
def index():
    print("Index route is called")  # Temporäres Print-Statement für Debugging
    if not hasattr(g, 'app'):
        print("g.app is not set")
        # Fallback auf current_app, falls g.app nicht gesetzt ist
        logger = current_app.logger
    else:
        logger = g.app.logger

    logger.info("Index-Route wird aufgerufen")
    try:
        logger.info("Versuche, Daten für die Startseite zu laden")
        news_items = get_data('news', limit=5, order_by='date')
        logger.info(f"News-Items geladen: {len(news_items)}")
        upcoming_events = get_data('events', limit=5, order_by='date')
        logger.info(f"Upcoming Events geladen: {len(upcoming_events)}")
        current_date = datetime.now().strftime('%Y-%m-%d')
        upcoming_events = [event for event in upcoming_events if event['date'] >= current_date]
        logger.info("Startseite erfolgreich geladen")
        return render_template('index.html', news_items=news_items, upcoming_events=upcoming_events)
    except Exception as e:
        logger.error(f"Fehler beim Laden der Startseite: {str(e)}")
        logger.exception("Vollständiger Traceback:")
        return render_template('error.html', error="Fehler beim Laden der Startseite"), 500

@bp.route('/suche')
def suche():
    g.app.logger.info("Suche-Route aufgerufen")
    query = request.args.get('q', '')
    results = search_data(query)
    return render_template('suchergebnisse.html', query=query, results=results)

@bp.route('/events')
@cache.cached(timeout=300)
def events():
    g.app.logger.info("Events-Route aufgerufen")
    events_list = get_events()
    return render_template('events.html', title='Events', events=events_list)

@bp.route('/event/<string:event_id>')
def event_detail(event_id):
    g.app.logger.info(f"Event-Detail-Route aufgerufen für Event ID: {event_id}")
    event = get_event(event_id)
    if event is None:
        abort(404)
    return render_template('event_detail.html', title=event['title'], event=event)

@bp.route('/news')
@cache.cached(timeout=300)
def news():
    g.app.logger.info("News-Route aufgerufen")
    news_list = get_news()
    return render_template('news.html', title='Neuigkeiten', news=news_list)

@bp.route('/news/<string:news_id>')
def news_detail(news_id):
    g.app.logger.info(f"News-Detail-Route aufgerufen für News ID: {news_id}")
    news_item = get_news_item(news_id)
    if news_item is None:
        abort(404)
    return render_template('news_detail.html', title=news_item['title'], news_item=news_item)

@bp.route('/marktplatz')
@cache.cached(timeout=300)
def marktplatz():
    g.app.logger.info("Marktplatz-Route aufgerufen")
    try:
        angebote = get_data('marktplatz_angebote')
        return render_template('marketplace.html', title='Marktplatz', angebote=angebote)
    except Exception as e:
        g.app.logger.error(f"Fehler beim Laden des Marktplatzes: {str(e)}")
        return render_template('error.html', error="Ein Fehler ist beim Laden des Marktplatzes aufgetreten"), 500

@bp.route('/chatbot', methods=['POST'])
@limiter.limit("10 per minute")
def chatbot():
    g.app.logger.info("Chatbot-Route aufgerufen")
    user_input = request.json['message']
    response = get_chatbot_response(user_input)
    return jsonify({'response': response})

# Authentifizierung und Benutzerverwaltung
@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    g.app.logger.info("Login-Route aufgerufen")
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if 'login_attempts' not in session:
        session['login_attempts'] = 0
    
    if session['login_attempts'] >= MAX_LOGIN_ATTEMPTS:
        if 'lockout_time' in session and time.time() < session['lockout_time']:
            flash('Account gesperrt. Bitte versuchen Sie es später erneut.', 'error')
            return render_template('auth/login.html', title='Anmelden', form=form)
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
    
    return render_template('auth/login.html', title='Anmelden', form=form)

@bp.route('/logout')
@login_required
def logout():
    g.app.logger.info(f"Logout-Route aufgerufen für Benutzer: {current_user.username}")
    logout_user()
    flash('Sie wurden erfolgreich abgemeldet.')
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def register():
    g.app.logger.info("Registrierungs-Route aufgerufen")
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            g.app.logger.info(f"Neuer Benutzer registriert: {user.username}")
            flash('Ihr Konto wurde erfolgreich erstellt! Sie können sich jetzt anmelden.', 'success')
            return redirect(url_for('main.login'))
        except IntegrityError:
            db.session.rollback()
            g.app.logger.error("Fehler bei der Benutzerregistrierung: IntegrityError")
            flash('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.', 'danger')
    return render_template('auth/register.html', title='Registrieren', form=form)

@bp.route('/profile')
@login_required
def profile():
    g.app.logger.info(f"Profil-Route aufgerufen für Benutzer: {current_user.username}")
    player = Player.query.filter_by(user_id=current_user.id).first()
    
    total_games = 0
    wins = 0
    losses = 0
    win_rate = 0
    performance_data = []
    performance_labels = []

    if player:
        games = Game.query.filter((Game.player1_id == player.id) | (Game.player2_id == player.id)).all()
        
        total_games = len(games)
        wins = sum(1 for game in games if game.winner_id == player.id)
        losses = total_games - wins
        win_rate = round((wins / total_games * 100), 2) if total_games > 0 else 0

        performance_data = [game.player1_score if game.player1_id == player.id else game.player2_score for game in games[-10:]]
        performance_labels = [f'Spiel {i+1}' for i in range(len(performance_data))]
    
    return render_template('profile.html', 
                           user=current_user,
                           player=player,
                           total_games=total_games,
                           wins=wins,
                           losses=losses,
                           win_rate=win_rate,
                           performance_data=performance_data,
                           performance_labels=performance_labels)

@bp.route('/profile/<username>')
@login_required
def user_profile(username):
    g.app.logger.info(f"Benutzer-Profil-Route aufgerufen für: {username}")
    user = User.query.filter_by(username=username).first_or_404()
    player = Player.query.filter_by(user_id=user.id).first()
    
    if player:
        games = Game.query.filter((Game.player1_id == player.id) | (Game.player2_id == player.id)).all()
        
        total_games = len(games)
        wins = sum(1 for game in games if game.winner_id == player.id)
        losses = total_games - wins
        win_rate = (wins / total_games * 100) if total_games > 0 else 0
        
        performance_data = [game.player1_score if game.player1_id == player.id else game.player2_score for game in games[-10:]]
        performance_labels = [f'Spiel {i+1}' for i in range(len(performance_data))]
        
        recent_activities = Activity.query.filter_by(user_id=user.id).order_by(Activity.date.desc()).limit(5).all()
    else:
        total_games = wins = losses = win_rate = 0
        performance_data = performance_labels = []
        recent_activities = []

    return render_template('profile.html', 
                           user=user,
                           total_games=total_games,
                           wins=wins,
                           losses=losses,
                           win_rate=win_rate,
                           average_score=player.average_score if player else 0,
                           highest_checkout=player.highest_checkout if player else 0,
                           performance_data=performance_data,
                           performance_labels=performance_labels,
                           recent_activities=recent_activities)


# Passwortmanagement und Profilbearbeitung
@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    g.app.logger.info(f"Passwort-Änderungs-Route aufgerufen für Benutzer: {current_user.username}")
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            g.app.logger.info(f"Passwort erfolgreich geändert für Benutzer: {current_user.username}")
            flash('Ihr Passwort wurde erfolgreich geändert.', 'success')
            return redirect(url_for('main.profile'))
        else:
            g.app.logger.warning(f"Fehlgeschlagener Passwort-Änderungsversuch für Benutzer: {current_user.username}")
            flash('Falsches aktuelles Passwort. Bitte versuchen Sie es erneut.', 'danger')
    return render_template('change_password.html', form=form)

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    g.app.logger.info("Passwort-Zurücksetzungs-Anfrage-Route aufgerufen")
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
            g.app.logger.info(f"Passwort-Zurücksetzungs-E-Mail gesendet an: {user.email}")
        flash('Eine E-Mail mit Anweisungen zum Zurücksetzen Ihres Passworts wurde gesendet.', 'info')
        return redirect(url_for('main.login'))
    return render_template('reset_password_request.html', title='Passwort zurücksetzen', form=form)

@bp.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    g.app.logger.info("Passwort-Zurücksetzungs-Token-Route aufgerufen")
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_token(token)
    if user is None:
        g.app.logger.warning("Ungültiger oder abgelaufener Passwort-Zurücksetzungs-Token verwendet")
        flash('Das ist ein ungültiger oder abgelaufener Token', 'warning')
        return redirect(url_for('main.reset_password_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        g.app.logger.info(f"Passwort erfolgreich zurückgesetzt für Benutzer: {user.username}")
        flash('Ihr Passwort wurde aktualisiert! Sie können sich jetzt anmelden', 'success')
        return redirect(url_for('main.login'))
    return render_template('reset_token.html', title='Passwort zurücksetzen', form=form)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    g.app.logger.info(f"Profil-Bearbeitungs-Route aufgerufen für Benutzer: {current_user.username}")
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        g.app.logger.info(f"Profil erfolgreich aktualisiert für Benutzer: {current_user.username}")
        flash('Ihre Änderungen wurden gespeichert.')
        return redirect(url_for('main.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Profil bearbeiten', form=form)


# Vereinsmitglieder Bereich (Training, Forum, Statistiken)
@bp.route('/training', methods=['GET', 'POST'])
@login_required
@member_required
def training():
    g.app.logger.info(f"Training-Route aufgerufen von Benutzer: {current_user.username}")
    
    if request.method == 'POST' and current_user.is_trainer:
        new_training = Training(
            date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
            time=request.form['time'],
            trainer_id=request.form['trainer_id'],
            description=request.form['description']
        )
        db.session.add(new_training)
        db.session.commit()
        g.app.logger.info(f"Neue Trainingseinheit hinzugefügt von Benutzer: {current_user.username}")
        return redirect(url_for('main.training'))

    upcoming_sessions = Training.query.filter(Training.date >= datetime.now()).order_by(Training.date).limit(5).all()
    trainers = User.query.filter(User.roles.any(Role.name == 'trainer')).all()
    
    if current_user.is_trainer and current_user not in trainers:
        trainers.append(current_user)

    return render_template('training.html', 
                           upcoming_sessions=upcoming_sessions,
                           trainers=trainers)

@bp.route('/training/scorer', methods=['GET', 'POST'])
@login_required
@member_required
def scorer():
    g.app.logger.info(f"Scorer-Route aufgerufen von Benutzer: {current_user.username}")
    if request.method == 'POST':
        data = request.json
        game = Game(start_score=data['start_score'])
        db.session.add(game)
        
        for player_data in data['players']:
            player = Player.query.get(player_data['id'])
            if player:
                db.session.execute(game_players.insert().values(
                    game_id=game.id,
                    player_id=player.id,
                    score=player_data['score']
                ))
        
        if 'winner_id' in data:
            game.winner_id = data['winner_id']
        
        db.session.commit()
        cache.delete('view//statistiken')  # Invalidate cache
        g.app.logger.info(f"Neues Spiel gespeichert von Benutzer: {current_user.username}")
        return jsonify({'success': True, 'game_id': game.id})
    
    players = Player.query.all()
    return render_template('scorer.html', players=players)

@bp.route('/forum')
@login_required
@member_required
@cache.cached(timeout=300)
def forum():
    g.app.logger.info(f"Forum-Route aufgerufen von Benutzer: {current_user.username}")
    themen = ForumThema.query.order_by(ForumThema.erstellungsdatum.desc()).all()
    return render_template('forum.html', themen=themen)

@bp.route('/forum/<int:thema_id>')
@login_required
@member_required
def forum_thema(thema_id):
    g.app.logger.info(f"Forum-Thema-Route aufgerufen von Benutzer: {current_user.username} für Thema ID: {thema_id}")
    thema = ForumThema.query.options(joinedload(ForumThema.antworten)).get_or_404(thema_id)
    return render_template('forum_thema.html', thema=thema)

@bp.route('/neues_thema', methods=['GET', 'POST'])
@login_required
@member_required
@limiter.limit("5 per hour")
def neues_thema():
    g.app.logger.info(f"Neues-Thema-Route aufgerufen von Benutzer: {current_user.username}")
    if request.method == 'POST':
        titel = request.form['titel']
        inhalt = request.form['inhalt']
        neues_thema = ForumThema(titel=titel, inhalt=inhalt, autor=current_user)
        db.session.add(neues_thema)
        db.session.commit()
        cache.delete('view//forum')  # Invalidate cache
        g.app.logger.info(f"Neues Forum-Thema erstellt von Benutzer: {current_user.username}")
        flash('Neues Thema wurde erstellt!', 'success')
        return redirect(url_for('main.forum'))
    return render_template('neues_thema.html')

@bp.route('/forum/<int:thema_id>/antwort', methods=['POST'])
@login_required
@member_required
@limiter.limit("10 per minute")
def neue_antwort(thema_id):
    g.app.logger.info(f"Neue-Antwort-Route aufgerufen von Benutzer: {current_user.username} für Thema ID: {thema_id}")
    thema = ForumThema.query.get_or_404(thema_id)
    inhalt = request.form['inhalt']
    neue_antwort = ForumAntwort(inhalt=inhalt, autor=current_user, thema=thema)
    db.session.add(neue_antwort)
    db.session.commit()
    cache.delete(f'view//forum/{thema_id}')  # Invalidate cache
    g.app.logger.info(f"Neue Forum-Antwort erstellt von Benutzer: {current_user.username} für Thema ID: {thema_id}")
    flash('Ihre Antwort wurde hinzugefügt!', 'success')
    return redirect(url_for('main.forum_thema', thema_id=thema_id))

@bp.route('/statistiken', methods=['GET', 'POST'])
@login_required
@member_required
@cache.cached(timeout=300, unless=lambda: request.method != 'GET')
def statistiken():
    g.app.logger.info(f"Statistiken-Route aufgerufen von Benutzer: {current_user.username}")
    player = Player.query.get(current_user.id)
    
    stats = db.session.query(
        func.count(Game.id).label('total_games'),
        func.count(Game.id).filter(Game.winner_id == current_user.id).label('won_games'),
        func.avg(
            case(
                (Game.player1_id == current_user.id, Game.player1_score),
                (Game.player2_id == current_user.id, Game.player2_score),
                else_=None
            )
        ).label('avg_score'),
        func.max(
            case(
                (Game.player1_id == current_user.id, Game.player1_score),
                (Game.player2_id == current_user.id, Game.player2_score),
                else_=None
            )
        ).label('best_score')
    ).filter((Game.player1_id == current_user.id) | (Game.player2_id == current_user.id)).first()

    async_tasks = group(
        analyze_player_trend.s(current_user.id),
        generate_training_recommendation.s(current_user.id)
    )
    task_group = async_tasks.apply_async()

    analyzed_data = db.session.query(
        func.avg(ThrowData.angle).label('avg_angle'),
        func.avg(ThrowData.velocity).label('avg_velocity'),
        func.avg(ThrowData.accuracy).label('avg_accuracy'),
        func.max(ThrowData.score).label('max_score')
    ).filter_by(player_id=current_user.id).first()

    performance_data = ThrowData.query.filter_by(player_id=current_user.id).order_by(ThrowData.timestamp.desc()).limit(50).all()

    if request.method == 'POST':
        new_throw = ThrowData(
            player_id=current_user.id,
            angle=request.form['throw_angle'],
            velocity=request.form['speed'],
            accuracy=request.form['accuracy'],
            score=request.form['score']
        )
        db.session.add(new_throw)
        db.session.commit()
        cache.delete('view//statistiken')  # Cache invalidieren
        g.app.logger.info(f"Neue Wurfdaten hinzugefügt von Benutzer: {current_user.username}")
        flash('Neue Wurfdaten wurden erfolgreich gespeichert.', 'success')
        return redirect(url_for('main.statistiken'))

    trend_analysis, training_recommendation = task_group.get()

    return render_template('statistics.html', 
                           player=player,
                           stats=stats,
                           trend_analysis=trend_analysis,
                           training_recommendation=training_recommendation,
                           analyzed_data=analyzed_data,
                           performance_data=performance_data)


# Spieler-Performance, API-Endpunkte und administrative Funktionen
@bp.route('/player/<int:player_id>')
@login_required
@member_required
@cache.cached(timeout=300)
def player_performance(player_id):
    g.app.logger.info(f"Spieler-Performance-Route aufgerufen für Spieler ID: {player_id}")
    player = Player.query.options(joinedload(Player.throws)).get_or_404(player_id)
    trend_analysis = analyze_player_trend(player_id)
    training_recommendation = generate_training_recommendation(player_id)
    return render_template('player_performance.html', player=player, 
                           trend_analysis=trend_analysis, 
                           training_recommendation=training_recommendation)

@bp.route('/api/player-shortcuts/<int:player_id>')
@login_required
@member_required
@cache.cached(timeout=300)
def player_shortcuts(player_id):
    g.app.logger.info(f"Spieler-Shortcuts-API aufgerufen für Spieler ID: {player_id}")
    player = Player.query.get_or_404(player_id)
    shortcuts = [60, 100, 140, 180]  # Beispiel-Daten
    return jsonify({'shortcuts': shortcuts})

@bp.route('/player_list', methods=['GET'])
@login_required
@member_required
@cache.cached(timeout=300)
def player_list():
    g.app.logger.info("Spielerliste-Route aufgerufen")
    players = Player.query.options(db.joinedload(Player.games)).all()
    return render_template('player_list.html', players=players)

@bp.route('/update_stats/<int:player_id>')
@login_required
@member_required
def update_stats(player_id):
    g.app.logger.info(f"Statistik-Update angefordert für Spieler ID: {player_id}")
    update_player_statistics.delay(player_id)
    flash('Statistik-Update wurde gestartet. Dies kann einige Minuten dauern.', 'info')
    return redirect(url_for('main.player_profile', player_id=player_id))

@bp.route('/update_player_stats/<int:player_id>')
@login_required
def trigger_update_player_stats(player_id):
    g.app.logger.info(f"Spieler-Statistik-Update-API aufgerufen für Spieler ID: {player_id}")
    task = update_player_statistics.delay(player_id)
    return jsonify({"message": "Statistik-Update gestartet", "task_id": task.id}), 202

@bp.route('/analyze_player/<int:player_id>')
@login_required
@member_required
def analyze_player(player_id):
    g.app.logger.info(f"Detaillierte Spieleranalyse gestartet für Spieler ID: {player_id}")
    task = analyze_player_data_task.delay(player_id)
    return jsonify({"task_id": task.id, "message": "Spieleranalyse wurde gestartet"})

@bp.route('/add_news', methods=['GET', 'POST'])
@login_required
@member_required
def add_news():
    g.app.logger.info(f"Neuigkeiten-Hinzufügen-Route aufgerufen von Benutzer: {current_user.username}")
    form = AddNewsForm()
    if form.validate_on_submit():
        news_data = {
            'title': form.title.data,
            'content': form.content.data,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'authorId': current_user.id
        }
        add_news(news_data)
        cache.delete('view//news')  # Invalidate news cache
        g.app.logger.info(f"Neue Neuigkeit hinzugefügt von Benutzer: {current_user.username}")
        flash('Neuigkeit erfolgreich hinzugefügt', 'success')
        return redirect(url_for('main.news'))
    return render_template('add_news.html', title='Neuigkeit hinzufügen', form=form)

@bp.route('/add_event', methods=['GET', 'POST'])
@login_required
@member_required
def add_event():
    g.app.logger.info(f"Event-Hinzufügen-Route aufgerufen von Benutzer: {current_user.username}")
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
        cache.delete('view//events')  # Invalidate events cache
        g.app.logger.info(f"Neues Event hinzugefügt von Benutzer: {current_user.username}")
        flash('Event erfolgreich hinzugefügt', 'success')
        return redirect(url_for('main.events'))
    return render_template('add_event.html', title='Event hinzufügen', form=form)

@bp.route('/event/<string:event_id>/delete', methods=['POST'])
@login_required
@member_required
def delete_event_route(event_id):
    g.app.logger.info(f"Event-Lösch-Route aufgerufen für Event ID: {event_id} von Benutzer: {current_user.username}")
    if delete_event(event_id):
        cache.delete('view//events')  # Invalidate events cache
        g.app.logger.info(f"Event (ID: {event_id}) erfolgreich gelöscht von Benutzer: {current_user.username}")
        flash('Event erfolgreich gelöscht', 'success')
    else:
        g.app.logger.error(f"Fehler beim Löschen des Events (ID: {event_id}) durch Benutzer: {current_user.username}")
        flash('Fehler beim Löschen des Events', 'error')
    return redirect(url_for('main.events'))

@bp.route('/event/<string:event_id>/edit', methods=['GET', 'POST'])
@login_required
@member_required
def edit_event(event_id):
    g.app.logger.info(f"Event-Bearbeiten-Route aufgerufen für Event ID: {event_id} von Benutzer: {current_user.username}")
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
            cache.delete('view//events')  # Invalidate events cache
            g.app.logger.info(f"Event (ID: {event_id}) erfolgreich aktualisiert von Benutzer: {current_user.username}")
            flash('Event erfolgreich aktualisiert', 'success')
            return redirect(url_for('main.event_detail', event_id=event_id))
        else:
            g.app.logger.error(f"Fehler beim Aktualisieren des Events (ID: {event_id}) durch Benutzer: {current_user.username}")
            flash('Fehler beim Aktualisieren des Events', 'error')
    elif request.method == 'GET':
        form.title.data = event['title']
        form.description.data = event['description']
        form.date.data = datetime.strptime(event['date'], '%Y-%m-%d')
        form.location.data = event['location']
    return render_template('edit_event.html', title='Event bearbeiten', form=form)

@bp.route('/news/<string:news_id>/delete', methods=['POST'])
@login_required
@member_required
def delete_news_route(news_id):
    g.app.logger.info(f"Neuigkeiten-Lösch-Route aufgerufen für News ID: {news_id} von Benutzer: {current_user.username}")
    if delete_news_item(news_id):
        cache.delete('view//news')  # Invalidate news cache
        g.app.logger.info(f"Neuigkeit (ID: {news_id}) erfolgreich gelöscht von Benutzer: {current_user.username}")
        flash('Neuigkeit erfolgreich gelöscht', 'success')
    else:
        g.app.logger.error(f"Fehler beim Löschen der Neuigkeit (ID: {news_id}) durch Benutzer: {current_user.username}")
        flash('Fehler beim Löschen der Neuigkeit', 'error')
    return redirect(url_for('main.news'))

@bp.route('/news/<string:news_id>/edit', methods=['GET', 'POST'])
@login_required
@member_required
def edit_news(news_id):
    g.app.logger.info(f"Neuigkeiten-Bearbeiten-Route aufgerufen für News ID: {news_id} von Benutzer: {current_user.username}")
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
            cache.delete('view//news')  # Invalidate news cache
            g.app.logger.info(f"Neuigkeit (ID: {news_id}) erfolgreich aktualisiert von Benutzer: {current_user.username}")
            flash('Neuigkeit erfolgreich aktualisiert', 'success')
            return redirect(url_for('main.news_detail', news_id=news_id))
        else:
            g.app.logger.error(f"Fehler beim Aktualisieren der Neuigkeit (ID: {news_id}) durch Benutzer: {current_user.username}")
            flash('Fehler beim Aktualisieren der Neuigkeit', 'error')
    elif request.method == 'GET':
        form.title.data = news_item['title']
        form.content.data = news_item['content']
    return render_template('edit_news.html', title='Neuigkeit bearbeiten', form=form)

@bp.route('/mitgliederbereich', methods=['GET', 'POST'])
@login_required
@member_required
@cache.cached(timeout=300, unless=lambda: request.method != 'GET')
def mitgliederbereich():
    g.app.logger.info(f"Mitgliederbereich-Route aufgerufen von Benutzer: {current_user.username}")
    try:
        if request.method == 'POST':
            neues_mitglied = {
                'name': request.form['name'],
                'email': request.form['email'],
                'team': request.form['team']
            }
            push_data('mitglieder', neues_mitglied)
            cache.delete('view//mitgliederbereich')  # Invalidate cache
            g.app.logger.info(f"Neues Mitglied hinzugefügt von Benutzer: {current_user.username}")
            flash('Neues Mitglied erfolgreich hinzugefügt!', 'success')
            return redirect(url_for('main.mitgliederbereich'))
        
        mitglieder = get_data('mitglieder')
        return render_template('mitgliederbereich.html', mitglieder=mitglieder)
    except Exception as e:
        g.app.logger.error(f"Fehler im Mitgliederbereich: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@bp.route('/api/throw_data', methods=['POST'])
@login_required
@member_required
def add_throw_data():
    g.app.logger.info(f"Wurfdaten-Hinzufügen-API aufgerufen von Benutzer: {current_user.username}")
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
        cache.delete(f'view//player/{data["player_id"]}')  # Invalidate player cache
        g.app.logger.info(f"Neue Wurfdaten hinzugefügt für Spieler ID: {data['player_id']}")
        return jsonify({"message": "Wurfdaten erfolgreich hinzugefügt", "id": throw_data.id}), 201
    except ValueError as e:
        g.app.logger.error(f"Fehler beim Hinzufügen von Wurfdaten: {str(e)}")
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
            cache.delete(f'view//event/{event_id}')  # Invalidate event cache
            g.app.logger.info(f"Benutzer {current_user.username} hat sich für Event ID: {event_id} angemeldet")
            return jsonify({'success': True, 'message': 'Erfolgreich für das Event angemeldet'})
        else:
            g.app.logger.warning(f"Anmeldung fehlgeschlagen für Benutzer {current_user.username} bei Event ID: {event_id}")
            return jsonify({'success': False, 'message': 'Anmeldung fehlgeschlagen'}), 400
    except Exception as e:
        g.app.logger.error(f"Fehler bei der Event-Registrierung: {str(e)}")
        return jsonify({'success': False, 'message': 'Ein Fehler ist aufgetreten'}), 500

# Administrative Routen und zusätzliche Funktionen
@bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    current_app.logger.info(f"User {current_user.username} accessing admin dashboard. Roles: {[role.name for role in current_user.roles]}")
    total_users = User.query.count()
    current_events = Event.query.filter(Event.date >= datetime.now()).count()
    return render_template('admin/dashboard.html', total_users=total_users, current_events=current_events)

@bp.route('/generate_report')
@login_required
@admin_required
def trigger_weekly_report():
    g.app.logger.info("Wöchentlicher Berichtgenerator gestartet")
    task = generate_weekly_report.delay()
    return jsonify({"message": "Berichtgenerierung gestartet", "task_id": task.id}), 202

@bp.route('/clean_data')
@login_required
@admin_required
def trigger_data_cleanup():
    g.app.logger.info("Datenbereinigungsprozess gestartet")
    task = clean_old_data.delay()
    return jsonify({"message": "Datenbereinigung gestartet", "task_id": task.id}), 202

@bp.route('/manage_users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('Sie können Ihren eigenen Account nicht löschen.', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f'Benutzer {user.username} wurde erfolgreich gelöscht.', 'success')
    return redirect(url_for('main.manage_users'))

@bp.route('/site-statistics')
@login_required
@admin_required
@cache.cached(timeout=300)
def site_statistics():
    g.app.logger.info(f"Website-Statistiken aufgerufen von Admin: {current_user.username}")
    total_users = User.query.count()
    total_events = Event.query.count()
    total_games = Game.query.count()
    return render_template('admin/statistics.html', title='Website-Statistiken', 
                           total_users=total_users, total_events=total_events, total_games=total_games)

@bp.route('/run_task')
@login_required
@admin_required
def run_task():
    g.app.logger.info(f"Langläufige Aufgabe gestartet von Admin: {current_user.username}")
    task = long_running_task.delay()
    return jsonify({"task_id": task.id}), 202

@bp.route('/task_status/<task_id>')
@login_required
def task_status(task_id):
    task = AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Ausstehend...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('status', '')
        }
    else:
        response = {
            'state': task.state,
            'status': str(task.info)
        }
    return jsonify(response)

@bp.route('/task_interface')
@login_required
@admin_required
def task_interface():
    g.app.logger.info(f"Aufgaben-Interface aufgerufen von Admin: {current_user.username}")
    return render_template('task_interface.html')

@bp.route('/flower')
@login_required
@admin_required
def flower_dashboard():
    g.app.logger.info(f"Flower-Dashboard aufgerufen von Admin: {current_user.username}")
    return redirect('http://localhost:5555')

@bp.route('/test-firebase')
@login_required
@admin_required
def test_firebase():
    g.app.logger.info(f"Firebase-Test durchgeführt von Admin: {current_user.username}")
    try:
        ref = db.reference('/')
        ref.set({'test': 'Erfolgreich mit Firebase verbunden!'})
        return 'Firebase-Test erfolgreich!'
    except Exception as e:
        g.app.logger.error(f"Fehler beim Firebase-Test: {str(e)}")
        return 'Firebase-Test fehlgeschlagen.'

@bp.route('/test_db')
@login_required
@admin_required
def test_db():
    g.app.logger.info(f"Datenbank-Test durchgeführt von Admin: {current_user.username}")
    try:
        db.session.execute('SELECT 1')
        return 'Datenbankverbindung erfolgreich!'
    except Exception as e:
        g.app.logger.error(f"Datenbankfehler: {str(e)}")
        return 'Datenbankverbindung fehlgeschlagen.'

@bp.route('/admin/analytics')
@login_required
@admin_required
def admin_analytics():
    g.app.logger.info(f"Admin-Analytics aufgerufen von Admin: {current_user.username}")
    analytics_data = get_analytics_data()
    return render_template('admin/admin_analytics.html', data=analytics_data)

@bp.route('/edit_player/<int:player_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_player(player_id):
    player = Player.query.get_or_404(player_id)
    form = EditPlayerForm()
    form.team.choices = [(t.id, t.name) for t in Team.query.all()]
    
    if form.validate_on_submit():
        player.team_id = form.team.data
        db.session.commit()
        flash('Spielerdaten erfolgreich aktualisiert', 'success')
        return redirect(url_for('main.manage_users'))
    
    form.team.data = player.team_id
    return render_template('edit_player.html', form=form, player=player)

@bp.route('/manage_events')
@login_required
@admin_required
def manage_events():
    events = Event.query.all()
    return render_template('events.html', events=events)

# restliche Routen
@bp.route('/api/updates/<path>')
@login_required
@member_required
def get_updates(path):
    g.app.logger.info(f"Update-Anfrage für Pfad: {path} von Benutzer: {current_user.username}")
    try:
        data = get_realtime_data(path).get()
        return jsonify(data)
    except Exception as e:
        g.app.logger.error(f"Fehler beim Abrufen der Updates für {path}: {str(e)}")
        return jsonify({"error": "Ein Fehler ist aufgetreten"}), 500

@bp.route('/saisonspiele')
@login_required
@member_required
@cache.cached(timeout=300)
def saisonspiele():
    g.app.logger.info(f"Saisonspiele-Route aufgerufen von Benutzer: {current_user.username}")
    # Implementieren Sie hier die Logik für die Saisonspiele
    return render_template('saisonspiele.html', title='Saisonspiele')

@bp.route('/mitgliederbereich/neu', methods=['GET', 'POST'])
@login_required
@member_required
def neues_mitglied():
    g.app.logger.info(f"Neues-Mitglied-Route aufgerufen von Benutzer: {current_user.username}")
    if request.method == 'POST':
        neues_mitglied = {
            'name': request.form['name'],
            'email': request.form['email'],
            'team': request.form['team']
        }
        # Hier die Logik zum Hinzufügen des neuen Mitglieds implementieren
        flash('Neues Mitglied erfolgreich hinzugefügt!', 'success')
        return redirect(url_for('main.mitgliederbereich'))
    return render_template('neues_mitglied.html', title='Neues Mitglied hinzufügen')

@bp.route('/termine')
@login_required
@member_required
@cache.cached(timeout=300)
def termine():
    """Display all appointments."""
    g.app.logger.info(f"Termine-Route aufgerufen von Benutzer: {current_user.username}")
    termine = get_data('termine')
    return render_template('events.html', termine=termine)

@bp.route('/termine/neu', methods=['GET', 'POST'])
@login_required
@member_required
def neuer_termin():
    """Handle creation of a new appointment."""
    g.app.logger.info(f"Neuer-Termin-Route aufgerufen von Benutzer: {current_user.username}")
    if request.method == 'POST':
        termin_data = {
            'titel': request.form['titel'],
            'datum': request.form['datum'],
            'uhrzeit': request.form['uhrzeit'],
            'beschreibung': request.form['beschreibung'],
            'typ': request.form['typ']
        }
        push_data('termine', termin_data)
        cache.delete('view//termine')  # Invalidate cache
        g.app.logger.info(f"Neuer Termin hinzugefügt von Benutzer: {current_user.username}")
        flash('Neuer Termin erfolgreich hinzugefügt!')
        return redirect(url_for('main.termine'))
    return render_template('neuer_termin.html')

@bp.route('/training/statistics')
@login_required
@member_required
@cache.cached(timeout=300)
def training_statistics():
    """Display training statistics."""
    g.app.logger.info(f"Training-Statistiken aufgerufen von Benutzer: {current_user.username}")
    stats = db.session.query(
        func.count(Game.id).label('total_games'),
        func.sum(Game.winner_id == current_user.id).label('won_games'),
        func.avg(case([(Game.player1_id == current_user.id, Game.player1_score),
                       (Game.player2_id == current_user.id, Game.player2_score)],
                      else_=None)).label('avg_score'),
        func.max(case([(Game.player1_id == current_user.id, Game.player1_score),
                       (Game.player2_id == current_user.id, Game.player2_score)],
                      else_=None)).label('best_score')
    ).filter((Game.player1_id == current_user.id) | (Game.player2_id == current_user.id)).first()

    return render_template('statistics.html', stats=stats)

@bp.route('/training/neu', methods=['GET', 'POST'])
@login_required
@member_required
def neues_training():
    """Handle creation of a new training session."""
    g.app.logger.info(f"Neues-Training-Route aufgerufen von Benutzer: {current_user.username}")
    if request.method == 'POST':
        training_data = {
            'datum': request.form['datum'],
            'uhrzeit': request.form['uhrzeit'],
            'dauer': request.form['dauer'],
            'thema': request.form['thema'],
            'trainer': request.form['trainer']
        }
        push_data('trainings', training_data)
        cache.delete('view//training')  # Invalidate cache
        g.app.logger.info(f"Neues Training hinzugefügt von Benutzer: {current_user.username}")
        flash('Neues Training erfolgreich hinzugefügt!')
        return redirect(url_for('main.training'))
    return render_template('neues_training.html')

# Gastspieler Bereich
@bp.route('/oeffentliche_turniere')
@login_required
@cache.cached(timeout=300)
def oeffentliche_turniere():
    """Display public tournaments."""
    g.app.logger.info(f"Öffentliche-Turniere-Route aufgerufen von Benutzer: {current_user.username}")
    # Implementieren Sie hier die Logik für öffentliche Turniere
    return render_template('oeffentliche_turniere.html', title='Öffentliche Turniere')

@bp.route('/trainingsangebote')
@login_required
@cache.cached(timeout=300)
def trainingsangebote():
    """Display training offers."""
    g.app.logger.info(f"Trainingsangebote-Route aufgerufen von Benutzer: {current_user.username}")
    # Implementieren Sie hier die Logik für Trainingsangebote
    return render_template('trainingsangebote.html', title='Trainingsangebote')

@bp.route('/gastforum')
@login_required
@cache.cached(timeout=300)
def gastforum():
    """Display guest forum."""
    g.app.logger.info(f"Gastforum-Route aufgerufen von Benutzer: {current_user.username}")
    # Implementieren Sie hier die Logik für das Gastforum
    return render_template('gastforum.html', title='Gastforum')

@bp.route('/persoenliche_statistiken')
@login_required
def persoenliche_statistiken():
    """Display personal statistics."""
    g.app.logger.info(f"Persönliche-Statistiken-Route aufgerufen von Benutzer: {current_user.username}")
    # Implementieren Sie hier die Logik für persönliche Statistiken
    return render_template('persoenliche_statistiken.html', title='Persönliche Statistiken')

@bp.route('/marktplatz/neues_angebot', methods=['GET', 'POST'])
@login_required
def neues_angebot():
    """Handle creation of a new marketplace offer."""
    g.app.logger.info(f"Neues-Angebot-Route aufgerufen von Benutzer: {current_user.username}")
    if request.method == 'POST':
        angebot_data = {
            'titel': request.form['titel'],
            'beschreibung': request.form['beschreibung'],
            'preis': float(request.form['preis']),
            'verkäufer': current_user.name,
            'datum': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        push_data('marktplatz_angebote', angebot_data)
        cache.delete('view//marktplatz')  # Cache invalidieren
        g.app.logger.info(f"Neues Marktplatz-Angebot erstellt von Benutzer: {current_user.username}")
        flash('Neues Angebot erfolgreich erstellt!')
        return redirect(url_for('main.marktplatz'))
    return render_template('neues_angebot.html')

@bp.route('/test_celery/<int:x>/<int:y>')
def test_celery(x, y):
    g.app.logger.info(f"Celery-Test aufgerufen mit Parametern x={x}, y={y}")
    task = example_task.delay(x, y)
    return jsonify({"task_id": task.id, "message": "Task wurde gestartet"})

@bp.route('/test')
def test():
    g.app.logger.info("Test-Route aufgerufen")
    return "Test route works!"

@bp.route('/test-main')
def test_main():
    return "Main Blueprint Test"

@bp.route('/debug-test')
def debug_test():
    return "Debug-Test erfolgreich!"

@bp.route('/add/<int:x>/<int:y>')
def add(x, y):
    """Add two numbers using a Celery task."""
    g.app.logger.info(f"Addition-Route aufgerufen mit Parametern x={x}, y={y}")
    task = example_task.delay(x, y)
    return jsonify({"task_id": task.id}), 202

@bp.route('/send_email')
def trigger_email():
    """Trigger sending a test email."""
    g.app.logger.info("E-Mail-Trigger-Route aufgerufen")
    task = send_email.delay("empfaenger@example.com", "Test", "Dies ist eine Test-E-Mail")
    return jsonify({"task_id": task.id}), 202

# Fehlerbehandlung
@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@bp.errorhandler(Exception)
def handle_exception(e):
    """Handle general exceptions."""
    if isinstance(e, HTTPException):
        return jsonify(error=str(e)), e.code
    g.app.logger.error(f"Unbehandelte Ausnahme: {str(e)}")
    return jsonify(error="Interner Serverfehler"), 500

# Debug-Ausgabe der registrierten Routen
def register_routes(app):
    if app.debug:
        print("Registrierte Routen in main/routes.py:")
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith('main.'):
                print(f"{rule.endpoint}: {rule.rule}")
