from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from app import db, login
from flask_login import UserMixin
from flask_login import current_user

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    accounts = db.relationship('Account', backref='owner', lazy='dynamic')
    
    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

class Account(db.Model):
    __tablename__ = 'account'
    id            = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String(64), unique=False)
    type  = db.Column(db.String(32), unique=False)
    currency = db.Column(db.String(16), unique=False)
    description   = db.Column(db.String(255), nullable=True)
    created_at    = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    start_balance = db.Column(db.Float(64), default=0.00)
    balance_date   = db.Column(db.Date, index=True, default=datetime.today())
    user_id       = db.Column(db.Integer, db.ForeignKey('user.id'))
    balance_archive = db.Column(db.String(), nullable=True)

    def __repr__(self):
        return '<Account {}>'.format(self.name)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Category(db.Model):
    __tablename__ = 'category'
    id            = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String(64), unique=False)
    type  = db.Column(db.String(32), unique=False)
    description   = db.Column(db.String(255), nullable=True)
    competence = db.Column(db.String(32), unique=False, default='Monthly')
    created_at    = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    budget = db.Column(db.Float(64), default=0.00)
    user_id       = db.Column(db.Integer, db.ForeignKey('user.id'))
    icon          = db.Column(db.String(255), nullable=True, default='mooney/app/static/icons/icon.png')
    budget_archive = db.Column(db.String(), nullable=True)

    def __repr__(self):
        return '<Category {}>'.format(self.name)

class Transaction(db.Model):
    __tablename__ = 'transaction'
    id            = db.Column(db.Integer, primary_key=True)
    account  = db.Column(db.Integer, db.ForeignKey('account.id'))
    category  = db.Column(db.Integer, db.ForeignKey('category.id'))
    amount = db.Column(db.Float(64), default=0.00, index=True)
    currency = db.Column(db.String(16), db.ForeignKey('account.currency'), unique=False)
    date   = db.Column(db.Date, index=True, default=datetime.today())
    created_at    = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    tag  = db.Column(db.String(32), unique=False)
    description   = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return self.amount

def account_choices(type=False, user=current_user):
    if type:
        ac = Account.query.filter_by(user_id=current_user.id).filter_by(type=type)
    else:
        ac = Account.query.filter_by(user_id=current_user.id)
    return ac

def inv_acc_choices(type='Investment', user=current_user):
    ac = Account.query.filter_by(user_id=current_user.id).filter_by(type=type)
    return ac

def not_inv_acc_choices(type='Investment', user=current_user):
    ac = Account.query.filter_by(user_id=current_user.id).filter(Account.type!=type)
    return ac

def category_choices(type=False, user=current_user):
    cc = Category.query.filter_by(user_id=current_user.id)
    return cc

def income_categories(type='Income', user=current_user):
    cc = Category.query.filter_by(user_id=current_user.id).filter_by(type=type)
    return cc

def expense_categories(type='Expense', user=current_user):
    cc = Category.query.filter_by(user_id=current_user.id).filter_by(type=type)
    return cc

class Transfer(db.Model):
    __tablename__ = 'transfer'
    id            = db.Column(db.Integer, primary_key=True)
    source_account  = db.Column(db.Integer, db.ForeignKey('account.id'))
    target_account  = db.Column(db.Integer, db.ForeignKey('account.id'))
    currency = db.Column(db.String(16), db.ForeignKey('account.currency'), unique=False)
    date   = db.Column(db.Date, index=True, default=datetime.today())
    amount = db.Column(db.Float(64), default=0.00, index=True)
    created_at    = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    description   = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return self.amount

class Assets(db.Model):
    __tablename__ = 'assets'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('user.id'))
    account        = db.Column(db.String)
    symbol         = db.Column(db.String(16), index=True)
    name           = db.Column(db.String())
    type           = db.Column(db.String())
    previous_close = db.Column(db.Float(64))
    historic_price = db.Column(db.String(), nullable=True)
    quantity       = db.Column(db.Integer)
    cost           = db.Column(db.Float(64))
    purchase_date  = db.Column(db.Date)
    purchase_price = db.Column(db.Float(64))
    last365days    = db.Column(db.Float(16))
    last30days     = db.Column(db.Float(16))
    last7days      = db.Column(db.Float(16))

    def __repr__(self):
        return self.symbol