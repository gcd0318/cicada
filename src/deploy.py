import os
import sys

from gcutils.misc import read_config
from gcutils.cli import exec_cmd 

conf = read_config('config/cicada.conf')
nodename = sys.argv[1]

for sect in conf['cluster']['nodes'].split():
    print(sect, conf[sect])

node = conf[nodename]
incoming = os.sep.join([node['root'], node['incoming']])
backup = os.sep.join([node['root'], node['backup']])
storage = os.sep.join([node['root'], node['storage']])
for p in (backup, storage):
    for s in conf['cluster']['nodes'].split():
        tgt_path = os.sep.join([p, s])
        if ((s != nodename) and (not os.path.exists(tgt_path))):
            os.makedirs(tgt_path)
        else:
            print(tgt_path, 'exists')


