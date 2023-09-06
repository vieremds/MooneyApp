from app import db
from flask_login import current_user
from app.models import Account, Transaction, Transfer, Category
from sqlalchemy import func
from config import Config
import json
import collections
from datetime import datetime, date, timedelta
import calendar
import yfinance
import tabula
import pandas as pd


def get_balance_by_type(types=Config.ACCOUNT_TYPES):
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
                    balances.append(round(float(acc_[key][0] or 0.00), 2))
                else:
                    balances.append(round(float(acc.start_balance or 0.00), 2))

            balance_by_type[type] = normal_amt(sum(balances))

        elif type in ['Giro','Liability']:
            account = [id[0] for id in db.session.query(Account.id).filter_by(type=type).filter_by(user_id=current_user.id).all()]

            #BALANCE ON TOP STUFF
            transaction_balance = Transaction.query.filter(Transaction.account.in_(account)).with_entities(func.sum(Transaction.amount).label('total')).first().total
            trf_negative = Transfer.query.filter(Transfer.source_account.in_(account)).with_entities(func.sum(Transfer.amount).label('total')).first().total
            trf_positive = Transfer.query.filter(Transfer.target_account.in_(account)).with_entities(func.sum(Transfer.amount).label('total')).first().total
            start_balance = Account.query.filter(Account.id.in_(account)).with_entities(func.sum(Account.start_balance).label('total')).first().total

            transfer_balance = round(float(trf_positive or 0.00), 2) - round(float(trf_negative or 0.00),2)
            balance = round(float(start_balance or 0.00),2) + round(float(transaction_balance or 0.0),2) + transfer_balance
            balance_by_type[type] = normal_amt(balance)

        elif type == 'History':
            pass
    
    return balance_by_type

def get_single_balance(account):
    if account.type in ['Giro','Liability']:
        transaction_balance = Transaction.query.filter(Transaction.account.in_([account.id])).with_entities(func.sum(Transaction.amount).label('total')).first().total
        trf_negative = Transfer.query.filter(Transfer.source_account.in_([account.id])).with_entities(func.sum(Transfer.amount).label('total')).first().total
        trf_positive = Transfer.query.filter(Transfer.target_account.in_([account.id])).with_entities(func.sum(Transfer.amount).label('total')).first().total
        start_balance = Account.query.filter(Account.id.in_([account.id])).with_entities(func.sum(Account.start_balance).label('total')).first().total

        transfer_balance = round(float(trf_positive or 0.00),2) - round(float(trf_negative or 0.00),2)
        balance = round(float(start_balance or 0.00),2) + round(float(transaction_balance or 0.00),2) + transfer_balance

    elif account.type == 'Investment':
        balance = normal_amt(account.start_balance)
        
        try:
            acc_= json.loads(account.balance_archive)
            acc_= collections.OrderedDict(sorted(acc_.items()))
        except:
            acc_= False

        if acc_:
            last_key, last_value = acc_.popitem()
            balance = normal_amt(last_value[0])
    
    elif account.type == 'History':
        balance = 0.00

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

def get_month_dates(st_date='', ed_date='', get_previous=False):
    if not st_date and not ed_date :
        today = date.today()
        first = today.replace(day=1)
        end_date = first - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif get_previous:
        first = st_date.replace(day=1)
        end_date = first - timedelta(days=1)
        start_date = end_date.replace(day=1)
    else:
        start_date = st_date.replace(day = 1)
        end_date = ed_date.replace(day = calendar.monthrange(ed_date.year, ed_date.month)[1])
    
    return start_date, end_date

def get_balance_at_eom(accounts, month_range):

    acc_trimmed = {}
    acc_range = []

    for acc in accounts:
        acc_trimmed[acc.name] = {}
        
        if acc.name not in acc_range:
            acc_range.append(acc.name)

        if acc.type == 'Investment':            
            for idx, m in enumerate(month_range): 
                acc_trimmed[acc.name][m] = normal_amt(acc.start_balance)
                
                try:
                    acc_= json.loads(acc.balance_archive)
                    acc_= collections.OrderedDict(sorted(acc_.items()))
                except:
                    acc_= False

                if acc_:
                    #{2023-03-23: [1000, "balbalba"], 2023-04-23: [1000, "balbalba"]}
                    if m in acc_:
                        acc_trimmed[acc.name][m] = normal_amt(acc_[m][0])
                    else:
                        if idx-1 >= 0:
                            acc_trimmed[acc.name][m] = normal_amt(acc_trimmed[acc.name][month_range[idx-1]])
        elif acc.type in ['Giro','Liability']:
            for idx, m in enumerate(month_range):
                a, endDate = get_month_dates(st_date =datetime.strptime(m,'%Y-%m'), ed_date = datetime.strptime(m,'%Y-%m'))
                transaction_balance = db.session.query(func.sum(Transaction.amount)).filter(Transaction.account.in_([acc.id])).filter(Transaction.date<=endDate).first()
                trf_negative = db.session.query(func.sum(Transfer.amount)).filter(Transfer.source_account.in_([acc.id])).filter(Transfer.date<=endDate).first()
                trf_positive = db.session.query(func.sum(Transfer.amount)).filter(Transfer.target_account.in_([acc.id])).filter(Transfer.date<=endDate).first()
                start_balance = db.session.query(Account.start_balance).filter(Account.id.in_([acc.id])).filter(Account.balance_date<=endDate).first()
                
                transfer_balance = normal_amt(trf_positive[0]) - normal_amt(trf_negative[0])
                balance = normal_amt(start_balance[0]) + normal_amt(transaction_balance[0]) + transfer_balance

                acc_trimmed[acc.name][m] = normal_amt(balance)

        elif acc.type == 'History':
            pass

    return acc_trimmed, acc_range

def normal_amt(amount):
    try:
        amt = round(float(amount or 0.00),2)
    except: 
        amt = 0.00
    return amt

def fx_base(amount, currency, base='EUR'):
    if currency != base:
        fx = yfinance.Ticker(currency + 'EUR=X')
        fx = fx.info['previousClose']
        amt = normal_amt(amount * fx)
    else:
        amt = normal_amt(amount)
    return amt

def readStatement(file, categories, pages='all', area=[10,0,80,100], columns=[7,15,80], regex="([0-3][0-9].[0-1][0-9])", columnsName=['date', 'date2', 'description', 'amount'], dateFormat='%d.%m', filterOff='ZAHLUNG.*'): 
    try:
        dfs = tabula.read_pdf(file, pages=pages, relative_area=True, relative_columns=True, area=area, columns=columns, java_options=[
        "-Dorg.slf4j.simpleLogger.defaultLogLevel=off",
        "-Dorg.apache.commons.logging.Log=org.apache.commons.logging.impl.NoOpLog"])
        
        #merge dfs
        df = pd.concat(dfs, ignore_index=True)

        #renameColumns
        df.columns = columnsName
    except ValueError:
        dfs = tabula.read_pdf(file, pages=2, relative_area=True, relative_columns=True, area=[10,12,90,100], columns=[26,37,79,91], java_options=[
        "-Dorg.slf4j.simpleLogger.defaultLogLevel=off",
        "-Dorg.apache.commons.logging.Log=org.apache.commons.logging.impl.NoOpLog"])
        regex = "([0-3][0-9].[0-1][0-9].[2][0-2][0-9][0-9])"
        columnsName = ['date', 'date2', 'description', 'amount', 'amount2']
        dateFormat = '%d.%m.%Y'

        #merge dfs
        df = pd.concat(dfs, ignore_index=True)

        #renameColumns
        df.columns = columnsName

    #filter stuff out
    df = df.dropna()
    df = df[df["date"].str.match(regex)]
    df = df[~df["description"].str.contains(filterOff, case=False)]
    df = df.drop(columns=['date2','amount2'], errors='ignore')

    #Reset index
    df = df.reset_index(drop=True)

    #Adjust datatypes
    df['date'] = pd.to_datetime(df['date'], format=dateFormat, dayfirst=True) + pd.DateOffset(year=2023)
    df['date'] = df['date'].dt.date
    try:
        df['amount'] = pd.to_numeric(df['amount'].str.replace(',','.').str.replace(' ',''), downcast='float')
    except ValueError as e:
        print(f"An exception occurred when handling the amount {str(e)}")
    #Get all category name for the user
    categoryList = [] 
    for category in categories:
        categoryList.append(category.name)

    df['category'] = [categoryList for _ in df.index]

    return df.to_json(double_precision=2, orient='records', date_format='iso',  date_unit='s')
