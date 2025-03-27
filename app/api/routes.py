from flask import jsonify, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.api import bp
from app.models.user import User
from app.extensions import db, limiter
from sqlalchemy.exc import IntegrityError
from marshmallow import Schema, fields, ValidationError

class UserSchema(Schema):
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True)

@bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    user = User.query.filter_by(username=data.get('username')).first()
    if user and user.check_password(data.get('password')):
        login_user(user)
        return jsonify({"message": "Logged in successfully.", "user_id": user.id}), 200
    return jsonify({"error": "Invalid username or password"}), 401

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully."}), 200

@bp.route('/register', methods=['POST'])
@limiter.limit("3 per hour")
def register():
    schema = UserSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"error": err.messages}), 422

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 409
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already exists"}), 409

    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    try:
        db.session.commit()
        return jsonify({"message": "User registered successfully.", "user_id": user.id}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "An error occurred while registering the user"}), 500

@bp.route('/user', methods=['GET'])
@login_required
def get_user():
    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }), 200

@bp.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded", "message": str(e.description)}), 429
