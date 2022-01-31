from models.node import Node

#@get_func
def refresh(node):
    node.refresh()

if ('__main__' == __name__):
    node = Node()
    while True:
        refresh(node)
