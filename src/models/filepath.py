from config import DEF_LEVEL
from model import db, logger
from utils import get_encrypt

import datetime

class FilePath(db.Model):
    __tablename__ = 'filepaths'

    filepath = db.Column(db.String(1024), nullable=False)
    fp_encrypt = db.Column(db.String(128), nullable=False, unique=True, primary_key=True)
    node_ip = db.Column(db.String(15), unique=True, primary_key=True)
    level = db.Column(db.Integer, default=DEF_LEVEL)
    encrypt = db.Column(db.String(32), nullable=False)
    last_updated = db.Column(db.TIMESTAMP, nullable=False, onupdate=datetime.datetime.now,
                             default=datetime.datetime.now)
