from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp
from app.models.user import User

class RegistrationForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    password = PasswordField('Passwort', validators=[
        DataRequired(),
        Length(min=12, message="Das Passwort muss mindestens 12 Zeichen lang sein."),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$',
               message="Das Passwort muss mindestens einen Großbuchstaben, einen Kleinbuchstaben, eine Zahl und ein Sonderzeichen enthalten.")
    ])
    confirm_password = PasswordField('Passwort bestätigen', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrieren')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Dieser Benutzername ist bereits vergeben. Bitte wählen Sie einen anderen.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Diese E-Mail-Adresse wird bereits verwendet. Bitte wählen Sie eine andere.')

class LoginForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    remember_me = BooleanField('Angemeldet bleiben')
    submit = SubmitField('Anmelden')

class EditProfileForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired()])
    about_me = TextAreaField('Über mich', validators=[Length(min=0, max=140)])
    submit = SubmitField('Speichern')

class AddEventForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired()])
    description = TextAreaField('Beschreibung', validators=[DataRequired()])
    date = DateField('Datum', format='%Y-%m-%d', validators=[DataRequired()])
    location = StringField('Ort', validators=[DataRequired()])
    submit = SubmitField('Event hinzufügen')

class AddNewsForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired()])
    content = TextAreaField('Inhalt', validators=[DataRequired()])
    submit = SubmitField('Neuigkeit hinzufügen')

class EditEventForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired()])
    description = TextAreaField('Beschreibung', validators=[DataRequired()])
    date = DateField('Datum', format='%Y-%m-%d', validators=[DataRequired()])
    location = StringField('Ort', validators=[DataRequired()])
    submit = SubmitField('Aktualisieren')

class EditNewsForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired()])
    content = TextAreaField('Inhalt', validators=[DataRequired()])
    submit = SubmitField('Aktualisieren')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Aktuelles Passwort', validators=[DataRequired()])
    new_password = PasswordField('Neues Passwort', validators=[
        DataRequired(),
        Length(min=12, message="Das Passwort muss mindestens 12 Zeichen lang sein."),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$',
               message="Das Passwort muss mindestens einen Großbuchstaben, einen Kleinbuchstaben, eine Zahl und ein Sonderzeichen enthalten.")
    ])
    confirm_password = PasswordField('Neues Passwort bestätigen', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwörter müssen übereinstimmen.')
    ])
    submit = SubmitField('Passwort ändern')

class RequestPasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Passwort zurücksetzen anfordern')
