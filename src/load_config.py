import os
import sys

from gcutils.fileops import makedirs
from gcutils.misc import read_config
from gcutils.cli import exec_cmd 

def load(conffile='../config/cicada.conf'):
    conf = read_config(conffile)
    nodename = sys.argv[1]

    node = conf[nodename]

    nodes = conf['cluster']['nodes'].split()
    max_replica = min(int(conf['cluster']['max_replica']), len(nodes))

    incoming = os.sep.join([node['root'], node['incoming']])
    backup = os.sep.join([node['root'], node['backup']])
    storage = os.sep.join([node['root'], node['storage']])

    return incoming, backup, storage, max_replica
