import os
import sys

from gcutils.fileops import makedirs
from gcutils.misc import read_config
from gcutils.cli import exec_cmd 

def check_path(path):
    print(path, os.path.exists(os.path.realpath(os.path.expanduser(path))))

conf = read_config('../config/cicada.conf')
nodename = sys.argv[1]

node = conf[nodename]

nodes = conf['cluster']['nodes'].split()
max_replica = min(int(conf['cluster']['max_replica']), len(nodes))

incoming = os.sep.join([node['root'], node['incoming']])
backup = os.sep.join([node['root'], node['backup']])
storage = os.sep.join([node['root'], node['storage']])

makedirs(incoming)
for i in range(max_replica):
    replica_path = os.sep.join([incoming, str(i + 1)])
    makedirs(replica_path)
    check_path(replica_path)

makedirs(storage)
check_path(storage)

for s in nodes:
    if (s != nodename):
        bpath = os.sep.join([backup, s])
        makedirs(bpath)
        check_path(bpath)

for i in range(len(nodes)):
    nodei = nodes[i]
    for j in range(i + 1, len(nodes)):
        nodej = nodes[j]
        storage_ij = os.sep.join([storage, nodei + '_' +  nodej])
        makedirs(storage_ij)
        check_path(storage_ij)
        backup_ji = os.sep.join([backup, nodej + '_' +  nodei])
        makedirs(backup_ji)
        check_path(backup_ji)
