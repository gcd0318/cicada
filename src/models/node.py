from const import NodeStatus
from models import db, logger
from models.node_manager import NodeManager
from gcutils.netops import get_local_ip, get_local_hostname

import json

class Node(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(80), unique=True)
    free_limit = db.Column(db.Integer)
    manager = db.relationship('NodeManager', backref='manager', lazy='dynamic')
#class Node():
    def __init__(self, free_limit):
        self.manager = NodeManager()
        self.hostname = get_local_hostname()
        self.free_limit = free_limit

    def __str__(self):
        self.refresh()
        res = {
            'hostname': self.hostname or self.manager.ip,
            'ip': self.manager.ip,
            'status': self.manager.get_status(),
            'free_space': self.manager.get_free_space(),
            'accessibles': self.manager.get_accesses()
        }
        return json.dumps(res)

    def refresh(self):
        self.manager.set_free_space()
        self.manager.set_accesses()
        status = NodeStatus.NA
        try:
            if not(False in self.manager.get_accesses().values()):
                free = self.manager.get_free_space()
                if (self.free_limit < free.get('INCOMING'))and((MIN_FREE_SPACE < free.get('BACKUP'))):
                    status = status + NodeStatus.READY
                else:
                    if (self.free_limit >= free.get('INCOMING')):
                        status = status + NodeStatus.INCOMING_FULL
                    if (self.free_limit >= free.get('BACKUP')):
                        status = status + NodeStatus.BACKUP_FULL
        except Exception as err:
            import traceback
            logger.error(__name__)
            logger.error(err)
            logger.error(traceback.format_exc())
        finally:
            self.manager.set_status(status)
