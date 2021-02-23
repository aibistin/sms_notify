# app/auth/email.py
# https://pythonhosted.org/Flask-Mail/
# from flask_mail import Message
from app.email import send_email
from flask import current_app


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[SMSNotify] Reset Your Password',
              sender= current_app.config['ADMINS'],
              recipients=[user.email],
              text_body=render_template(
                  'email/reset_password.txt', user=user, token=token),
              html_body=render_template(
                  'email/reset_password.html', user=user, token=token)
              )
