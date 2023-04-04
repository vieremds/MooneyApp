from app import db
from flask_login import current_user
from app.models import Account, Transaction, Transfer
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
        print(account.id)
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