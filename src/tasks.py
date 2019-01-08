from config import DNS, DEF_PATHS, COPIES
from utils import get_func, get_path_size, get_md5, scan ,deep_scan
from model import logger
from models.node_manager import NodeManager
from models.node import Node

import os

@get_func
def refresh(node):
    node.refresh()

@get_func
def incoming_to_redis(node):
    data = {}
    for filepath in scan():
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
        data[filepath] = filedata
    return node.manager.write_to_redis('files', data)

def _incoming_from_redis(node):
    return node.manager.read_from_redis()

@get_func
def copy_local():
    pass


if ('__main__' == __name__):
    node = Node()
    refresh(node)
    incoming_to_redis(node)
    status = incoming_from_redis(node)['files']
    print(type(status))
    for filepath in status:
        print(filepath, status[filepath])
