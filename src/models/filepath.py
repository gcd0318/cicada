from . import db, logger

import datetime

class FilePath(db.Model):
    __tablename__ = 'filepaths'

    id = db.Column(db.Integer, primary_key=True)
    filepath = db.Column(db.String(4096), nullable=False)
    fp_encrypt = db.Column(db.String(128), nullable=False)
    node_ip = db.Column(db.String(15))
#    level = db.Column(db.Integer, default=DEF_LEVEL)
    encrypt = db.Column(db.String(4096), nullable=False)
    last_updated = db.Column(db.TIMESTAMP, nullable=False, onupdate=datetime.datetime.now, default=datetime.datetime.now)
