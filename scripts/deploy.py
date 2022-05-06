import os
import sys

from gcutils.fileops import makedirs
from gcutils.netops import get_local_hostname
from gcutils.cli import exec_cmd 

from load_config import load
from models import db
from models.node import Node


def check_path(path):
    print(path, os.path.exists(os.path.realpath(os.path.expanduser(path))))


nodename = get_local_hostname()
conf = load('../config/cicada.conf', nodename)
nodes = conf['nodes']
cmdip = conf['cmdip']
dataip = conf['dataip']
incoming_path = conf['incoming_path']
backup_path = conf['backup_path']
storage_path = conf['storage_path']
max_replica = conf['max_replica']
free_limit = conf['free_limit']

makedirs(incoming_path)
for i in range(max_replica):
    replica_path = os.sep.join([incoming_path, str(i + 1)])
    makedirs(replica_path)
    check_path(replica_path)

makedirs(storage_path)
check_path(storage_path)

for s in nodes:
    if (s != nodename):
        bpath = os.sep.join([backup_path, s])
        makedirs(bpath)
        check_path(bpath)

for i in range(len(nodes)):
    nodei = nodes[i]
    for j in range(i + 1, len(nodes)):
        nodej = nodes[j]
        storage_ij = os.sep.join([storage_path, nodei + '_' +  nodej])
        makedirs(storage_ij)
        check_path(storage_ij)
        backup_ji = os.sep.join([backup_path, nodej + '_' +  nodei])
        makedirs(backup_ji)
        check_path(backup_ji)





# db.drop_all()
# db.create_all()
# db.session.add(Node(hostname=nodename, free_limit=free_limit, ip=ip))

# db.session.commit()
