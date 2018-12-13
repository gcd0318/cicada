from config import MIN_FREE_SPACE
from const import NodeStatus
from model import db, logger
from models.nodemanager import NodeManager

import datetime

class Node(db.Model):
    __tablename__ = 'nodes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hostname = db.Column(db.String(64), default='', nullable=True)
    ip = db.Column(db.String(16), default='127.0.0.1', nullable=False, unique=True)
    port = db.Column(db.Integer, nullable=False, default=22)
    username = db.Column(db.String(64), default='cicada', nullable=True)
    password = db.Column(db.String(1024), default='', nullable=True)
    status = db.Column(db.Integer, default=NodeStatus.NA)
    last_updated = db.Column(db.TIMESTAMP, nullable=False, onupdate=datetime.datetime.now,
                             default=datetime.datetime.now)
    manager = NodeManager()

    def to_json(self):
        return {
            'hostname': self.hostname or self.ip,
            'ip': self.ip,
            'status': self.status,
            'free_space': self.manager.get_free_space()
        }

    def __str__(self):
        return str(self.to_json())

    def init(self):
        accessibles, free = self.manager.init()
        if False in accessibles.values():
            self.status = NodeStatus.NA
        if (MIN_FREE_SPACE < free):
            self.status = NodeStatus.READY
        elif (MIN_FREE_SPACE >= free):
            self.status = NodeStatus.FULL
        db.session.commit()
        return accessibles, free