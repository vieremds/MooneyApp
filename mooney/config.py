import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    #DB URL should come on deployment, or be by default the dev env one
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://mooney_root:rBuV9pTRG?Ik>LMK{cbZ3d{TR]K4@mooney-db-dev.chqdptrep2oh.us-east-2.rds.amazonaws.com/postgres')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
    ACCOUNT_TYPES = ['Giro','Liability','Investment','History']
    CURRENCIES = [('EUR', 'Euro'), ('BRL', 'Brasilian-Real'), ('USD', 'Dollar'), ('GBP','British-Pounds')]
    CATEGORY_TYPES = ['All','Income','Expense']
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    MONTHS = ['January','February','March', 'April','May','June','July','August','September','October','November','December']
    CACHE_TYPE = "SimpleCache"