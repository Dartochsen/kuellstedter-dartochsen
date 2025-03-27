from flask import request, jsonify, abort, g
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from app.main import bp
from app.models import db, Team
from app.schemas import TeamSchema
from app.decorators import login_required, admin_required
from app.extensions import cache, limiter

team_schema = TeamSchema()
teams_schema = TeamSchema(many=True)

@bp.before_request
def before_request():
    g.app = bp.app

@bp.route('/team', methods=['POST'])
@login_required
@admin_required
@limiter.limit("5 per minute")
def create_team():
    try:
        data = team_schema.load(request.json)
        new_team = Team(**data)
        db.session.add(new_team)
        db.session.commit()
        cache.delete('all_teams')
        g.app.logger.info(f"New team created: {new_team.id}")
        return team_schema.jsonify(new_team), 201
    except ValidationError as err:
        g.app.logger.error(f"Validation error: {err.messages}")
        abort(400, description=err.messages)
    except IntegrityError:
        db.session.rollback()
        g.app.logger.error("IntegrityError while creating team")
        abort(400, description="Team could not be created due to integrity constraints")

@bp.route('/teams', methods=['GET'])
@cache.cached(timeout=300, key_prefix='all_teams')
def get_teams():
    all_teams = Team.query.all()
    result = teams_schema.dump(all_teams)
    return jsonify(result)

@bp.route('/team/<int:id>', methods=['GET'])
@cache.cached(timeout=300, key_prefix='team')
def get_team(id):
    team = Team.query.get(id)
    if team is None:
        abort(404, description="Team not found")
    return team_schema.jsonify(team)

@bp.route('/team/<int:id>', methods=['PUT'])
@login_required
@admin_required
@limiter.limit("10 per minute")
def update_team(id):
    team = Team.query.get(id)
    if team is None:
        abort(404, description="Team not found")
    try:
        data = team_schema.load(request.json, partial=True)
        for key, value in data.items():
            setattr(team, key, value)
        db.session.commit()
        cache.delete('all_teams')
        cache.delete(f'team_{id}')
        g.app.logger.info(f"Team updated: {id}")
        return team_schema.jsonify(team)
    except ValidationError as err:
        g.app.logger.error(f"Validation error: {err.messages}")
        abort(400, description=err.messages)
    except IntegrityError:
        db.session.rollback()
        g.app.logger.error(f"IntegrityError while updating team: {id}")
        abort(400, description="Team could not be updated due to integrity constraints")

@bp.route('/team/<int:id>', methods=['DELETE'])
@login_required
@admin_required
@limiter.limit("5 per minute")
def delete_team(id):
    team = Team.query.get(id)
    if team is None:
        abort(404, description="Team not found")
    try:
        db.session.delete(team)
        db.session.commit()
        cache.delete('all_teams')
        cache.delete(f'team_{id}')
        g.app.logger.info(f"Team deleted: {id}")
        return '', 204
    except IntegrityError:
        db.session.rollback()
        g.app.logger.error(f"IntegrityError while deleting team: {id}")
        abort(400, description="Team could not be deleted due to integrity constraints")
