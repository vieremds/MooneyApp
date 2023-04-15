from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField, SelectField, DateField, SelectMultipleField, RadioField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, NumberRange
from wtforms.widgets.core import Select
from app.models import User, Account, Category, account_choices, category_choices, inv_acc_choices
import calendar
from datetime import datetime, date
from config import Config
from .func import get_month_dates

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
        choices=Config.ACCOUNT_TYPES)
    currency = SelectField('Currency', validators=[DataRequired()],
        choices=Config.CURRENCIES)
    description = StringField('Description')
    start_balance = FloatField('Start_Balance')
    balance_date = DateField('Balance_Date')
    submit = SubmitField('Add')
    def validate_name(self, name):
        account = Account.query.filter_by(name=name.data).first()
        if account is not None:
            raise ValidationError('Please use a different account name.')
        
class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    type = SelectField('Type', validators=[DataRequired()], 
        choices=[('Income'), ('Expense')])
    description = StringField('Description')
    budget = FloatField('Budget')
    icon = StringField('Icon')
    submit = SubmitField('Save')

    def validate_name(self, name):
        category = Category.query.filter_by(name=name.data).first()
        if category is not None:
            raise ValidationError('Please use a different category name.')


class TransactionForm(FlaskForm):
    account = QuerySelectField(query_factory=account_choices, get_label='name')
    category = QuerySelectField(query_factory=category_choices, get_label='name')
    amount = FloatField('Amount')
    currency = SelectField('Currency', validators=[DataRequired()],
        choices=Config.CURRENCIES)
    date = DateField('Date')
    tag = StringField('Tag')
    description = StringField('Description')
    submit = SubmitField('Save & Exit')
    submit_plus = SubmitField('Save +1')

class TransferForm(FlaskForm):
    source_account = QuerySelectField(query_factory=account_choices, get_label='name')
    target_account = QuerySelectField(query_factory=account_choices, get_label='name')
    date = DateField('Date')
    amount = FloatField('Amount')
    currency = SelectField('Currency', validators=[DataRequired()],
        choices=Config.CURRENCIES)
    description = StringField('Description')
    submit = SubmitField('Save')

class SelectDateForm(FlaskForm):
    start_date = DateField('Start Date', default=get_month_dates()[0])
    end_date = DateField('End Date', default=get_month_dates()[1])
    amount = FloatField('Amount')
    submit = SubmitField('Go')

class DateTypeForm(FlaskForm):
    start_date = DateField('Start Date', default=get_month_dates()[0])
    end_date = DateField('End Date', default=get_month_dates()[1])
    type = SelectMultipleField('Type', id='type', validators=[DataRequired()], 
        choices=Config.ACCOUNT_TYPES, default='')
    submit = SubmitField('Go')

class DateAccountCategoryForm(FlaskForm):
    start_date = DateField('Start Date', default=get_month_dates()[0])
    end_date = DateField('End Date', default=get_month_dates()[1])
    account = QuerySelectField(query_factory=account_choices, get_label='name', allow_blank=True, default='')
    category = QuerySelectField(query_factory=category_choices, get_label='name', allow_blank=True, default='')
    submit = SubmitField('Go')


class UpdateBalanceForm(FlaskForm):
    account = QuerySelectField(query_factory=inv_acc_choices, get_label='name')
    amount = FloatField('Amount', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField('Save')