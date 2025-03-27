from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.admin import bp
from app.models.user import User
from app.extensions import db

@bp.route('/login')
def login():
    # Redirect to auth.login, as admin login should use the same mechanism
    return redirect(url_for('auth.login'))

@bp.route('/logout')
def logout():
    # Redirect to auth.logout
    return redirect(url_for('auth.logout'))

@bp.route('/register')
def register():
    # Admin registration should be a protected operation
    return redirect(url_for('auth.register'))

@bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash('Sie haben keine Berechtigung für diese Seite.', 'danger')
        return redirect(url_for('main.index'))
    return render_template('admin/dashboard.html')

@bp.route('/users')
@login_required
def user_list():
    if not current_user.is_admin:
        flash('Sie haben keine Berechtigung für diese Seite.', 'danger')
        return redirect(url_for('main.index'))
    users = User.query.all()
    return render_template('admin/user_list.html', users=users)
