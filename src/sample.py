from model import *
from models.node import *

#db.drop_all()
#db.create_all()

n = Node()
print('access:', n.refresh())
print('json:', n.to_json())
print(n.manager.scan('../src/'))
print(n.manager.scan('config.py'))
print(n.manager.refresh_incoming())
print(n.manager.call_peers())

#db.session.add(n)
#db.session.commit()
