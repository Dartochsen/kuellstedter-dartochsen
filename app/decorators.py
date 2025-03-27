from functools import wraps
from flask import abort, current_app
from flask_login import current_user, login_required

def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            log_access_attempt(roles)
            if not any(current_user.has_role(role) for role in roles):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def member_required(f):
    return role_required('member', 'admin')(f)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            current_app.logger.info(f"User not authenticated")
            abort(403)
        if not current_user.has_role('admin'):
            current_app.logger.info(f"User {current_user.username} does not have admin role. Roles: {current_user.roles}")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def log_access_attempt(roles):
    current_app.logger.info(f"Access attempt by user {current_user.username}. User roles: {[role.name for role in current_user.roles]}, Required roles: {roles}")

__all__ = ['login_required', 'role_required', 'member_required', 'admin_required']
