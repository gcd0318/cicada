from model import *
from models.node import *

n = Node()
print(n.init())
print(n.scan('../src/'))
print(n.scan('config.py'))
