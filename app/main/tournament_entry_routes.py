from flask import request, jsonify, abort, g
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from app.main import bp
from app.models import db, TournamentEntry
from app.schemas import TournamentEntrySchema
from app.decorators import login_required, admin_required
from app.extensions import cache, limiter

entry_schema = TournamentEntrySchema()
entries_schema = TournamentEntrySchema(many=True)

@bp.before_request
def before_request():
    g.app = bp.app

@bp.route('/entry', methods=['POST'])
@login_required
@limiter.limit("5 pro Minute")
def create_entry():
    try:
        data = entry_schema.load(request.json)
        new_entry = TournamentEntry(**data)
        db.session.add(new_entry)
        db.session.commit()
        cache.delete('all_entries')
        g.app.logger.info(f"Neuer Turniereintrag erstellt: {new_entry.id}")
        return entry_schema.jsonify(new_entry), 201
    except ValidationError as err:
        g.app.logger.error(f"Validierungsfehler: {err.messages}")
        abort(400, description=err.messages)
    except IntegrityError:
        db.session.rollback()
        g.app.logger.error("IntegrityError beim Erstellen des Turniereintrags")
        abort(400, description="Turniereintrag konnte aufgrund von Integritätsbeschränkungen nicht erstellt werden")

@bp.route('/entries', methods=['GET'])
@cache.cached(timeout=300, key_prefix='all_entries')
def get_entries():
    all_entries = TournamentEntry.query.all()
    result = entries_schema.dump(all_entries)
    return jsonify(result)

@bp.route('/entry/<int:id>', methods=['GET'])
@cache.cached(timeout=300, key_prefix='entry')
def get_entry(id):
    entry = TournamentEntry.query.get(id)
    if entry is None:
        abort(404, description="Turniereintrag nicht gefunden")
    return entry_schema.jsonify(entry)

@bp.route('/entry/<int:id>', methods=['PUT'])
@login_required
@admin_required
@limiter.limit("10 pro Minute")
def update_entry(id):
    entry = TournamentEntry.query.get(id)
    if entry is None:
        abort(404, description="Turniereintrag nicht gefunden")
    try:
        data = entry_schema.load(request.json, partial=True)
        for key, value in data.items():
            setattr(entry, key, value)
        db.session.commit()
        cache.delete('all_entries')
        cache.delete(f'entry_{id}')
        g.app.logger.info(f"Turniereintrag aktualisiert: {id}")
        return entry_schema.jsonify(entry)
    except ValidationError as err:
        g.app.logger.error(f"Validierungsfehler: {err.messages}")
        abort(400, description=err.messages)
    except IntegrityError:
        db.session.rollback()
        g.app.logger.error(f"IntegrityError beim Aktualisieren des Turniereintrags: {id}")
        abort(400, description="Turniereintrag konnte aufgrund von Integritätsbeschränkungen nicht aktualisiert werden")

@bp.route('/entry/<int:id>', methods=['DELETE'])
@login_required
@admin_required
@limiter.limit("5 pro Minute")
def delete_entry(id):
    entry = TournamentEntry.query.get(id)
    if entry is None:
        abort(404, description="Turniereintrag nicht gefunden")
    try:
        db.session.delete(entry)
        db.session.commit()
        cache.delete('all_entries')
        cache.delete(f'entry_{id}')
        g.app.logger.info(f"Turniereintrag gelöscht: {id}")
        return '', 204
    except IntegrityError:
        db.session.rollback()
        g.app.logger.error(f"IntegrityError beim Löschen des Turniereintrags: {id}")
        abort(400, description="Turniereintrag konnte aufgrund von Integritätsbeschränkungen nicht gelöscht werden")
