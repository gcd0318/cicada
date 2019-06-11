#!/usr/bin/python

from config import DNS, INCOMING, BACKUP, COPIES, BLANK, CLUSTER, MIN_FREE_SPACE
from const import NodeStatus
from utils import get_func, get_path_size, get_encrypt, scan ,deep_scan, pathize, local_cp, remote_cp
from model import logger, db
from models.filepath import FilePath
from models.node import Node
import threading

import os
import time

def backup(node, tgt=BACKUP):
    task_ts = node.manager.redis.lpop('cp_tasks')
    print(task_ts)
    task = node.manager.redis.hgetall(task_ts)
    if task is not None:
        print(task)
        remote_cp(task['from'], task['to'])
#        if remote_cp(task['from'], task['to']) is not None:
#            pass

if ('__main__' == __name__):
    node = Node()
    while True:
        backup(node)