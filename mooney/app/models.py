from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db, login
from flask_login import UserMixin


class User(UserMixin, db.Model):
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
    id            = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String(64), unique=True)
    type  = db.Column(db.String(32), unique=False)
    currency = db.Column(db.String(16), unique=False)
    description   = db.Column(db.String(255), nullable=True)
    created_at    = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    start_balance = db.Column(db.Float(64), default=0.00)
    user_id       = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Account {}>'.format(self.name)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))