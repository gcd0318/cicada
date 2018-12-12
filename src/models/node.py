from config import DEF_PATHS
from const import NA, READY, FULL
from model import db, logger
from utils import get_disk_usage

import datetime
import os

class Node(db.Model):
    __tablename__ = 'nodes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hostname = db.Column(db.String(64), default='', nullable=True)
    ip = db.Column(db.String(16), default='127.0.0.1', nullable=False, unique=True)
    port = db.Column(db.Integer, nullable=False, default=22)
    username = db.Column(db.String(64), default='cicada', nullable=True)
    password = db.Column(db.String(1024), default='', nullable=True)
    status = db.Column(db.Integer, default=NA)
    last_updated = db.Column(db.TIMESTAMP, nullable=False, onupdate=datetime.datetime.now,
                             default=datetime.datetime.now)

    def to_json(self):
        return {
            'id': self.id,
            'hostname': self.hostname or self.ip,
            'ip': self.ip,
            'status': self.status,
            'disk_space': self.get_free_space()
        }

    def init(self):
        access_ok = {}
        for path in DEF_PATHS:
            access_ok[path] = os.path.isdir(DEF_PATHS[path]) and os.access(DEF_PATHS[path], os.R_OK|os.W_OK)
        return access_ok

    def scan(self, root=DEF_PATHS['INCOMING']):
        resl = []
        root = os.path.abspath(root)
        if os.path.isdir(root):
            if not(root.endswith(os.sep)):
                root = root + os.sep
            for dirpath, dirnames, filenames in os.walk(root):
                for filepath in filenames:
                    resl.append(os.path.join(dirpath, filepath))
        else:
            resl.append(root)
        return resl

    def get_free_space(self):
        total, used, free = get_disk_usage('/mnt/sda1')
        if (1024 * 1024 >= free):
            self.status = FULL
            db.session.commit()
        return free

if ('__main__' == __name__):
    print(Node.to_json())