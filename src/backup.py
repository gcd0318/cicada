#!/usr/bin/python

from config import DNS, INCOMING, BACKUP, COPIES, BLANK, CLUSTER, MIN_FREE_SPACE, USERNAME, PASSWORD
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
    encrypt = node.manager.redis.lpop('cp_tasks')
    print(encrypt)
    while encrypt is not None:
        filepath, size_str, copy_num_str, target_copy = node.manager.read_from_redis_dict(encrypt, ['filename', 'size', 'copy_num', 'target_copy'])
#        if filepath is not None:
        print(filepath, size_str, copy_num_str, target_copy)
        size = int(size_str)
        copy_num = int(copy_num_str)
        tgt_ip = None
        margin = -1
        for ip in CLUSTER:
            node_info = node.manager.read_redis_str(ip)
            if node_info is not None:
                print(size)
                new_margin = node_info.get('free')['BACKUP'] - MIN_FREE_SPACE - size
                if (0 < new_margin) and (margin < new_margin):
                    tgt_ip = ip
                    margin = new_margin
        if tgt_ip is not None:
            ts = time.time()
            node.manager.redis.insert_or_update_list('cp_tasks', ts)
            node.manager.redis.insert_or_update_dict(ts, {'from': filepath, 'to': tgt_ip})
            print(ts)

        print(remote_cp(filepath, USERNAME + ':' + PASSWORD + '@' + tgt_ip + '@' + BACKUP))
        copy_num = copy_num + 1
        rs['files'][filepath]['copy_num'] = copy_num
        node.manager.write_to_redis()
        if copy_num < target_copy:
            node.manager.redis.insert_or_update_list('cp_tasks', encrypt)
            node.manager.redis.insert_or_update_dict(encrypt, {'filename': filepath,
                                                               'copy_num': copy_num,
                                                               'target_copy': target_copy,
                                                               'size': size})

        encrypt = node.manager.redis.lpop('cp_tasks')
        print('encrypt', encrypt)

if ('__main__' == __name__):
    node = Node()
    while True:
        backup(node)