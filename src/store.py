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

#@get_func
def refresh(node):
    node.refresh()

#@get_func
def incoming_to_redis(node):
    data = _threading_incoming_to_redis(node.manager.read_from_redis_str().get('files', {}))
    return node.manager.write_to_redis('files', data)

def _threading_incoming_to_redis(data):
    threads = []

    def runner(filepath):
        filedata = {'copy_num': 0}
        if filepath in data:
            filedata = data[filepath]
        old_encrypt = filedata.get('encrypt', '')
        new_encrypt = get_encrypt(filepath)
        if (old_encrypt != new_encrypt):
            while(old_encrypt != new_encrypt):
                time.sleep(1)
                old_encrypt = new_encrypt
                new_encrypt = get_encrypt(filepath)
            filedata['encrypt'] = new_encrypt
            filedata['size'] = get_path_size(filepath)

            target_copy = COPIES
            try:
                target_copy = int(filepath.split(os.sep)[-2])
            except Exception as err:
                logger.warning(err)
                logger.warning('use default target_cpoy: ' + str(COPIES))
            finally:
                pass
            filedata['target_copy'] = target_copy
            filedata['copy_num'] = 0
            data[filepath] = filedata

    for filepath in scan():
        _t = threading.Thread(
            target=runner,
            args=(filepath,)
        )
        _t.start()
        threads.append(_t)
    for _t in threads:
        _t.join()
    return data


#@get_func
def store(node, src=INCOMING, tgt=BACKUP):
    rs = node.manager.read_from_redis_str()
    status = rs['status']
    accesses = rs['accesses']
    free = rs['free']
    files = rs['files']
    res = True
    if (NodeStatus.READY == status) and accesses['INCOMING']:
        for filepath in files:
            if src in filepath:
                src = pathize(os.path.abspath(src))
                fp = FilePath.query.filter_by(filepath=filepath).first()
                filestat = files[filepath]
                size = filestat['size']
                encrypt = filestat['encrypt']
                target_copy = filestat['target_copy']
                copy_num = filestat['copy_num']
                if (fp is None) or (fp.fp_encrypt != encrypt):
                    tgt = pathize(os.path.abspath(tgt))
                    if fp is None:
                        fp = FilePath(filepath=filepath, encrypt=filestat['encrypt'], node_ip=node.ip, fp_encrypt=get_encrypt(filepath))
                        db.session.add(fp)
                    else:
                        fp.fp_encrypt = encrypt
                    if (0 == copy_num):
                        fp_size = get_path_size(filepath)
                        tgt_ip = None
                        margin = -1
                        for ip in CLUSTER:
                            node_info = node.manager.read_redis(ip)
                            if node_info is not None:
                                new_margin = node_info.get('free')['BACKUP'] - MIN_FREE_SPACE - fp_size
                                if (0 < new_margin) and (margin < new_margin):
                                    tgt_ip = ip
                                    margin = new_margin
                        if tgt_ip is not None:
                            node.manager.redis.insert_or_update_dict('cp_task', {'from': filepath, 'to': tgt_ip})
                        #rs['files'][filepath]['copy_num'] = copy_num + 1
                    db.session.commit()
                else:
                    res = False
            node.manager.write_to_redis('files', rs['files'])
    return res

if ('__main__' == __name__):
    node = Node()
    while True:
        refresh(node)
        incoming_to_redis(node)
        status = node.manager.read_from_redis_str()
        store(node)
