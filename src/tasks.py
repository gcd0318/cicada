from config import DNS, DEF_PATHS, COPIES
from utils import get_func, get_path_size, get_md5, scan ,deep_scan
from model import logger
from models.node_manager import NodeManager
from models.node import Node

import os

#@get_func
def refresh(node):
    node.refresh()

#@get_func
def get_incoming(node):
    res = True
    for filepath in scan():
        data = {
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
        data['target_copy'] = target_copy
        print (filepath, data)
        res = res and node.manager.write_to_redis(filepath, data)
    return res


if ('__main__' == __name__):
    node = Node()
    refresh(node)
    print(get_incoming(node))