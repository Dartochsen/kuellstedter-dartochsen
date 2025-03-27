from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models.question import Question
from app.extensions import db, cache, limiter
from app.forms import QuestionForm  # Sie müssen dieses Formular noch erstellen

bp = Blueprint('questions', __name__)

@bp.route('/')
@cache.cached(timeout=300)
def index():
    questions = Question.query.order_by(Question.created_at.desc()).all()
    return render_template('questions/index.html', questions=questions)

@bp.route('/<int:id>')
@cache.cached(timeout=300)
def show(id):
    question = Question.query.get_or_404(id)
    return render_template('questions/show.html', question=question)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per minute")
def create():
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(title=form.title.data, content=form.content.data)
        db.session.add(question)
        db.session.commit()
        cache.delete('view//questions/')
        current_app.logger.info(f"Neue Frage erstellt: {question.id}")
        flash('Ihre Frage wurde erfolgreich erstellt.', 'success')
        return redirect(url_for('questions.show', id=question.id))
    return render_template('questions/create.html', form=form)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per minute")
def edit(id):
    question = Question.query.get_or_404(id)
    form = QuestionForm(obj=question)
    if form.validate_on_submit():
        question.title = form.title.data
        question.content = form.content.data
        db.session.commit()
        cache.delete('view//questions/')
        cache.delete(f'view//questions/{id}')
        current_app.logger.info(f"Frage aktualisiert: {question.id}")
        flash('Ihre Frage wurde erfolgreich aktualisiert.', 'success')
        return redirect(url_for('questions.show', id=question.id))
    return render_template('questions/edit.html', form=form, question=question)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def delete(id):
    question = Question.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    cache.delete('view//questions/')
    cache.delete(f'view//questions/{id}')
    current_app.logger.info(f"Frage gelöscht: {id}")
    flash('Ihre Frage wurde erfolgreich gelöscht.', 'success')
    return redirect(url_for('questions.index'))
