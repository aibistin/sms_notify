# app/main/routes.py
from datetime import datetime
from twilio.rest import Client
# HTML template module
from flask import flash, redirect, render_template, request, url_for
from flask import g, jsonify
from flask_babel import _, lazy_gettext as _l
from flask_login import current_user, login_required
from app import current_app, db
from app.main import bp
from app.main.forms import EditProfileForm, EmptyForm, MessageForm
from app.main.forms import PrivateMessageForm, SearchForm
# Commmunicate logins with the db
from app.models import User, Message, PrivateMessage, Notification


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
#    g.locale = str(get_locale())


@bp.route("/", methods=['GET', 'POST'])
@bp.route("/index", methods=['GET', 'POST'])
@login_required
def home():
    #    if current_user.is_authenticated:
    #        flash("You are logged in as {}".format(current_user.username))
    print(current_app.config)

    messages = []
    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(body=form.message.data, sender=current_user)
        db.session.add(msg)
        db.session.commit()
        flash("You sent a message!")
        return redirect(url_for('main.home'))

    page = request.args.get('page', 1, type=int)
    messages = current_user.followed_messages().paginate( page, current_app.config['MESSAGES_PER_PAGE'], False)		
    next_url = url_for('main.home', page=messages.next_num) if messages.has_next else None
    prev_url = url_for('main.home', page=messages.prev_num) if messages.has_prev else None

    # messages = current_user.followed_messages().all()

    return render_template("index.html", title=current_app.config['TITLE'] + " - Send",
             form=form, 
             messages=messages.items,
             next_url=next_url,  prev_url=prev_url
             )


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
           'from_': '+someNumber', 'to': '+1someNumber'}
    # client = Client(current_app.config['TWILIO_ACCOUNT_SID'],
    # current_app.config['TWILIO_AUTH_TOKEN'])
    print(current_app.config)
    message = None
    # message = client.messages.create(**msg)
    #    .create(
    #         body="One long message",
    #         from_='+someNumber',
    #         to='+1someNumber'
    #     )

    msg['sid'] = message.id if message else "Fred"
    # print(message.sid)
    return render_template("index.html", title=current_app.config['TITLE'] + " - Send", form=form, msg=msg)


@bp.route('/send_private_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_private_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = PrivateMessageForm()
    if form.validate_on_submit():
        msg = PrivateMessage(sender=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        db.session.commit()
        flash(_('Your message has been sent.'))
        current_user.add_notification('unread_private_message_count', user.new_private_messages())
        db.session.commit()
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_private_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)


@bp.route('/private_messages')
@login_required
def private_messages():
    current_user.last_private_message_read_time = datetime.utcnow()
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.private_messages_received.order_by(
        PrivateMessage.timestamp.desc()).paginate(
            page, current_app.config['MESSAGES_PER_PAGE'], False)
    current_user.add_notification('unread_private_message_count', 0)
    db.session.commit()
    next_url = url_for('main.private_messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.private_messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('private_messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)
						   
# ------------------------------------------------------------------------------
#    User Profile
# ------------------------------------------------------------------------------


@bp.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
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
    
    page = request.args.get('page', 1, type=int)
    messages = Message.query.order_by(Message.timestamp.desc()).paginate(page, current_app.config['MESSAGES_PER_PAGE'], False)
    next_url = url_for('main.explore', page=messages.next_num) if messages.has_next else None
    prev_url = url_for('main.explore', page=messages.prev_num) if messages.has_prev else None
    return render_template('index.html', title='Explore', messages=messages.items, next_url=next_url,  prev_url=prev_url)


@bp.route('/search')
@login_required
def search():
    # Use this type of form validation for GET requests
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    messages, total = Message.search(
        g.search_form.q.data, page, current_app.config['MESSAGES_PER_PAGE'])
    next_url = url_for('main.search', q.search_form.q.data, page=page + 1) \
        if total > current_app.config['MESSAGES_PER_PAGE'] * page else None
    prev_url = url_for('main.search', q.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


# ------------------------------------------------------------------------------
#    Services
# ------------------------------------------------------------------------------

@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])


@bp.route('/export_messages')
@login_required
def export_messages():
    if current_user.get_task_in_progress('export_messages'):
        flash(_('Theres an export task already in progress'))
    else:
        current_user.launch_task('export_messages', _('Exporting messages...'))
        db.session.commit()
    return redirect(url_for('main.user', username=current_user.username))
