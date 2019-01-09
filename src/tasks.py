from config import DNS, DEF_PATHS, COPIES, BLANK
from const import NodeStatus
from utils import get_func, get_path_size, get_md5, scan ,deep_scan, pathize
from model import logger
from models.node_manager import NodeManager
from models.node import Node
import threading

import os
import shutil
import time

#@get_func
def refresh(node):
    node.refresh()

#@get_func
def incoming_to_redis(node):
    data = node.manager.read_from_redis().get('files', {})
    for filepath in scan():
        old_md5 = ''
        new_md5 = get_md5(filepath)
        while(old_md5 != new_md5):
            time.sleep(1)
            old_md5 = new_md5
            new_md5 = get_md5(filepath)
        if not(filepath in data):
            filedata = {
                'md5': get_md5(filepath),
                'size': get_path_size(filepath),
            }
            target_copy = COPIES
            try:
                target_copy = int(filepath.split(os.sep)[-2])
            except Exception as err:
                logger.warning(err)
            finally:
                pass
            filedata['target_copy'] = target_copy
            filedata['copy_num'] = 0
            data[filepath] = filedata
    return node.manager.write_to_redis('files', data)



#@get_func
def copy_local(node, src=DEF_PATHS['INCOMING'], tgt=DEF_PATHS['BACKUP']):
    rs = node.manager.read_from_redis()
    status = rs['status']
    accesses = rs['accesses']
    free = rs['free']
    files = rs['files']
    res = True
    if (NodeStatus.READY == status) and accesses['BACKUP']:
        for filepath in files:
            if src in filepath:
                print(filepath)
                tgt = pathize(tgt)
                filestat = files[filepath]
                size = filestat['size']
                md5 = filestat['md5']
                target_copy = filestat['target_copy']
                copy_num = filestat['copy_num']
                if (size < free - BLANK) and (0 == copy_num):
                    if os.path.isdir(filepath):
                        tgtfp = shutil.copytree(filepath, tgt + filepath.replace(src, '').split(os.sep)[0])
                    else:
                        tgtfp = shutil.copy2(filepath, tgt)
                    copy_num = 1
                    res = res and (get_md5(tgtfp) == md5)
            else:
                res = False
            rs['files'][filepath]['copy_num'] = copy_num
            print(node.manager.write_to_redis('files', rs['files']))
    return res


if ('__main__' == __name__):
    node = Node()
    refresh(node)
    incoming_to_redis(node)
    status = node.manager.read_from_redis()
    print(status)
    print(copy_local(node))
