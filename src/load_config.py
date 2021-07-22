import os
import sys

from gcutils.fileops import makedirs
from gcutils.misc import read_config
from gcutils.cli import exec_cmd 

def load(conffile='../config/cicada.conf', nodename=None):
    incoming, backup, storage = None, None, None

    conf = read_config(conffile)
    nodes = conf['cluster']['nodes'].split()
    max_replica = min(int(conf['cluster']['max_replica']), len(nodes))

    if nodename is not None:
        node = conf[nodename]

        incoming = os.sep.join([node['root'], node['incoming']])
        backup = os.sep.join([node['root'], node['backup']])
        storage = os.sep.join([node['root'], node['storage']])

    return nodes, incoming, backup, storage, max_replica
