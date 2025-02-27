from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from urllib.parse import urlparse
from app import db, limiter
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models.user import User

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Ungültiger Benutzername oder Passwort', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        
        if not next_page or urlparse(next_page).netloc != '':
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
        user.set_password(form.password.data)
        
        db.session.add(user)
        
        try:
            db.session.commit()
            flash('Glückwunsch, Sie sind jetzt registriert!', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.', 'danger')
    
    return render_template('auth/register.html', title='Registrieren', form=form)
