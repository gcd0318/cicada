import os
import re
import sys

from gcutils.fileops import makedirs
from gcutils.misc import read_config
from gcutils.cli import exec_cmd 

def load(conffile='../config/cicada.conf', nodename=None):
    res = {}

    conf = read_config(conffile)
    nodes = conf['cluster']['nodes'].split()
    max_replica = min(int(conf['cluster']['max_replica']), len(nodes))

    if nodename is None:
        res['nodes'] = nodes
        for nname in nodes:
            node = conf[nname]
            tmp = {}
            for key in conf[nname]:
                if ('_path' in key):
                    tmp[key] = os.sep.join([node['root'], node[key]])
                elif ('free_limit' == key):
                    free_limit = node.get('free_limit', '100M').upper()
                    unit_match = 'BKMGT'
                    free_limit = '0' + free_limit
                    free_limit_unit = re.findall('\D$', free_limit)[0]
                    free_limit = int(''.join(re.findall('\d*', free_limit)))
                    for i in range(unit_match.index(free_limit_unit)):
                        free_limit = free_limit * 1024
                    tmp[key] = free_limit
                else:
                    tmp[key] = node[key]
            res[nname] = tmp
    else:
        node = conf[nodename]

        ip = node['ip']
        incoming_path = os.sep.join([node['root'], node['incoming_path']])
        backup_path = os.sep.join([node['root'], node['backup_path']])
        storage_path = os.sep.join([node['root'], node['storage_path']])

        free_limit = node.get('free_limit', '100M').upper()
        unit_match = 'BKMGT'
        free_limit = '0' + free_limit
        free_limit_unit = re.findall('\D$', free_limit)[0]
        free_limit = int(''.join(re.findall('\d*', free_limit)))
        for i in range(unit_match.index(free_limit_unit)):
            free_limit = free_limit * 1024

        res = {
                'nodes': nodes,
                'ip': ip,
                'incoming_path': incoming_path,
                'backup_path': backup_path,
                'storage_path': storage_path,
                'max_replica': max_replica,
                'free_limit': free_limit,
                }


    return res

if ('__main__' == __name__):
    print(load())
    from gcutils.netops import get_local_hostname
    print(load(nodename=get_local_hostname()))
