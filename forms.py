from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError


class SignUpForm(FlaskForm):
    name = StringField(label='Name', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired(), Length(min=8, max=20)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(label='Sign up')


class VerificationForm(FlaskForm):

    ver_code = StringField(label='Verification Code', validators=[DataRequired(), Length(6,6)])
    submit = SubmitField('Verify')

    def __init__(self, expected_code):
        super().__init__()
        self.expected_code = expected_code

    def validate_ver_code(self, field):
        if field.data != self.expected_code:
            raise ValidationError('Not the right code buddy! Try again')


class LoginForm(FlaskForm):
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired(), Length(min=8, max=20)])
    submit = SubmitField(label='Login')
