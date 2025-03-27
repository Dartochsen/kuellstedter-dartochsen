from flask import request, jsonify, abort, g
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from app.main import bp
from app.models import db, Match
from app.schemas import MatchSchema
from app.decorators import login_required, admin_required
from app import CustomError
from app.extensions import cache, limiter

match_schema = MatchSchema()
matches_schema = MatchSchema(many=True)

@bp.before_request
def before_request():
    g.app = bp.app

@bp.route('/match', methods=['POST'])
@login_required
@admin_required
@limiter.limit("5 per minute")
def create_match():
    try:
        data = match_schema.load(request.json)
        new_match = Match(**data)
        db.session.add(new_match)
        db.session.commit()
        cache.delete('all_matches')  # Invalidate cache
        g.app.logger.info(f"New match created: {new_match.id}")
        return match_schema.jsonify(new_match), 201
    except ValidationError as err:
        g.app.logger.error(f"Validation error: {err.messages}")
        abort(400, description=err.messages)
    except IntegrityError:
        db.session.rollback()
        g.app.logger.error("IntegrityError while creating match")
        abort(400, description="Match could not be created due to integrity constraints")

@bp.route('/matches', methods=['GET'])
@cache.cached(timeout=300, key_prefix='all_matches')
def get_matches():
    all_matches = Match.query.all()
    result = matches_schema.dump(all_matches)
    return jsonify(result)

@bp.route('/match/<int:id>', methods=['GET'])
@cache.cached(timeout=300, key_prefix='match')
def get_match(id):
    match = Match.query.get(id)
    if match is None:
        abort(404, description="Match not found")
    return match_schema.jsonify(match)

@bp.route('/match/<int:id>', methods=['PUT'])
@login_required
@admin_required
@limiter.limit("10 per minute")
def update_match(id):
    match = Match.query.get(id)
    if match is None:
        abort(404, description="Match not found")
    try:
        data = match_schema.load(request.json, partial=True)
        for key, value in data.items():
            setattr(match, key, value)
        db.session.commit()
        cache.delete('all_matches')  # Invalidate cache
        cache.delete(f'match_{id}')  # Invalidate specific match cache
        g.app.logger.info(f"Match updated: {id}")
        return match_schema.jsonify(match)
    except ValidationError as err:
        g.app.logger.error(f"Validation error: {err.messages}")
        abort(400, description=err.messages)
    except IntegrityError:
        db.session.rollback()
        g.app.logger.error(f"IntegrityError while updating match: {id}")
        abort(400, description="Match could not be updated due to integrity constraints")

@bp.route('/match/<int:id>', methods=['DELETE'])
@login_required
@admin_required
@limiter.limit("5 per minute")
def delete_match(id):
    match = Match.query.get(id)
    if match is None:
        abort(404, description="Match not found")
    try:
        db.session.delete(match)
        db.session.commit()
        cache.delete('all_matches')  # Invalidate cache
        cache.delete(f'match_{id}')  # Invalidate specific match cache
        g.app.logger.info(f"Match deleted: {id}")
        return '', 204
    except IntegrityError:
        db.session.rollback()
        g.app.logger.error(f"IntegrityError while deleting match: {id}")
        abort(400, description="Match could not be deleted due to integrity constraints")
