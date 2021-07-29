#from config import ITEMS_PER_PAGE

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import logging.handlers

logger = logging.getLogger()
fh = logging.handlers.TimedRotatingFileHandler('../log/cicada.log', "D", 1, 10)
fh.setFormatter(
    logging.Formatter('%(asctime)s %(filename)s_%(lineno)d: [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S'))
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)

# app = Flask(__name__)
app = Flask('cicada')

#app.config['ARTISAN_POSTS_PER_PAGE'] = ITEMS_PER_PAGE
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://cicada:cicada@localhost:3306/cicada?charset=utf8&autocommit=true'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


