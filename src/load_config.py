import os
import re
import sys

from gcutils.fileops import makedirs
from gcutils.misc import read_config
from gcutils.cli import exec_cmd 

def load(conffile='../config/cicada.conf', nodename=None):
    incoming, backup, storage = None, None, None

    conf = read_config(conffile)
    nodes = conf['cluster']['nodes'].split()
    max_replica = min(int(conf['cluster']['max_replica']), len(nodes))
    free_limit = '100M'

    if nodename is not None:
        node = conf[nodename]

        ip = node['ip']
        incoming_path = os.sep.join([node['root'], node['incoming']])
        backup_path = os.sep.join([node['root'], node['backup']])
        storage_path = os.sep.join([node['root'], node['storage']])
        free_limit = node.get('free_limit', '100M').upper()


    unit_match = 'BKMGT'
    if free_limit:
        free_limit = '0' + free_limit
        free_limit_unit = re.findall('\D$', free_limit)[0]
        free_limit = int(''.join(re.findall('\d*', free_limit)))
        for i in range(unit_match.index(free_limit_unit)):
            free_limit = free_limit * 1024


    return nodes, ip, incoming_path, backup_path, storage_path, max_replica, free_limit
