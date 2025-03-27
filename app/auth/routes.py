from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user
from urllib.parse import urlparse, urljoin
from app.auth import bp
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models.user import User
from app.extensions import db, limiter
from sqlalchemy.exc import IntegrityError
from app.services.mail_service import send_password_reset_email
import logging

logger = logging.getLogger(__name__)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data)
        if user is None or not user.check_password(form.password.data):
            logger.warning(f"Fehlgeschlagener Anmeldeversuch für Benutzer: {form.username.data}")
            flash('Ungültiger Benutzername oder Passwort', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        logger.info(f"Benutzer {user.username} hat sich erfolgreich angemeldet")
        next_page = request.args.get('next')
        if not next_page or not is_safe_url(next_page):
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Anmelden', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    flash('Sie wurden erfolgreich abgemeldet.', 'success')
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.password = form.password.data
        
        db.session.add(user)
        
        try:
            db.session.commit()
            logger.info(f"Neuer Benutzer registriert: {user.username}")
            flash('Glückwunsch, Sie sind jetzt registriert!', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            logger.error(f"Registrierung fehlgeschlagen für Benutzer: {form.username.data}")
            flash('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.', 'danger')
    
    return render_template('auth/register.html', title='Registrieren', form=form)

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Überprüfen Sie Ihre E-Mail für die Anweisungen zum Zurücksetzen Ihres Passworts', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', title='Passwort zurücksetzen', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Ihr Passwort wurde zurückgesetzt.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)
