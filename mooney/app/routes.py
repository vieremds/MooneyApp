from flask import render_template, flash, redirect, url_for, request, session
from app import app, db
from app.forms import LoginForm, RegistrationForm, AddAccountForm, CategoryForm, TransactionForm, TransferForm, SelectDateForm, DateTypeForm, UpdateBalanceForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Account, Category, Transaction, Transfer
from werkzeug.urls import url_parse
from sqlalchemy import func
from config import Config
import pandas as pd 

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = DateTypeForm()

    types = Config.ACCOUNT_TYPES
    balance_by_type = {}

    for type in types:
        account = [id[0] for id in db.session.query(Account.id).filter_by(type=type).filter_by(user_id=current_user.id).all()]

        #BALANCE ON TOP STUFF
        transaction_balance = Transaction.query.filter(Transaction.account.in_(account)).with_entities(func.sum(Transaction.amount).label('total')).first().total
        trf_negative = Transfer.query.filter(Transfer.source_account.in_(account)).with_entities(func.sum(Transfer.amount).label('total')).first().total
        trf_positive = Transfer.query.filter(Transfer.target_account.in_(account)).with_entities(func.sum(Transfer.amount).label('total')).first().total
        start_balance = Account.query.filter(Account.id.in_(account)).with_entities(func.sum(Account.start_balance).label('total')).first().total

        transfer_balance = float(trf_positive or 0.0) - float(trf_negative or 0.0)
        balance = float(start_balance or 0.0) + float(transaction_balance or 0.0) + transfer_balance
        balance_by_type[type] = balance
  
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

        print(account_trx)

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
                       user_id=current_user.id)
        db.session.add(account)
        db.session.commit()
        flash('An account was just added!')
        return redirect(url_for('accounts'))
    return render_template('add_account.html', title='Add Account', form=form)

@app.route('/accounts', methods=['GET'])
@login_required
def accounts():
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    for account in accounts: 
        transaction_balance = Transaction.query.filter_by(account=account.id).with_entities(func.sum(Transaction.amount).label('total')).first().total
        trf_negative = Transfer.query.filter_by(source_account=account.id).with_entities(func.sum(Transfer.amount).label('total')).first().total
        trf_positive = Transfer.query.filter_by(target_account=account.id).with_entities(func.sum(Transfer.amount).label('total')).first().total
    #think about transaction signs
        transfer_balance = float(trf_positive or 0.0) - float(trf_negative or 0.0)
        balance = account.start_balance + float(transaction_balance or 0.0) + transfer_balance
        account.balance = balance
    #think about filters
    return render_template('accounts.html', title='Accounts', accounts=accounts)

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

@app.route('/categories', methods=['GET'])
@login_required
def categories():
    categories = Category.query.filter_by(user_id=current_user.id)
    return render_template('categories.html', title='Categories', categories=categories)

@app.route('/add_transactions', methods=['GET', 'POST'])
@login_required
def add_transaction():
    form = TransactionForm()
    if form.validate_on_submit():
        #Competence is not yet an option
        #think about transaction signs
        transaction = Transaction(account=form.account.data.id, category=form.category.data.id, amount=form.amount.data, 
                                  currency=form.account.data.currency, date=form.date.data, 
                                  description=form.description.data, tag=form.tag.data)
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

    account_ids = db.session.query(Account.id).filter_by(name=account).first()
    account_type = db.session.query(Account.type).filter_by(name=account).first()
    print(account_type[0])
    #ACCOUNT TYPE IS BEING PASSED LIKE THIS ('Investment',)
    
    account_trx = db.session.query(Transaction.amount.label('amount'), Transaction.date.label('date'), Category.name.label('name'), Transaction.tag.label('tag')).join(
        Category, Category.id == Transaction.category).filter(Transaction.account.in_(account_ids)).filter(
        Transaction.date.between(form.start_date.data, form.end_date.data)).order_by(Transaction.date.desc()).all()

    transaction_balance = Transaction.query.filter(Transaction.account.in_(account_ids)).with_entities(func.sum(Transaction.amount).label('total')).first().total
    trf_negative = Transfer.query.filter(Transfer.source_account.in_(account_ids)).with_entities(func.sum(Transfer.amount).label('total')).first().total
    trf_positive = Transfer.query.filter(Transfer.target_account.in_(account_ids)).with_entities(func.sum(Transfer.amount).label('total')).first().total
    start_balance = Account.query.filter(Account.id.in_(account_ids)).with_entities(func.sum(Account.start_balance).label('total')).first().total

    transfer_balance = float(trf_positive or 0.0) - float(trf_negative or 0.0)
    balance = float(start_balance or 0.0) + float(transaction_balance or 0.0) + transfer_balance
    
    bal_recon = float(form.amount.data or 0.0)
    diff = bal_recon - balance
    try: 
        diff_p = round((diff/bal_recon)*100, 2)
    except ZeroDivisionError:
        diff_p = 0
    
    return render_template('account_detail.html', title=account, account_type=account_type, form=form, account_trx=account_trx, 
                           balance=balance, bal_recon=bal_recon, diff=diff, diff_p=diff_p)

@app.route('/update_balance', methods=['GET', 'POST'])
@login_required
def update_balance():
    form = UpdateBalanceForm()

    if form.validate_on_submit():
        account_ =  Account.query.filter_by(user_id=current_user.id).filter_by(name=form.account.data).first()
        
        new = (form.date.data, form.amount.data, form.description.data)
        
        if account_.balance_archive:
            account_.balance_archive.add(new)
        else:
            account_.balance_archive = {new}
        db.session.commit()
        flash('A balance was just added!')
        return redirect(url_for('account_detail'))

    return render_template('update_balance.html', title='Update Balance', form=form)

@app.route('/balance_view', methods=['GET', 'POST'])
@login_required
def balance_view():
    form = DateTypeForm()
    month_range = []
    acc_range = []
    
    #BALANCE ON TOP STUFF / CURRENT BALANCE
    types = Config.ACCOUNT_TYPES
    balance_by_type = {}

    for type in types:
        account = [id[0] for id in db.session.query(Account.id).filter_by(type=type).filter_by(user_id=current_user.id).all()]

        transaction_balance = Transaction.query.filter(Transaction.account.in_(account)).with_entities(func.sum(Transaction.amount).label('total')).first().total
        trf_negative = Transfer.query.filter(Transfer.source_account.in_(account)).with_entities(func.sum(Transfer.amount).label('total')).first().total
        trf_positive = Transfer.query.filter(Transfer.target_account.in_(account)).with_entities(func.sum(Transfer.amount).label('total')).first().total
        start_balance = Account.query.filter(Account.id.in_(account)).with_entities(func.sum(Account.start_balance).label('total')).first().total

        transfer_balance = float(trf_positive or 0.0) - float(trf_negative or 0.0)
        balance = float(start_balance or 0.0) + float(transaction_balance or 0.0) + transfer_balance
        balance_by_type[type] = balance

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
                #acc_list = db.session.query(Account.name, Account.start_balance, Account.balance_archive, Account.created_at).filter(Account.id.in_([acc.id])).all()
                
                #Structure {N26:[03-2022:1000, 04-2023:2000, 05-2023:2500]}
                #for acc_ in acc_list:
                for idx, m in enumerate(month_range): 
                    acc_trimmed[acc.name][m] = acc.start_balance
                    if acc.balance_archive:
                        for k in acc.balance_archive:
                            if m == func.strftime("%Y-%m", k[0]):
                                acc_trimmed[acc.name][m] = k[1]
                            else:
                                if idx-1 >= 0:
                                    acc_trimmed[acc.name][m] = acc_trimmed[acc.name][month_range[idx-1]]

            else:
                transaction_balance = db.session.query(func.sum(Transaction.amount), 
                    func.strftime("%Y-%m", Transaction.date).label('month')).filter(Transaction.account.in_([acc.id])).group_by(func.strftime("%Y-%m",
                    Transaction.date).label('month')).all()
                
                print(transaction_balance)

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
        print(acc_trimmed)

        return render_template('balance_view.html', title='Balance View', form=form, balance_by_type=balance_by_type, month_range=month_range, acc_range=acc_range, acc_trimmed=acc_trimmed)     
    return render_template('balance_view.html', title='Balance View', form=form,balance_by_type=balance_by_type, month_range=month_range, acc_range=acc_range)

    #Information needed, Accounts.Names, Balance by Month, Month Range

#think about investment accounts, add balance to them, display that shit with filters


#NO TRANSACTIONS FOR INVESTMENT ACCOUNTS
#THERE ARE TRANSFERS, BUT THESE ARE NOT INCLUDED IN THE BALANCE AS 
#BALANCE ARCHIVE IS THE SINGLE SOURCE OF TRUTH FOR INVESTMENT ACCOUNTS BALANCE

