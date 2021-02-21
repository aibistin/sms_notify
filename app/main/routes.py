# app/main/routes.py
from twilio.rest import Client
# HTML template module
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from datetime import datetime
from app import current_app, db
from app.main.forms import EditProfileForm, EmptyForm, MessageForm
from app.main import bp
# Commmunicate logins with the db
from app.models import User, Message


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route("/", methods=['GET', 'POST'])
@bp.route("/index", methods=['GET', 'POST'])
def home():
    #    if current_user.is_authenticated:
    #        flash("You are logged in as {}".format(current_user.username))
    print(current_app.config)

    messages = []
    form = None

    if current_user.is_authenticated:
        form = MessageForm()
        if form.validate_on_submit():
            msg = Message(body=form.message.data, sender=current_user)
            db.session.add(msg)
            db.session.commit()
            flash("You sent a message!")
            return redirect(url_for('main.home'))

        messages = current_user.followed_messages().all()

    return render_template("index.html", title=current_app.config['TITLE'] + " - Send", form=form, messages=messages)


@bp.route('/sms')
@login_required
def send_message():
    #  and set the environment variables. See http://twil.io/secure
    # account_sid = os.environ['TWILIO_ACCOUNT_SID']
    # auth_token = os.environ['TWILIO_AUTH_TOKEN']
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(body=form.message.data, sender=current_user).filter()
        db.session.add(msg)
        db.session.commit()
        flash("You sent a message!")
        return redirect(url_for('main.home'))

    msg = {'body': "One long message",
           'from_': '+18593748177', 'to': '+19177108047'}
    # client = Client(current_app.config['TWILIO_ACCOUNT_SID'],
    # current_app.config['TWILIO_AUTH_TOKEN'])
    print(current_app.config)
    message = None
    # message = client.messages.create(**msg)
    #    .create(
    #         body="One long message",
    #         from_='+18593748177',
    #         to='+19177108047'
    #     )

    msg['sid'] = message.id if message else "Fred"
    # print(message.sid)
    return render_template("index.html", title=current_app.config['TITLE'] + " - Send", form=form, msg=msg)

# ------------------------------------------------------------------------------
#    User Profile
# ------------------------------------------------------------------------------


@bp.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    print("INSIDE /user/" + username );
    user = User.query.filter_by(username=username).first_or_404()
    messages = current_user.followed_messages().all()

    # EmptyForm for FollowFollowers
    form = EmptyForm()
    return render_template('user.html', user=user, messages=messages, form=form)


@bp.route('/user/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your profile has been changed")
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title='Edit Profile', form=form)

# ------------------------------------------------------------------------------
#    Follow and Unfollow
# ------------------------------------------------------------------------------


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User, {1} doesn't exist!".format(username))
            return redirect(url_for('main.home'))
        if user == current_user:
            flash("You cannot follow yourself!")
            return redirect(url_for('main.user', username=username))

        current_user.follow(user)
        db.session.commit()
        flash("You are now followng {}!".format(user.username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.home'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User, {1} doesn't exist!".format(username))
            return redirect(url_for('main.home'))
        if user == current_user:
            flash("You cannot unfollow yourself!")
            return redirect(url_for('main.user', username=username))

        current_user.unfollow(user)
        db.session.commit()
        flash("You have stopped followng {}!".format(user.username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.home'))


# ------------------------------------------------------------------------------
#    Navigation
# ------------------------------------------------------------------------------
@bp.route('/explore')
@login_required
def explore():
    messages = Message.query.order_by(Message.timestamp.desc()).all()
    return render_template('index.html', title='Explore', messages=messages)
