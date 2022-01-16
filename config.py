import os
from dotenv import load_dotenv

basedir = os.path.abspath( os.path.dirname(__file__) )
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join( basedir, 'DB', 'app.db' )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    ADMINS = ['cocchi.e89@gmail.com']
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    MONGO_URL = os.environ.get('MONGO_URL') or 'mongodb://127.0.0.1:27017'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join( basedir, 'upload' )
    ALLOWED_EXTENSIONS = [ '.vcf', '.gz', '.txt', '.gl' ]
    SERVER_ADDRESS = os.environ.get('SERVER_ADDRESS')
    TOKEN_EXP_SEC = os.environ.get('TOKEN_EXP_SEC') or 3600
    TOKEN_RESTORE_EXP_SEC = os.environ.get('TOKEN_RESTORE_EXP_SEC') or 1800
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    MESSAGE_PER_PAGE = os.environ.get('MESSAGE_PER_PAGE') or 10
    LOGIN_DISABLED = True if os.environ.get('LOGIN_DISABLED') == "1" else False
    DEVELOPMENT_TESTING = True if os.environ.get('DEVELOPMENT_TESTING') == "1" else False
    JSON_FOLDER = os.environ.get('JSON_FOLDER') or os.path.join( basedir, 'JSON' )
