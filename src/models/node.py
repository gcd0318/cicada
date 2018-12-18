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
    last_updated = db.Column(db.TIMESTAMP, nullable=False, onupdate=datetime.datetime.now,
                             default=datetime.datetime.now)
    manager = NodeManager()

    def to_json(self):
        self.refresh()
        return {
            'hostname': self.hostname or self.ip,
            'ip': self.ip,
            'status': self.manager.get_status(),
            'free_space': self.manager.get_free_space(),
            'accessibles': self.manager.get_accesses()
        }

    def __str__(self):
        return str(self.to_json())

    def refresh(self):
        self.manager.set_free_space()
        self.manager.set_accesses()
        status = NodeStatus.NA
        try:
            if not(False in self.manager.get_accesses().values()):
                free = self.manager.get_free_space()
                if (MIN_FREE_SPACE < free):
                    status = NodeStatus.READY
                elif (MIN_FREE_SPACE >= free):
                    status = NodeStatus.FULL
        except Exception as err:
            import traceback
            logger.error(str(err))
            logger.error(traceback.format_exc())
        finally:
            self.manager.set_status(status)
