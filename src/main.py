#from config import ITEMS_PER_PAGE

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

#app.config['ARTISAN_POSTS_PER_PAGE'] = ITEMS_PER_PAGE
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://cicada:cicada@localhost:3306/cicada?charset=utf8&autocommit=true'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def logger(logfile='cicada.log'):
    import logging.handlers

    log = logging.getLogger()
    fh = logging.handlers.TimedRotatingFileHandler(logfile, "D", 1, 10)
    fh.setFormatter(
        logging.Formatter('%(asctime)s %(filename)s_%(lineno)d: [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S'))
    log.addHandler(fh)
    log.setLevel(logging.DEBUG)

