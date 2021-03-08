# app/auth/routes.py
from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, \
    ResetPasswordRequestForm, ResetPasswordForm
from app.auth.email import send_password_reset_email
# Commmunicate logins with the db
from app.models import User


# ------------------------------------------------------------------------------
#    Login and Registration
# ------------------------------------------------------------------------------
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Username or password is invalid!")
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        # Redirects only if the url is relative. No external redirects
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.home')
        # flash('Login requested for user {}, remember_me {}'.format(
        #     form.username.data, form.remember_me.data))
        return redirect(next_page)

    return render_template("auth/login.html", title=current_app.config['TITLE'] + " - Login", form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Welcome to scout sms")
        return redirect(url_for('auth.login'))

    return render_template("auth/register.html", title=current_app.config['TITLE'] + " - Register", form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash("Check your email for instructions to reset your password")
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(uri_for('main.home'))
    user = User.verify_reset_password_token(token)
    if not user: 
        flash("Hey! we cant find you in our system")
        return redirect(uri_for('main.home'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset!")
        return redirect(uri_for('auth.login'))
    return render_template('auth/reset_password.html', title='Login Again', form=form)

