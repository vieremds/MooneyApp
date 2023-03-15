from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, NumberRange
from app.models import User, Account

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
        
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class AddAccountForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    type = SelectField('Type', validators=[DataRequired()], 
        choices=[('Giro', 'Giro'), ('Liability', 'Liability'), ('Investment', 'Investment')])
    currency = SelectField('Currency', validators=[DataRequired()],
        choices=[('EUR', 'Euro'), ('BRL', 'Brasilian-Real'), ('USD', 'Dollar'), ('GBP','British-Pounds')])
    description = StringField('Description')
    start_balance = FloatField('Start_Balance')
    submit = SubmitField('Add')

    def validate_name(self, name):
        account = Account.query.filter_by(name=name.data).first()
        if account is not None:
            raise ValidationError('Please use a different account name.')