from config import DNS, DEF_PATHS
from utils import get_func, get_path_size, get_md5
from models.node_manager import NodeManager
from models.node import Node


@get_func
def refresh():
    node = Node()
    node.refresh()



if ('__main__' == __name__):
    print(scan())
    print(deep_scan())