from flask import current_app, render_template, url_for
from flask_mail import Message
from app.extensions import mail

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[Dartochsen] Passwort zurücksetzen',
               sender=current_app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Passwort zurücksetzen',
                  sender='noreply@example.com',
                  recipients=[user.email])
    msg.body = f'''Um Ihr Passwort zurückzusetzen, besuchen Sie folgenden Link:
{url_for('main.reset_token', token=token, _external=True)}

Wenn Sie kein Passwort-Reset angefordert haben, ignorieren Sie diese E-Mail bitte.
'''
    mail.send(msg)