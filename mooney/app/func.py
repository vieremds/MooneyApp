from app import db
from flask_login import current_user
from app.models import Account, Transaction, Transfer, Category
from sqlalchemy import func
from config import Config
import json
import collections


def get_balance_by_type():
    types = Config.ACCOUNT_TYPES
    balance_by_type = {}

    for type in types:
        if type == 'Investment':
            accounts =  Account.query.filter_by(user_id=current_user.id).filter_by(type=type).all()
            balances = []

            for acc in accounts:
                try:
                    acc_= json.loads(acc.balance_archive)
                    acc_= collections.OrderedDict(sorted(acc_.items()))
                except:
                    acc_= False
                if acc_:
                    #get last key, and amount
                    key = next(reversed(acc_))
                    balances.append(acc_[key][0])
                else:
                    balances.append(acc.start_balance)

            balance_by_type[type] = sum(balances)

        else:
            account = [id[0] for id in db.session.query(Account.id).filter_by(type=type).filter_by(user_id=current_user.id).all()]

            #BALANCE ON TOP STUFF
            transaction_balance = Transaction.query.filter(Transaction.account.in_(account)).with_entities(func.sum(Transaction.amount).label('total')).first().total
            trf_negative = Transfer.query.filter(Transfer.source_account.in_(account)).with_entities(func.sum(Transfer.amount).label('total')).first().total
            trf_positive = Transfer.query.filter(Transfer.target_account.in_(account)).with_entities(func.sum(Transfer.amount).label('total')).first().total
            start_balance = Account.query.filter(Account.id.in_(account)).with_entities(func.sum(Account.start_balance).label('total')).first().total

            transfer_balance = float(trf_positive or 0.0) - float(trf_negative or 0.0)
            balance = float(start_balance or 0.0) + float(transaction_balance or 0.0) + transfer_balance
            balance_by_type[type] = balance
    
    return balance_by_type

def get_single_balance(account):
    if account.type != 'Investment':
        transaction_balance = Transaction.query.filter(Transaction.account.in_([account.id])).with_entities(func.sum(Transaction.amount).label('total')).first().total
        trf_negative = Transfer.query.filter(Transfer.source_account.in_([account.id])).with_entities(func.sum(Transfer.amount).label('total')).first().total
        trf_positive = Transfer.query.filter(Transfer.target_account.in_([account.id])).with_entities(func.sum(Transfer.amount).label('total')).first().total
        start_balance = Account.query.filter(Account.id.in_([account.id])).with_entities(func.sum(Account.start_balance).label('total')).first().total

        transfer_balance = float(trf_positive or 0.0) - float(trf_negative or 0.0)
        balance = float(start_balance or 0.0) + float(transaction_balance or 0.0) + transfer_balance

    else:
        balance = account.start_balance
        
        try:
            acc_= json.loads(account.balance_archive)
            acc_= collections.OrderedDict(sorted(acc_.items()))
        except:
            acc_= False

        if acc_:
            last_key, last_value = acc_.popitem()
            balance = last_value[0]
    
    return balance

def get_category_balance(start_date, end_date):
    values = []

    #Income
    cat_ids = [id[0] for id in db.session.query(Category.id).filter_by(user_id = current_user.id).filter_by(type='Income').all()]
    income = db.session.query(func.sum(Transaction.amount)).filter(Transaction.category.in_(cat_ids)).filter(Transaction.date.between(start_date, end_date)).first()

    #expense
    cat_ids = [id[0] for id in db.session.query(Category.id).filter_by(user_id = current_user.id).filter_by(type='Expense').all()]       
    expense = db.session.query(func.sum(Transaction.amount)).filter(Transaction.category.in_(cat_ids)).filter(Transaction.date.between(start_date, end_date)).first()

    values.append(round(float(income[0] or 0.00), 2))
    values.append(round(float(expense[0] or 0.00), 2))
    values.append(round(float(values[0] + values[1]), 2))

    return values


def get_category_type_balance(start_date, end_date):
    income_keys = []
    income_values = []
    expense_keys = []
    expense_values = []

    #Income
    cat_ids = db.session.query(Category.type, Category.name, Category.id).filter_by(user_id = current_user.id).filter_by(type='Income').all()
    for cat in cat_ids:
        amount = db.session.query(func.sum(Transaction.amount)).filter(Transaction.category.in_([cat.id])).filter(Transaction.date.between(start_date, end_date)).first()
        income_keys.append(cat.name)
        income_values.append(round(float(amount[0] or 0.00), 2))

    #expense
    cat_ids = db.session.query(Category.type, Category.name, Category.id).filter_by(user_id = current_user.id).filter_by(type='Expense').all()   
    for cat in cat_ids:
        amount = db.session.query(func.sum(Transaction.amount)).filter(Transaction.category.in_([cat.id])).filter(Transaction.date.between(start_date, end_date)).first()
        expense_keys.append(cat.name)
        expense_values.append(round(float(amount[0] or 0.00), 2))

    return income_keys, income_values, expense_keys, expense_values
