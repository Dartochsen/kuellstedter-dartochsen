from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    is_member = fields.Bool()
    is_admin = fields.Bool()

class PlayerSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    average_score = fields.Float()
    games_played = fields.Int()
    wins = fields.Int()
    losses = fields.Int()

class TournamentSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    date = fields.DateTime(required=True)
    location = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    organizer_id = fields.Int(required=True)
    phase = fields.Str(validate=validate.OneOf(['Registration', 'In Progress', 'Completed']))
    format = fields.Str(required=True, validate=validate.OneOf(['1vs1', 'team-based']))
    type = fields.Str(required=True, validate=validate.OneOf(['tournament', 'league', 'ladder']))

class StageSchema(Schema):
    id = fields.Int(dump_only=True)
    tournament_id = fields.Int(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    order = fields.Int(required=True, validate=validate.Range(min=1))
    start_date = fields.DateTime(required=True)
    end_date = fields.DateTime(required=True)
    status = fields.Str(validate=validate.OneOf(['Pending', 'In Progress', 'Completed']))

class MatchSchema(Schema):
    id = fields.Int(dump_only=True)
    stage_id = fields.Int(required=True)
    player1_id = fields.Int(required=True)
    player2_id = fields.Int(required=True)
    winner_id = fields.Int()
    start_time = fields.DateTime()
    end_time = fields.DateTime()
    status = fields.Str()

class TeamSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    tournament_id = fields.Int(required=True)
    captain_id = fields.Int(required=True)

class TournamentEntrySchema(Schema):
    id = fields.Int(dump_only=True)
    tournament_id = fields.Int(required=True)
    player_id = fields.Int(required=True)
    team_id = fields.Int()
    registration_date = fields.DateTime(dump_only=True)
    status = fields.Str(validate=validate.OneOf(['Pending', 'Approved', 'Rejected']))

class MatchSchema(Schema):
    id = fields.Int(dump_only=True)
    stage_id = fields.Int(required=True)
    player1_id = fields.Int(required=True)
    player2_id = fields.Int(required=True)
    winner_id = fields.Int()
    start_time = fields.DateTime()
    end_time = fields.DateTime()
    status = fields.Str(validate=validate.OneOf(['Scheduled', 'In Progress', 'Completed']))
# Fügen Sie hier weitere Schemas hinzu, wenn nötig
