import os
import sys

from const import NodeStatus
from models import app, db
from models.node import Node
from models.node_manager import NodeManager
from models.cluster import Cluster

from gcutils.misc import read_config
from gcutils.netops import get_local_ip, get_local_hostname

from flask import jsonify
from threading import Thread

# conf = read_config('../config/cicada.conf')
# nodes = conf['cluster']['nodes'].split()

@app.route("/", methods=['GET', 'POST'])
def index():
    return conf
#    local_ip = get_local_ip()
#    node = Node.query.filter_by(ip=local_ip).first()
#    return jsonify(node.to_json())


@app.route("/nodes", methods=['GET', 'POST'])
def nodes():
    j = {}
    for node in nodes:
        j[node] = conf[node]['ip']
    return j
#    nodes = Node.query.all()
#    node_dict = {}
#    for node in nodes:
#        node_dict[node.id] = node.to_json()
#    return jsonify(node_dict)

#@app.route("/node/<int:node_id>", methods=['GET', 'POST'])
@app.route("/node/<nodename>", methods=['GET', 'POST'])
def show_node(nodename):
    res = conf[nodename]
    node = Node.query.filter_by(hostname=nodename).first()
    node.manager = NodeManager(conf)
    res['free_space'] = node.free_space()
    return res
#    node_json = {}
#    nodes = cluster.get_node(node_id)
#    if (1 == nodes.count()):
#        node_json = nodes.first().to_json()
#    return jsonify(node_json)


if ('__main__' == __name__):
    local_ip = get_local_ip()

    conf = read_config('../config/cicada.conf')
    for sect in conf:
        if 'root' in conf[sect]:
            conf[sect]['root'] = os.path.realpath(os.path.expanduser(conf[sect]['root']))
    nodes = conf['cluster']['nodes'].split()
    hostname = get_local_hostname()
    i = 0
    while (i < len(nodes)) and (hostname != conf[nodes[i]].get('hostname')):
        i = i + 1
    node = conf[nodes[i]]

    http_port = node.get('http_port', 9999)
    if 1 < len(sys.argv):
        http_port = sys.arv[1]

#    for node in Node.query.all():
#        node.status = NodeStatus.NA
#        db.session.commit()
#    local_ip = get_local_ip()
#    nodes = Node.query.filter_by(ip=local_ip)
#    node = None
#    if (1 == nodes.count()):
#        node = nodes.first()
#    else:
#        node = Node(ip=local_ip, hostname=get_local_hostname() or '')
#        db.session.add(node)
#    node.refresh()
#    db.session.commit()

#    tasks = []
#    t_refresh = Thread(target=node.refresh)
#    tasks.append(t_refresh)

#    for task in tasks:
#        task.start()

    app.run(debug=True, use_reloader=True, host='0.0.0.0', port=http_port)
