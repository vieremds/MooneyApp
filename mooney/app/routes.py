from flask import render_template, flash, redirect, url_for, request, session
from app import app, db
from app.forms import LoginForm, RegistrationForm, AddAccountForm, CategoryForm, TransactionForm, TransferForm, SelectDateForm, DateTypeForm, UpdateBalanceForm, DateAccountForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Account, Category, Transaction, Transfer
from werkzeug.urls import url_parse
from sqlalchemy import func
from config import Config
import pandas as pd 
import json
import collections
from .func import get_balance_by_type, get_single_balance, get_category_balance, get_category_type_balance
from datetime import datetime, date, timedelta  
import calendar

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = DateTypeForm()

    balance_by_type = get_balance_by_type()
  
    range_desc = []
    cat_range = []
    bdgt_range = []
    trx_by_cat = {}
    
    if form.validate_on_submit():

        account = [id[0] for id in db.session.query(Account.id).filter(Account.type.in_(form.type.data)).filter_by(user_id=current_user.id).all()]

        #CATEGORY/TRANSACTION STUFF
        account_trx = db.session.query(func.sum(Transaction.amount).label('sum'), 
        func.strftime("%Y-%m", Transaction.date).label('month'), Category.name, Category.budget).join(
        Category, Category.id == Transaction.category).filter(Transaction.account.in_(account)).filter(
        Transaction.date.between(form.start_date.data, form.end_date.data)).group_by(
        Transaction.category, func.strftime("%Y-%m", Transaction.date)).order_by(Transaction.date.asc()).all()

        for trx in account_trx:
            if trx.month not in range_desc:
                range_desc.append(trx.month)
            if trx.name not in cat_range:
                cat_range.append(trx.name)
            if trx.budget not in bdgt_range:
                bdgt_range.append(trx.budget)

        for trx in account_trx:
            if trx.name not in trx_by_cat:
                trx_by_cat[trx.name] = [None] * len(range_desc)
            month_idx = range_desc.index(trx.month)
            trx_by_cat[trx.name][month_idx] = trx.sum

    return render_template('index.html', title='Mooney', form=form, 
        balance_by_type=balance_by_type, range_desc=range_desc,
        cat_range=cat_range, bdgt_range=bdgt_range, trx_by_cat=trx_by_cat)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form = form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    form = AddAccountForm()
    if form.validate_on_submit():
        account = Account(name=form.name.data, type=form.type.data, currency=form.currency.data,
                       description=form.description.data, start_balance=form.start_balance.data, 
                       balance_date=form.balance_date.data, user_id=current_user.id)
        db.session.add(account)
        db.session.commit()
        flash('An account was just added!')
        return redirect(url_for('accounts'))
    return render_template('add_account.html', title='Add Account', form=form)

@app.route('/accounts', methods=['GET', 'POST'])
@login_required
def accounts():
    form = {"name":"text", "type":"text", "currency":"text", "description":"text", "start_balance":"float", "balance_date":"date", "balance_archive":"text"}
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    for account in accounts:       
        account.balance = get_single_balance(account)
    if request.method == 'POST':
        acc = Account.query.filter_by(id=request.form['id']).first()
        acc.name = request.form['name']
        acc.type = request.form['type']
        acc.currency = request.form['currency']
        acc.description = request.form['description']
        acc.start_balance = request.form['start_balance']
        acc.balance_date = datetime. strptime(request.form['balance_date'], '%Y-%m-%d')
        acc.balance_archive = request.form['balance_archive']
        acc.last_modified = datetime.utcnow()
        db.session.commit()
    return render_template('accounts.html', title='Accounts', accounts=accounts, form=form)

@app.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        #Competence is not yet an option
        category = Category(name=form.name.data, type=form.type.data, description=form.description.data, 
                            budget=form.budget.data, user_id=current_user.id, icon=form.icon.data)
        db.session.add(category)
        db.session.commit()
        flash('An category was just added!')
        return redirect(url_for('categories'))
    return render_template('add_category.html', title='Add Category', form=form)

@app.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    form = {"name":"text", "type":"text", "description":"text", "budget":"float"}
    categories = Category.query.filter_by(user_id=current_user.id)
    if request.method == 'POST':
        cat = Category.query.filter_by(id=request.form['id']).first()
        cat.name = request.form['name']
        cat.type = request.form['type']
        cat.description = request.form['description']
        cat.budget = request.form['budget']
        cat.last_modified = datetime.now()
        db.session.commit()
    return render_template('categories.html', title='Categories', categories=categories, form=form)

@app.route('/add_transactions', methods=['GET', 'POST'])
@login_required
def add_transaction():
    form = TransactionForm()
    if form.validate_on_submit():
        #Competence is not yet an option
        #think about transaction signs
        transaction = Transaction(account=form.account.data.id, category=form.category.data.id, amount=form.amount.data, 
                                  currency=form.account.data.currency, date=form.date.data, 
                                  description=form.description.data, tag=form.tag.data, user_id=current_user.id)
        db.session.add(transaction)
        db.session.commit()
        flash('A transaction was just added!')
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('accounts')
        return redirect(next_page)
    #showing not limited to the user
    return render_template('add_transaction.html', title='Add Transaction', form=form)

@app.route('/add_transfer', methods=['GET', 'POST'])
@login_required
def add_transfer():
    form = TransferForm()
    if form.validate_on_submit():
        transfer = Transfer(source_account=form.source_account.data.id, target_account=form.target_account.data.id,  
                            date=form.date.data, amount=form.amount.data, currency=form.target_account.data.currency, 
                            description=form.description.data)
        db.session.add(transfer)
        db.session.commit()
        flash('A transfer was just added!')
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('accounts')
        return redirect(next_page)
    #showing not limited to the user
    return render_template('add_transfer.html', title='Add Transfer', form=form)

@app.route('/account_detail/<account>', methods=['GET', 'POST'])
@login_required
def account_detail(account):
    form = SelectDateForm()

    account_ = Account.query.filter_by(name=account).filter_by(user_id=current_user.id).first()
 
    account_trx = db.session.query(Transaction.amount.label('amount'), Transaction.date.label('date'), Category.name.label('name'), Transaction.tag.label('tag')).join(
        Category, Category.id == Transaction.category).filter(Transaction.account.in_([account_.id])).filter(
        Transaction.date.between(form.start_date.data, form.end_date.data)).order_by(Transaction.date.desc()).all()
    
    balance = get_single_balance(account_)

    bal_recon = float(form.amount.data or 0.0)
    diff = bal_recon - balance
    try: 
        diff_p = round((diff/bal_recon)*100, 2)
    except ZeroDivisionError:
        diff_p = 0
    
    return render_template('account_detail.html', title=account, account_type=account_.type, form=form, account_trx=account_trx, 
                           balance=balance, bal_recon=bal_recon, diff=diff, diff_p=diff_p)

@app.route('/update_balance', methods=['GET', 'POST'])
@login_required
def update_balance():
    form = UpdateBalanceForm()

    if form.validate_on_submit():
        account_ =  Account.query.filter_by(user_id=current_user.id).filter_by(name=form.account.data.name).first()
        
        new = {}
        d = form.date.data
        d = d.strftime("%Y-%m")
        new[d] = []
        new[d] = [form.amount.data,
                                form.description.data]

        if account_.balance_archive:
            for k, v in json.loads(account_.balance_archive).items():
                new[k] = v
            a = json.dumps(new, default=str)
            account_.balance_archive = a
        else:
            a = json.dumps(new, default=str)
            account_.balance_archive = a
        
        db.session.commit()
        flash('A balance was just added!')
        return redirect(url_for('balance_view'))

    return render_template('update_balance.html', title='Update Balance', form=form)

@app.route('/balance_view', methods=['GET', 'POST'])
@login_required
def balance_view():
    form = DateTypeForm()
    month_range = []
    acc_range = []
    
    balance_by_type = get_balance_by_type()

    #BALANCES EVOLUTION MONTHLY BASED ON FORM SELECTION
    if form.validate_on_submit():
        accounts = db.session.query(Account.id, Account.name, Account.type,Account.start_balance, Account.balance_archive, 
                                 Account.created_at).filter(Account.type.in_(form.type.data)).filter_by(user_id=current_user.id).all()
        month_range = pd.date_range(form.start_date.data,form.end_date.data, 
              freq='MS').strftime("%Y-%m").tolist()
        
        acc_trimmed = {}

        for acc in accounts:
            acc_trimmed[acc.name] = {}

            if acc.name not in acc_range:
                acc_range.append(acc.name)

            if acc.type == 'Investment':
                for idx, m in enumerate(month_range): 
                    acc_trimmed[acc.name][m] = acc.start_balance
                    
                    try:
                        acc_= json.loads(acc.balance_archive)
                        acc_= collections.OrderedDict(sorted(acc_.items()))
                    except:
                        acc_= False

                    if acc_:
                        #{2023-03-23: [1000, "balbalba"], 2023-04-23: [1000, "balbalba"]}
                        if m in acc_:
                            acc_trimmed[acc.name][m] = acc_[m][0]
                        else:
                            if idx-1 >= 0:
                                acc_trimmed[acc.name][m] = acc_trimmed[acc.name][month_range[idx-1]]

            else:
                transaction_balance = db.session.query(func.sum(Transaction.amount), 
                    func.strftime("%Y-%m", Transaction.date).label('month')).filter(Transaction.account.in_([acc.id])).group_by(func.strftime("%Y-%m",
                    Transaction.date).label('month')).all()

                trf_negative = db.session.query(func.sum(Transfer.amount),
                    func.strftime("%Y-%m", Transfer.date).label('month')).filter(Transfer.source_account.in_([acc.id])).group_by(func.strftime("%Y-%m",
                    Transfer.date).label('month')).all()
                
                trf_positive = db.session.query(func.sum(Transfer.amount),
                    func.strftime("%Y-%m", Transfer.date).label('month')).filter(Transfer.target_account.in_([acc.id])).group_by(func.strftime("%Y-%m",
                    Transfer.date).label('month')).all()
                
                start_balance = db.session.query(func.sum(Account.start_balance),
                    func.strftime("%Y-%m", Account.created_at).label('month')).filter(Account.id.in_([acc.id])).group_by(func.strftime("%Y-%m",
                    Account.created_at).label('month')).all()

                for idx, m in enumerate(month_range): 
                    #(2023-04, 1000)
                    tr_ = 0.0
                    trf_n = 0.0
                    trf_p = 0.0
                    sb_ = 0.0

                    for tr in transaction_balance:
                        if m in tr:
                            tr_ = tr[0]

                    for tn in trf_negative:
                        if m in tn:
                            trf_n = tn[0]

                    for tp in trf_positive:
                        if m in tp:
                            trf_p = tp[0]

                    for sb in start_balance:
                        if m in sb:
                            sb_ = sb[0]

                    transfer_balance = float(trf_p) - float(trf_n)
                    balance = float(sb_) + float(tr_) + transfer_balance
                    if idx-1 >= 0:
                        acc_trimmed[acc.name][m] = balance + acc_trimmed[acc.name][month_range[idx-1]]
                    else: 
                        acc_trimmed[acc.name][m] = balance
                    #Structure {N26: [03-2022:1000, 04-2023:2000, 05-2023:2500]}

        return render_template('balance_view.html', title='Balance View', form=form, balance_by_type=balance_by_type, month_range=month_range, acc_range=acc_range, acc_trimmed=acc_trimmed)     
    return render_template('balance_view.html', title='Balance View', form=form,balance_by_type=balance_by_type, month_range=month_range, acc_range=acc_range)

    #Information needed, Accounts.Names, Balance by Month, Month Range

@app.route('/transactions', methods=['GET', 'POST'])
@login_required
def transactions():
    form = DateAccountForm()
    form_id = {"acc":"text", "category":"text", "amount":"float", "currency":"text", "date":"date", "created_at":"date", "tag":"text", "description":"text"}

    accounts = [id[0] for id in db.session.query(Account.id).filter_by(user_id=current_user.id).all()]
    
    if form.validate_on_submit():
        accounts = [form.account.data.id]

    transactions = db.session.query(Transaction.id, Transaction.date, Transaction.amount, Transaction.currency  , Account.name.label('acc'), Category.name.label('category'), Transaction.tag, 
        Transaction.description, Transaction.created_at).join(Account, Account.id == Transaction.account).join(
        Category, Category.id == Transaction.category).filter(Transaction.account.in_(accounts)).filter(
    Transaction.date.between(form.start_date.data, form.end_date.data)).order_by(Transaction.date.desc()).all()

    return render_template('transactions.html', title='Transactions', form=form, transactions=transactions, form_id=form_id)

@app.route('/transactions/edit', methods=['POST'])
@login_required
def transactions_edit():
    trx = Transaction.query.filter_by(id=request.form['id']).first()
    trx.account = db.session.query(Account.id).filter_by(user_id=current_user.id).filter_by(name=request.form['acc']).first()[0]
    trx.category = db.session.query(Category.id).filter_by(user_id=current_user.id).filter_by(name=request.form['category']).first()[0]
    trx.amount = request.form['amount']
    trx.currency = request.form['currency']
    trx.date = datetime.strptime(request.form['date'], '%Y-%m-%d')
    trx.created_at = datetime.utcnow()
    trx.tag = request.form['tag']
    trx.description = request.form['description']
    db.session.commit()

    return redirect(url_for('transactions'), code=307)

@app.route('/charts', methods=['GET', 'POST'])
@login_required
def charts():
    form = SelectDateForm()
    balance_by_type = get_balance_by_type()

    today = date.today()
        
    if form.validate_on_submit():
        st = form.start_date.data
        ed = form.end_date.data
        start_date = st.replace(day = 1)
        end_date = ed.replace(day = calendar.monthrange(ed.year, ed.month)[1])
    else:
        today = date.today()
        first = today.replace(day=1)
        end_date = first - timedelta(days=1)
        start_date = end_date.replace(day=1)

    labels = ["Income", "Expense", "Net"]
    values = get_category_balance(start_date, end_date)

    income_keys, income_values, expense_keys, expense_values = get_category_type_balance(start_date, end_date)

    return render_template('charts.html', title='Chart', form=form, end_date=end_date, start_date=start_date, balance_by_type=balance_by_type,
                           labels=labels, values=values, income_keys=income_keys, income_values=income_values, expense_keys=expense_keys, expense_values=expense_values)

#TRANSACTION_EDIT SHOULD KEEP THE FORMER VIEW
#ADD TRANSACTION FORM SHOULD HAVE AN OPTION TO SAVE + ADD ANOTHER TRANSACTION
#HOME, BALANCE, TRANSACTION SHOULD HAVE A PRE-POPULATED FILTER, SO IT DOESN"T SHOW EMPTY
#TRANSACTIONS SHOULD HAVE A FILTER FOR CATEGORIES
    #HOME CATEGORIES SHOULD POINT TO TRANSACTION URL
#IMPLEMENT ERRORS AS PER MEGATUTORIAL
#IMPLEMENT FORGOT PASSWORD AND EMAIL VALIDATION AS PER MEGATUTORIAL
#IMPLEMENT LOGGING
#IMPLEMENT BLUEPRINT AS PER MEGATUTORIAL
#IMPLEMENT MYSQL WAY OF WORKING
#DEPLOY