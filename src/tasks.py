from config import DNS, DEF_PATHS, COPIES, BLANK
from const import NodeStatus
from utils import get_func, get_path_size, get_encrypt, scan ,deep_scan, pathize
from model import logger, db
from models.filepath import FilePath
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
    data = _threading_incoming_to_redis(node.manager.read_from_redis().get('files', {}))
    return node.manager.write_to_redis('files', data)

def _threading_incoming_to_redis(data):
    threads = []

    def runner(filepath):
        print(filepath)
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
def store_local(node, src=DEF_PATHS['INCOMING'], tgt=DEF_PATHS['BACKUP']):
    rs = node.manager.read_from_redis()
    status = rs['status']
    accesses = rs['accesses']
    free = rs['free']
    files = rs['files']
    res = True
    # todo: to db
    # todo: only update modified part


    if (NodeStatus.READY == status) and accesses['BACKUP']:
        for filepath in files:
            if src in filepath:
                tgt = pathize(tgt)
                filestat = files[filepath]
                size = filestat['size']
                encrypt = filestat['encrypt']
                target_copy = filestat['target_copy']
                copy_num = filestat['copy_num']
                fp = FilePath(filepath=filepath, encrypt=filestat['encrypt'], node_ip=node.ip, fp_encrypt=get_encrypt(filepath))
                db.session.add(fp)
                db.session.commit()
                if (size < free - BLANK) and (0 == copy_num):
                    if os.path.isdir(filepath):
                        tgtfp = shutil.copytree(filepath, tgt + filepath.replace(src, '').split(os.sep)[0])
                    else:
                        tgtfp = shutil.copy2(filepath, tgt)
                    copy_num = 1
                    res = res and (get_encrypt(tgtfp) == encrypt)
                rs['files'][filepath]['copy_num'] = copy_num
            else:
                res = False
            node.manager.write_to_redis('files', rs['files'])
    return res


if ('__main__' == __name__):
    node = Node()
    refresh(node)
    incoming_to_redis(node)
    status = node.manager.read_from_redis()
    print(status)
    print(store_local(node))
