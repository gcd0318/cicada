from model import *
from models.node import *

db.drop_all()
db.create_all()

n = Node()
print('access:', n.init())
print('json:', n.to_json())
print(n.scan('../src/'))
print(n.scan('config.py'))

db.session.add(n)
db.session.commit()
