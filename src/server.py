from config import PORT
from model import app, db, logger
from models.node import Node
from utils import get_local_ip

from flask import render_template, redirect, url_for, request, jsonify

@app.route("/", methods=['GET', 'POST'])
def home():
    nodes = Node.query.all
    nodelist = []
    for node in nodes:
        nodelist.append(node.to_json())
    return jsonify({'nodes': nodelist})


if ('__main__' ==  __name__):
    local_ip = get_local_ip()
    nodes = Node.query.filter_by(ip=local_ip)
    node = None
    if (1 == nodes.count()):
        node = nodes.first()
    else:
        node = Node(ip=local_ip, hostname=get_local_hostname() or '')
        db.commit()
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=PORT)
