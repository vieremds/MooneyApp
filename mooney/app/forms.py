from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField, SelectField, DateField, SelectMultipleField, DecimalField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, NumberRange, Optional
from wtforms.widgets.core import Select
from app.models import User, Account, Category, account_choices, category_choices, inv_acc_choices, not_inv_acc_choices, income_categories, expense_categories
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
    start_balance = DecimalField('Start_Balance', default=0.00)
    balance_date = DateField('Date')
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
    account = QuerySelectField(query_factory=not_inv_acc_choices, get_label='name')
    cat_choices = SelectField('Category Group - Optional', choices=Config.CATEGORY_TYPES, validators=[Optional(strip_whitespace=True)], default='All')
    category = QuerySelectField(query_factory=category_choices, get_label='name', allow_blank=True)
    cat_income = QuerySelectField('Category', query_factory=income_categories, get_label='name', default=None, allow_blank=True)
    cat_expense = QuerySelectField('Category', query_factory=expense_categories, get_label='name', default=None, allow_blank=True)
    amount = DecimalField('Amount', default=0.00)
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
    amount = DecimalField('Amount', validators=[NumberRange(min=0.01, message='Amount must be positive')], default=0.00)
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
    amount = DecimalField('Amount', validators=[DataRequired()], default=0.00)
    date = DateField('Date')
    description = StringField('Description')
    submit = SubmitField('Save')