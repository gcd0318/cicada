class Cluster():
    def __init__(self, nodes):
        self.nodes = []
        for node in nodes:
            self.nodes.append(node)

    def get_node(self, node_id):
        res = None
        i = 0
        while (i < len(self.nodes)) and (self.nodes[i].id != node_id):
            i = i + 1
        if i < len(self.nodes):
            res = self.nodes[i]
        return res
