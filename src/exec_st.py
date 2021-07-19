from gcutils.misc import read_config

import syncthing

CONFFILE = '../config/cicada.conf'

cicada = read_config(CONFFILE, allow_empty=False)
sts = []

cluster = cicada.get('cluster', {})

for nodename in cicada:
    if nodename.startswith('node'):
        node = cicada[nodename]
        sts.append(syncthing.Syncthing(api_key=node['id'], host=node['ip']))

max_replica = min(int(cluster.get('max_replica', len(sts))), len(sts))

print(sts)
print(max_replica)
for st in sts:
    print(st)
    print(st.system.status())
