# app/models.py
from datetime import datetime
from time import time
from hashlib import md5
from flask import current_app
# To load the users from the database
from flask_login import UserMixin
# Password hashing
from werkzeug.security import generate_password_hash, check_password_hash
# JWT
import jwt
from app import  create_app, db, login


# Associative or bridging table
followers = db.Table('followers',
                     db.Column('follower_id', db.Integer,
                               db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer,
                               db.ForeignKey('user.id'))
                     )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), index=True, unique=True)
    #
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='sender', lazy='dynamic')

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def followed_messages(self):
        followed = Message.query.join(
            followers, (followers.c.followed_id == Message.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Message.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Message.timestamp.desc())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in},
                current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @ staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token,current_app.config['SECRET_KEY'],algorithm = ['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    # Tells Python to print objects of this class
    def __repr__(self):
        return '<User {}>'.format(self.username)


# ------------------------------------------------------------------------------


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(240), index=False, unique=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Message {}>'.format(self.body)

# ------------------------------------------------------------------------------


@ login.user_loader
def load_user(id):
    return User.query.get(int(id))
