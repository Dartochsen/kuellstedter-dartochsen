from flask import current_app
from app.extensions import db, bcrypt
from flask_login import UserMixin
from datetime import datetime
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

# Zwischentabelle für die Beziehung zwischen User und Role
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'))
)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f'<Role {self.name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    _password_hash = db.Column('password_hash', db.String(128), nullable=False)
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Beziehung zu Rollen (Viele-zu-Viele)
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy='dynamic'))

    # Andere Beziehungen bleiben unverändert
    player_profile = relationship('Player', back_populates='user', uselist=False, lazy='joined')
    organized_events = relationship('Event', back_populates='organizer', lazy='dynamic')
    participated_events = relationship('Event', secondary='event_participants', back_populates='participants', lazy='dynamic')
    forum_themen = relationship('ForumThema', back_populates='autor', lazy='dynamic')
    forum_antworten = relationship('ForumAntwort', back_populates='autor', lazy='dynamic')
    posts = relationship('Post', back_populates='author', lazy='dynamic')
    activities = relationship('Activity', back_populates='user', lazy='dynamic')
    organized_tournaments = relationship('Tournament', back_populates='organizer', lazy='dynamic')

    # Bestehende Methoden bleiben unverändert
    @hybrid_property
    def password(self):
        return self._password_hash

    @password.setter
    def password(self, plain_text_password):
        self._password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password(self, plain_text_password):
        return bcrypt.check_password_hash(self._password_hash, plain_text_password)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f'<User {self.username}>'

    def avatar(self, size):
        # Implement avatar logic here (e.g., using Gravatar)
        pass

    @property
    def is_active(self):
        return True

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

    @property
    def is_member(self):
        return self.has_role('member') or self.has_role('admin')

    @property
    def is_admin(self):
        return self.has_role('admin')

    @property
    def is_trainer(self):
        return self.has_role('trainer')

    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email).first()
