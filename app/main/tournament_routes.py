from app.main import bp
from flask import request, jsonify, abort, g
from flask_login import login_required, current_user
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from app.models import Tournament, Match, Team
from app.extensions import db, cache, limiter
from app.schemas import TournamentSchema
from app.decorators import admin_required
from app.tournament_logic import generate_round_robin_schedule, update_tournament_standings
from app.socket_events import socketio

tournament_schema = TournamentSchema()
tournaments_schema = TournamentSchema(many=True)

@bp.before_request
def before_request():
    g.app = bp.app

@bp.route('/tournaments/tournament', methods=['POST'])
@login_required
@admin_required
@limiter.limit("5 pro Minute")
def create_tournament():
    try:
        data = tournament_schema.load(request.json)
        new_tournament = Tournament(**data)
        db.session.add(new_tournament)
        db.session.commit()
        cache.delete('all_tournaments')
        socketio.emit('tournament_update', tournament_schema.dump(new_tournament), broadcast=True)
        g.app.logger.info(f"Neues Turnier erstellt: {new_tournament.id}")
        return tournament_schema.jsonify(new_tournament), 201
    except ValidationError as err:
        g.app.logger.error(f"Validierungsfehler: {err.messages}")
        abort(400, description=err.messages)
    except IntegrityError:
        db.session.rollback()
        g.app.logger.error("IntegrityError beim Erstellen des Turniers")
        abort(400, description="Turnier konnte aufgrund von Integritätsbeschränkungen nicht erstellt werden")

@bp.route('/tournaments/tournaments', methods=['GET'])
@cache.cached(timeout=300, key_prefix='all_tournaments')
def get_tournaments():
    all_tournaments = Tournament.query.all()
    return jsonify(tournaments_schema.dump(all_tournaments))

@bp.route('/tournaments/tournament/<int:id>', methods=['GET'])
@cache.cached(timeout=300, key_prefix='tournament')
def get_tournament(id):
    tournament = Tournament.query.get_or_404(id)
    return tournament_schema.jsonify(tournament)

@bp.route('/tournaments/tournament/<int:id>', methods=['PUT'])
@login_required
@admin_required
@limiter.limit("10 pro Minute")
def update_tournament(id):
    tournament = Tournament.query.get_or_404(id)
    try:
        data = tournament_schema.load(request.json, partial=True)
        for key, value in data.items():
            setattr(tournament, key, value)
        db.session.commit()
        cache.delete('all_tournaments')
        cache.delete(f'tournament_{id}')
        socketio.emit('tournament_update', tournament_schema.dump(tournament), broadcast=True)
        g.app.logger.info(f"Turnier aktualisiert: {id}")
        return tournament_schema.jsonify(tournament)
    except ValidationError as err:
        g.app.logger.error(f"Validierungsfehler: {err.messages}")
        abort(400, description=err.messages)
    except IntegrityError:
        db.session.rollback()
        g.app.logger.error(f"IntegrityError beim Aktualisieren des Turniers: {id}")
        abort(400, description="Turnier konnte aufgrund von Integritätsbeschränkungen nicht aktualisiert werden")

@bp.route('/tournaments/tournament/<int:id>', methods=['DELETE'])
@login_required
@admin_required
@limiter.limit("5 pro Minute")
def delete_tournament(id):
    tournament = Tournament.query.get_or_404(id)
    db.session.delete(tournament)
    db.session.commit()
    cache.delete('all_tournaments')
    cache.delete(f'tournament_{id}')
    socketio.emit('tournament_delete', {'id': id}, broadcast=True)
    g.app.logger.info(f"Turnier gelöscht: {id}")
    return '', 204

@bp.route('/tournaments/tournament/<int:id>/generate_schedule', methods=['POST'])
@login_required
@admin_required
def generate_tournament_schedule(id):
    tournament = Tournament.query.get_or_404(id)
    
    teams = [team.name for team in tournament.teams]
    schedule = generate_round_robin_schedule(teams)

    for round_num, round_matches in enumerate(schedule):
        for match in round_matches:
            new_match = Match(
                tournament_id=tournament.id,
                round=round_num + 1,
                team1=match[0],
                team2=match[1]
            )
            db.session.add(new_match)

    db.session.commit()

    socketio.emit('schedule_update', {'tournament_id': id}, broadcast=True)

    return jsonify({"message": "Turnierzeitplan erfolgreich generiert"}), 201

@bp.route('/tournaments/match/<int:id>/update_result', methods=['POST'])
@login_required
@admin_required
def update_match_result(id):
    match = Match.query.get_or_404(id)

    data = request.json
    match.team1_score = data.get('team1_score')
    match.team2_score = data.get('team2_score')
    match.status = 'Completed'

    db.session.commit()

    update_tournament_standings(match.tournament_id)

    socketio.emit('match_update', {'match_id': id, 'result': data}, broadcast=True)

    return jsonify({"message": "Das Ergebnis des Spiels wurde erfolgreich aktualisiert"}), 200

@bp.route('/tournaments/tournament/<int:id>/standings', methods=['GET'])
def get_tournament_standings(id):
    tournament = Tournament.query.get_or_404(id)

    standings = tournament.teams.order_by(Team.points.desc(), Team.wins.desc()).all()
    
    result = [{'team': team.name, 'points': team.points, 'games_played': team.games_played,
               'wins': team.wins, 'draws': team.draws, 'losses': team.losses} for team in standings]

    return jsonify(result)

@bp.route('/tournaments/tournament/<int:id>/register', methods=['POST'])
@login_required
def register_for_tournament(id):
    tournament = Tournament.query.get_or_404(id)
    
    if tournament.is_full():
        abort(400, description="Das Turnier ist bereits voll")
    
    if current_user in tournament.participants:
        abort(400, description="Sie sind bereits für dieses Turnier registriert")
    
    tournament.participants.append(current_user)
    
    db.session.commit()
    
    socketio.emit('new_participant', {'tournament_id': id, 'user_id': current_user.id}, broadcast=True)

    g.app.logger.info(f"Benutzer {current_user.id} für Turnier {id} registriert")
    
    return jsonify({'success': True, 'message': 'Erfolgreich für das Turnier registriert'}), 200
