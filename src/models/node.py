from config import MIN_FREE_SPACE, CLUSTER
from const import NodeStatus
from model import db, logger
from models.node_manager import NodeManager
from utils import get_local_ip, get_local_hostname

import datetime

class Node():
    def __init__(self):
        self.manager = NodeManager()
        self.ip = get_local_ip()
        self.hostname = get_local_hostname()

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
            if False in self.manager.get_accesses().values():
                status = NodeStatus.NA
            else:
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
