import os
import sys

from gcutils.misc import read_config
from gcutils.cli import exec_cmd 

conf = read_config('../config/cicada.conf')
nodename = sys.argv[1]

node = conf[nodename]
incoming = os.path.realpath(os.path.expanduser(os.sep.join([node['root'], node['incoming']])))
backup = os.path.realpath(os.path.expanduser(os.sep.join([node['root'], node['backup']])))
storage = os.path.realpath(os.path.expanduser(os.sep.join([node['root'], node['storage']])))

nodes = conf['cluster']['nodes'].split()
max_replica = min(int(conf['cluster']['max_replica']), len(nodes))

if not os.path.exists(incoming):
    os.makedirs(incoming)
for i in range(max_replica):
    os.makedirs(os.sep.join([incoming, str(i + 1)]))

for p in (backup, storage):
    for s in nodes:
        tgt_path = os.sep.join([p, s])
        if ((s != nodename) and (not os.path.exists(tgt_path))):
            os.makedirs(tgt_path)

        print(tgt_path, 'exists', os.path.exists(tgt_path))


