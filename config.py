import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """This adds to the existing Flask Config"""
    TITLE = "SMS Notify"
    #
    # Twilio Stuff
    #
    TWILIO_ACCOUNT_SID = os.environ.get(
        'TWILIO_ACCOUNT_SID') or 'You need to get a Twilio Account SID'
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN') or None
    SECRET_KEY = os.environ.get('TWILIO_SECRET_KEY')
    #
    # Database Stuff
    #
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    # Notifys of db changes
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    #
    # Email Setup
    #
    # Gmail or hMail
    # https://www.hmailserver.com/documentation/
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = os.environ.get('MAIL_ADMINS')
    # Python Mail simulator
    # (venv) $ python -m smtpd -n -c DebuggingServer localhost:8025
    # - MAIL_SERVER = "localhost"
    # - MAIL_PORT   = "8025"
    # ADMINS = os.environ.get('MAIL_ADMINS')
    #
    # Babel
    LANGUAGES = ["en", "es", "gd", "th"]
    #
    # Elasticsearch
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    MESSAGES_PER_PAGE = int(os.environ.get('MESSAGES_PER_PAGE') or 6)
