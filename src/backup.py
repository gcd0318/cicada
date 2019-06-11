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
    for task in (node.manager.read_redis(k='cp_tasks') or []):
        print(task)
#           remote_cp(task['from'], task['to'])

if ('__main__' == __name__):
    node = Node()
    while True:
        backup(node)