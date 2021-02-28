# app/main/forms.py
from flask_wtf import FlaskForm
from flask import request
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from wtforms.validators import Length
from flask_babel import _, lazy_gettext as _l
# Commmunicate logins with the db
from app.models import User

# ------------------------------------------------------------------------------
#    User Profile Forms
# ------------------------------------------------------------------------------


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = StringField('About Me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(
                    "Drat! Username exists already. Pick another one!")


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

# ------------------------------------------------------------------------------
#    Other Forms
# ------------------------------------------------------------------------------


class MessageForm(FlaskForm):
    message = TextAreaField('Text Msg:', validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Send')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


# Something like this search: https://duckduckgo.com/?t=ffnt&q=meaning+of+life&atb=v123-1&ia=web
class SearchForm(FlaskForm):
    q = StringField(_l('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            # Pass field values instead of usual "request.form" object
            kwargs['formdata'] = request.args
            # For clickable search links to work, CSRF has to be disabled!
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)
