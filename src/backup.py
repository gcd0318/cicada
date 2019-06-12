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
    rs = node.manager.read_from_redis_str()
    status = rs.get('status')
    accesses = rs.get('accesses')
    free = rs.get('free')
    files = rs.get('files')
    res = True
#    tasks = node.manager.read_from_redis_dict('cp_tasks', 'filename')
    encrypt = node.manager.redis.lpop('cp_tasks')
    while encrypt is not None:
        filepath, size, copy_num, target_copy = node.manager.read_from_redis_dict(encrypt, ['filename size copy_num target_copy'])
        print(filepath, size, copy_num, target_copy)
#    for task in tasks:
#        size = node.manager.redis.read_from_redis_dict(encrypt, 'size')
#        copy_num = node.manager.redis.read_from_redis_dict(encrypt, 'copy_num')
#        target_copy = node.manager.redis.read_from_redis_dict(encrypt, 'target_copy')
        tgt_ip = None
        margin = -1
        for ip in CLUSTER:
            node_info = node.manager.read_redis_str(ip)
            if node_info is not None:
                new_margin = node_info.get('free')['BACKUP'] - MIN_FREE_SPACE - size
                if (0 < new_margin) and (margin < new_margin):
                    tgt_ip = ip
                    margin = new_margin
        if tgt_ip is not None:
            ts = time.time
            node.manager.redis.insert_or_update_list('cp_tasks', ts)
            node.manager.redis.insert_or_update_dict(ts, {'from': filepath, 'to': tgt_ip})
            print(ts)

        remote_cp(filepath, tgt_ip)
        rs['files'][filepath]['copy_num'] = copy_num + 1

#        if remote_cp(task['from'], task['to']) is not None:
#            pass
        encrypt = node.manager.redis.lpop('cp_tasks')

if ('__main__' == __name__):
    node = Node()
    while True:
        backup(node)