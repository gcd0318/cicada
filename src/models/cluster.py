class Cluster():
    def __init__(self, nodes):
        self.nodes = []
        for node in nodes:
            self.nodes.append(node)

    def get_node(self, node_id=None, node_name=None):
        res = None
        i = 0
        if node_name is None:
            while (i < len(self.nodes)) and (self.nodes[i].id != node_id):
                i = i + 1
        elif node_id is None:
            while (i < len(self.nodes)) and (self.nodes[i].name != node_name):
                i = i + 1
        if i < len(self.nodes):
            res = self.nodes[i]
        return res

    def get_nodes(self):
        return self.nodes
