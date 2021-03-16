# app/models.py
import json
import redis
import rq
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
from app import create_app, db, login
from app.search import add_to_index, remove_from_index, query_index


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
    tasks = db.relationship('Task', backref='user', lazy='dynamic')


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
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithm=[
                            'HS256'])['reset_password']
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


    private_messages_sent = db.relationship('PrivateMessage',
                                    foreign_keys='PrivateMessage.sender_id',
                                    backref='sender', lazy='dynamic')

    private_messages_received = db.relationship('PrivateMessage',
									foreign_keys='PrivateMessage.recipient_id',
									backref='recipient', lazy='dynamic')

    last_private_message_read_time = db.Column(db.DateTime)

    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def new_private_messages(self):
	    last_read_time = self.last_private_message_read_time or datetime(1900, 1, 1)
	    return PrivateMessage.query.filter_by(recipient=self).filter( PrivateMessage.timestamp > last_read_time).count()

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, self.id, *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self, complete=False).first()

    # Tells Python to print objects of this class
    def __repr__(self):
        return '<User {}>'.format(self.username)



@ login.user_loader
def load_user(id):
    return User.query.get(int(id))

# ------------------------------------------------------------------------------
#  Searching For Stuff
# ------------------------------------------------------------------------------

class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

# ------------------------------------------------------------------------------
#  Message Class
#  Note: Run `>>> Message.reindex()` in the flask shell to set up the elasticsearch 
#        index. 
# ------------------------------------------------------------------------------

class Message(SearchableMixin, db.Model):
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(240), index=False, unique=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Message {}>'.format(self.body)

# ------------------------------------------------------------------------------
#  Private Message Class
#  Note: Run `>>> Message.reindex()` in the flask shell to set up the elasticsearch 
#        index. 
# ------------------------------------------------------------------------------

class PrivateMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<PrivateMessage {}>'.format(self.body)

# ------------------------------------------------------------------------------
# Notification  Class
# Notify of new PrivateMessage for the User
# Being generic, it's not entirely tied to PrivateMessage notifications
# ------------------------------------------------------------------------------

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))

# ------------------------------------------------------------------------------
# Task  Class
# Uses Redis
# ------------------------------------------------------------------------------

class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        prog = job.meta.get('progress', 0)
        return job.meta.get('progress', 0) if job is not None else 100
