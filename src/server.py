import sys

from const import NodeStatus
from models import app, db
from models.node import Node
from models.cluster import Cluster

from gcutils.netops import get_local_ip, get_local_hostname

from flask import jsonify
from threading import Thread

@app.route("/status", methods=['GET', 'POST'])
def status():
    return get_local_hostname()
#    local_ip = get_local_ip()
#    node = Node.query.filter_by(ip=local_ip).first()
#    return jsonify(node.to_json())


@app.route("/nodes", methods=['GET', 'POST'])
def nodes():
    nodes = Node.query.all()
    node_dict = {}
    for node in nodes:
        node_dict[node.id] = node.to_json()
    return jsonify(node_dict)


@app.route("/node/<int:node_id>", methods=['GET', 'POST'])
def show_node(node_id):
    node_json = {}
    nodes = cluster.get_node(node_id)
    if (1 == nodes.count()):
        node_json = nodes.first().to_json()
    return jsonify(node_json)


if ('__main__' == __name__):
    local_ip = get_local_ip()

    from gcutils.misc import read_config
    conf = read_config('../config/cicada.conf')
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

    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=http_port)
