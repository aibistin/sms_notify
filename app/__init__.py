# app/__init__.py
# from app import models
# from app.main import bp as main_bp
# from app.auth import bp as auth_bp
import logging
from logging.handlers import RotatingFileHandler
import os
from flask import current_app, Flask, request
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
# from flask_babel import Babel
#
# Register the error blueprint. Import bp right before register.
# from app.errors import bp as errors_bp
# app.register_blueprint(errors_bp)
# Register the auth blueprint.
# app.register_blueprint(auth_bp, url_prefix='/auth')
# Register the main blueprint.
# app.register_blueprint(main_bp)


# app = Flask(__name__)
# app.config.from_object(Config)

# db = SQLAlchemy(app)
# migrate = Migrate(app, db)
# The view function that handles logins
# login = LoginManager(app)
# login.login_view = 'login'
# Email
# mail = Mail(app)
# JS
# moment = Moment(app)
# babel = Babel(app)
# CSS
# bootstrap = Bootstrap(app)


# Start Refactor

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Get thee hence until thou loggest in!'
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    # babel.init_app(app)

    #
    # Register the error blueprint. Import bp right before register.
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    # Register the auth blueprint.
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    # Register the main blueprint.
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    if not app.debug:

        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/sms_notify.log', maxBytes=10240,
                                           backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('ScoutSms startup')

    return app


# END Refactor

# if __name__ == "__main__":
#     app.run()


# if not app.debug:

#     if not os.path.exists('logs'):
#         os.mkdir('logs')
#     file_handler = RotatingFileHandler('logs/sms_notify.log', maxBytes=10240,
#                                        backupCount=10)
#     file_handler.setFormatter(logging.Formatter(
#         '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
#     file_handler.setLevel(logging.INFO)
#     app.logger.addHandler(file_handler)

#     app.logger.setLevel(logging.INFO)
#     app.logger.info('ScoutSms startup')


# from logging.handlers import SMTPHandler
# if not app.debug:
#     if app.config['MAIL_SERVER']:
#         auth = None
#         if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
#             auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
#         secure = None
#         if app.config['MAIL_USE_TLS']:
#             secure = ()
#         mail_handler = SMTPHandler(
#             mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
#             fromaddr='no-reply@' + app.config['MAIL_SERVER'],
#             toaddrs=app.config['ADMINS'], subject='ScoutSms Failure',
#             credentials=auth, secure=secure)
#         mail_handler.setLevel(logging.ERROR)
#         app.logger.addHandler(mail_handler)

# Remember
# export FLASK_APP=sms_notify.py
# or:
# set FLASK_APP=sms_notify.py
# or: import flask-dotenv
# put into the .flaskenv

# @babel.localeselector
# def get_locale():
#     return request.accept_languages.best_match(app.config['LANGUAGES'])
# Last line to prevent circular references

from app import models