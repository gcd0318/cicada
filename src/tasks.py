from config import DNS, DEF_PATHS
from utils import get_func
from models.node_manager import NodeManager
from models.node import Node

import glob
import os

def deep_scan(root=DEF_PATHS['INCOMING']):
    resl = []
    root = os.path.abspath(root)
    if os.path.isdir(root):
        if not(root.endswith(os.sep)):
            root = root + os.sep
        for dirpath, dirnames, filenames in os.walk(root):
            for filepath in filenames:
                resl.append(os.path.join(dirpath, filepath))
    else:
        resl.append(root)
    return resl

def scan(root=DEF_PATHS['INCOMING']):
    resl = []
    root = os.path.abspath(root)
    if os.path.isdir(root):
        if not(root.endswith(os.sep)):
            root = root + os.sep
        for filepath in glob.glob(root + '*'):
            if os.path.isdir(filepath):
                if not (filepath.endswith(os.sep)):
                    filepath = filepath + os.sep
            resl.append(filepath)
    else:
        resl.append(root)
    return resl

@get_func
def refresh():
    node = Node()
    node.refresh()

if ('__main__' == __name__):
    print(scan())
    print(deep_scan())