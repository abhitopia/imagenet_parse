import xml.etree.ElementTree as etree

class ImageNetParser:
    def __init__(self, xml_path='structure_released.xml'):
        self.nodes = {}
        xml_root = etree.parse(xml_path).getroot()
        self.populate_graph(xml_root)
        print "Analysing graph..."
        if not self.is_tree():
            print "Graph is not a Tree, nodes have multiple parents!!"

        # if not self.is_acyclic():
        #     print "Graph has circular dependencies"
        print "No circular dependencies found. Assuming DAG such that traversal is possible only from parent to child node"

    def __parse(self, node, node_id, parent_id):
        """DFS algorithm to populate the nodes"""
        # add node to self.nodes
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                'id': node_id,
                'parent_ids': [] if parent_id is None else [parent_id],
                'child_ids': []
            }
        else:
            # looks like there are multiple parents
            self.nodes[node_id]['parent_ids'].append(parent_id)
        # recurse over children
        for child in node:
            if child.tag == 'synset':
                child_id = child.attrib['wnid']
                self.nodes[node_id]['child_ids'].append(child_id)
                self.__parse(child, child_id, node_id)

    def __traverse_along_path(self, node_id, follow='parent_ids', stop_at=None, dist=None, result=None):
        """
        returns a dictionary of all the ancestors(follow='parent_ids') or descendants(follow='child_ids)
        of the nodes in DAG along with its "shortest distance".
        """
        # initialisation of default argument because of Python's stupid single time initialisation of arguments
        if dist is None:
            dist = 0
        if result is None:
            result = {}

        self.check_if_valid_id(node_id)

        followed_nodes = self.nodes[node_id][follow]
        for fnode_id in followed_nodes:
            # the "min" essentially incorporates the shortest distance behavior in DAG
            result[fnode_id] = dist + 1 if fnode_id not in result else min(result[fnode_id], dist + 1)
            if node_id == stop_at:
                break
            else:
                self.__traverse_along_path(fnode_id, follow, stop_at, dist+1, result)

        return result

    def check_if_valid_id(self, node_id):
        if node_id not in self.nodes:
            raise KeyError("Invalid node_id: " + node_id)

    def populate_graph(self, xml_root):
        """
        Populates the internal data structure (self.nodes)
        :param xml_root: root node of the xml document
        """
        print 'Reading XML structure and populating the graph..'
        self.__parse(xml_root, 'root', None)

    def is_acyclic(self):
        """Check if the graph is cyclic"""
        for node_id in self.nodes:
            anc = self.get_ancestors(node_id)
            dec = self.get_descendants(node_id)
            # if the node is present in its ancestors or descendants, that indicates cyclic structure
            if len(list(set(anc) & set([node_id]))) > 0 or len(list(set(dec) & set([node_id]))) > 0:
                return False
        return True

    def is_tree(self):
        """Check if the graph is tree, that is each node has only one parent"""
        for node_id in self.nodes:
            if len(self.nodes[node_id]['parent_ids']) > 1:
                return False
        return True

    def get_ancestors(self, node_id):
        """returns list of wnids of all ancestor"""
        return self.__traverse_along_path(node_id, follow='parent_ids').keys()

    def get_descendants(self, node_id):
        """returns list of wnids of all descendants"""
        return self.__traverse_along_path(node_id, follow='child_ids').keys()

    def get_depth(self, node_id):
        """returns the depth from root of DAG
        Note: In case of multiple occurrence, minimum depth is returned
        """
        depths = self.__traverse_along_path(node_id, follow='parent_ids', stop_at='root')
        return depths['root'] if 'root' in depths else 0

    def get_distance(self, node_id1, node_id2):
        """
        This function calculated the "shortest" distance between the nodes in DAG.
        Distance is defined as number of edges, it takes to traverse from one node to another.
        Note:I have not implemented Djikstra algorithm (which under the hood does something similar)
        on purpose here to reuse existing code
        """

        # self.__traverse_along_path will take care of node_id1
        self.check_if_valid_id(node_id2)

        # Direct link means either node2 is in the ancestors of node1 or in the descendants of node1
        for follow_path in ['parent_ids', 'child_ids']:
            path = self.__traverse_along_path(node_id1, follow=follow_path, stop_at=node_id2)
            if node_id2 in path:
                return path[node_id2]

        # else return -1
        return -1



# Unit Tests
if __name__ == '__main__':
    parser = ImageNetParser()
    # get_depths
    assert(parser.get_depth('root') == 0)   # root node
    assert(parser.get_depth('n00017222') == 2)

    # ancestors
    assert(parser.get_ancestors('root') == [])  # root node
    assert(len(set(parser.get_ancestors('n00017222')) & set(['n00004475', 'root', 'fa11misc', 'fall11'])) == 4)

    # descendants
    assert(len(set(parser.get_descendants('n10151570')) & set(['n10718040', 'n09923003'])) == 2)
    assert(len(parser.get_descendants('n10081456')) == 0)   # child node

    # distance between nodes
    # note that n00017222 appears twice in graph, however, shortest distance is returned
    assert(parser.get_distance('root', 'n00017222') == 2)
    assert(parser.get_distance('n09201998', 'n09283066') == -1)  # both are child nodes
