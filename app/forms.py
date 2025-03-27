from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, DateField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp
from app.models.user import User
from datetime import date

class LoginForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired(), Length(min=3, max=64)], render_kw={"placeholder": "Benutzername"})
    password = PasswordField('Passwort', validators=[DataRequired(), Length(min=8)], render_kw={"placeholder": "Passwort"})
    remember_me = BooleanField('Angemeldet bleiben')
    submit = SubmitField('Anmelden')

class RegistrationForm(FlaskForm):
    username = StringField('Benutzername', validators=[
        DataRequired(),
        Length(min=3, max=64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Benutzernamen dürfen nur Buchstaben, Zahlen, Punkte oder Unterstriche enthalten')
    ], render_kw={"class": "form-label text-dark"})
    email = StringField('E-Mail', validators=[DataRequired(), Email(), Length(max=120)], render_kw={"class": "form-label text-dark"})
    password = PasswordField('Passwort', validators=[
        DataRequired(),
        Length(min=8, message="Das Passwort muss mindestens 8 Zeichen lang sein."),
        Regexp('^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', message="Das Passwort muss mindestens einen Großbuchstaben, einen Kleinbuchstaben, eine Zahl und ein Sonderzeichen enthalten.")
    ], render_kw={"class": "form-label text-dark"})
    password2 = PasswordField('Passwort wiederholen', validators=[DataRequired(), EqualTo('password', message='Passwörter müssen übereinstimmen')], render_kw={"class": "form-label text-dark"})
    submit = SubmitField('Registrieren')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Dieser Benutzername ist bereits vergeben. Bitte wählen Sie einen anderen.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Diese E-Mail-Adresse ist bereits registriert. Bitte verwenden Sie eine andere.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('E-Mail', validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField('Passwort zurücksetzen anfordern')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Passwort', validators=[
        DataRequired(),
        Length(min=8, message="Das Passwort muss mindestens 8 Zeichen lang sein."),
        Regexp('^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', message="Das Passwort muss mindestens einen Großbuchstaben, einen Kleinbuchstaben, eine Zahl und ein Sonderzeichen enthalten.")
    ])
    password2 = PasswordField('Passwort wiederholen', validators=[DataRequired(), EqualTo('password', message='Passwörter müssen übereinstimmen')])
    submit = SubmitField('Passwort zurücksetzen')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Aktuelles Passwort', validators=[DataRequired()])
    new_password = PasswordField('Neues Passwort', validators=[
        DataRequired(),
        Length(min=8, message="Das Passwort muss mindestens 8 Zeichen lang sein."),
        Regexp('^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', message="Das Passwort muss mindestens einen Großbuchstaben, einen Kleinbuchstaben, eine Zahl und ein Sonderzeichen enthalten.")
    ])
    new_password2 = PasswordField('Neues Passwort wiederholen', validators=[DataRequired(), EqualTo('new_password', message='Passwörter müssen übereinstimmen')])
    submit = SubmitField('Passwort ändern')

class EditProfileForm(FlaskForm):
    username = StringField('Benutzername', validators=[
        DataRequired(),
        Length(min=3, max=64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Benutzernamen dürfen nur Buchstaben, Zahlen, Punkte oder Unterstriche enthalten')
    ])
    about_me = TextAreaField('Über mich', validators=[Length(min=0, max=140)])
    submit = SubmitField('Änderungen speichern')

class EditEventForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Beschreibung', validators=[DataRequired(), Length(max=500)])
    date = DateField('Datum', validators=[DataRequired()])
    location = StringField('Ort', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Event aktualisieren')

    def validate_date(self, field):
        if field.data < date.today():
            raise ValidationError('Das Datum darf nicht in der Vergangenheit liegen.')

class AddNewsForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired(), Length(max=100)])
    content = TextAreaField('Inhalt', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Neuigkeit hinzufügen')

class EditNewsForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired(), Length(max=100)])
    content = TextAreaField('Inhalt', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Neuigkeit aktualisieren')

class AddEventForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Beschreibung', validators=[DataRequired(), Length(max=500)])
    date = DateField('Datum', validators=[DataRequired()])
    location = StringField('Ort', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Event hinzufügen')

    def validate_date(self, field):
        if field.data < date.today():
            raise ValidationError('Das Datum darf nicht in der Vergangenheit liegen.')

class QuestionForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired(), Length(min=5, max=255)])
    content = TextAreaField('Inhalt', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Frage stellen')

class EditPlayerForm(FlaskForm):
    team = SelectField('Mannschaft', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Spieler aktualisieren')
# ... Weitere Formulare hier ...