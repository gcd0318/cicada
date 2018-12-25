from config import MIN_FREE_SPACE
from const import NodeStatus
from model import db, logger
from models.node_manager import NodeManager

import datetime

node_filepath_xref = db.Table('node_filepath_xrefs',
                              db.Column('node_id', db.Integer, db.ForeignKey('nodes.id')),
                              db.Column('fp', db.String(1024), db.ForeignKey('filepaths.fp'))
                              )
class FilePath(db.Model):
    __tablename__ = 'filepaths'

    fp = db.Column(db.String(1024), nullable=False)
    nodes = db.relationshuo('Node', secondary=node_filepath_xref, lazy='dynamic',
                            backref=db.backref('nodes', lazy='dynamic'))
    last_updated = db.Column(db.TIMESTAMP, nullable=False, onupdate=datetime.datetime.now,
                             default=datetime.datetime.now)

    