from flask import request, jsonify, abort, g
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from app.main import bp
from app.models import db, Stage
from app.schemas import StageSchema
from flask_login import login_required
from app.decorators import admin_required
from app.extensions import cache, limiter

stage_schema = StageSchema()
stages_schema = StageSchema(many=True)

@bp.before_request
def before_request():
    g.app = bp.app

@bp.route('/stage', methods=['POST'])
@login_required
@admin_required
@limiter.limit("5 per minute")
def create_stage():
    try:
        data = stage_schema.load(request.json)
        new_stage = Stage(**data)
        db.session.add(new_stage)
        db.session.commit()
        cache.delete('all_stages')
        g.app.logger.info(f"New stage created: {new_stage.id}")
        return stage_schema.jsonify(new_stage), 201
    except ValidationError as err:
        g.app.logger.error(f"Validation error: {err.messages}")
        abort(400, description=err.messages)
    except IntegrityError:
        db.session.rollback()
        g.app.logger.error("IntegrityError while creating stage")
        abort(400, description="Stage could not be created due to integrity constraints")

@bp.route('/stages', methods=['GET'])
@cache.cached(timeout=300, key_prefix='all_stages')
def get_stages():
    all_stages = Stage.query.all()
    result = stages_schema.dump(all_stages)
    return jsonify(result)

@bp.route('/stage/<int:id>', methods=['GET'])
@cache.cached(timeout=300, key_prefix='stage')
def get_stage(id):
    stage = Stage.query.get(id)
    if stage is None:
        abort(404, description="Stage not found")
    return stage_schema.jsonify(stage)

@bp.route('/stage/<int:id>', methods=['PUT'])
@login_required
@admin_required
@limiter.limit("10 per minute")
def update_stage(id):
    stage = Stage.query.get(id)
    if stage is None:
        abort(404, description="Stage not found")
    try:
        data = stage_schema.load(request.json, partial=True)
        for key, value in data.items():
            setattr(stage, key, value)
        db.session.commit()
        cache.delete('all_stages')
        cache.delete(f'stage_{id}')
        g.app.logger.info(f"Stage updated: {id}")
        return stage_schema.jsonify(stage)
    except ValidationError as err:
        g.app.logger.error(f"Validation error: {err.messages}")
        abort(400, description=err.messages)
    except IntegrityError:
        db.session.rollback()
        g.app.logger.error(f"IntegrityError while updating stage: {id}")
        abort(400, description="Stage could not be updated due to integrity constraints")

@bp.route('/stage/<int:id>', methods=['DELETE'])
@login_required
@admin_required
@limiter.limit("5 per minute")
def delete_stage(id):
    stage = Stage.query.get(id)
    if stage is None:
        abort(404, description="Stage not found")
    try:
        db.session.delete(stage)
        db.session.commit()
        cache.delete('all_stages')
        cache.delete(f'stage_{id}')
        g.app.logger.info(f"Stage deleted: {id}")
        return '', 204
    except IntegrityError:
        db.session.rollback()
        g.app.logger.error(f"IntegrityError while deleting stage: {id}")
        abort(400, description="Stage could not be deleted due to integrity constraints")
