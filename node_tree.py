# -*- coding: utf-8 -*-

from pprint import pprint
import cPickle as pickle


class Node(object):
    def __init__(self, item=None):
        self.parent = None
        self.item = item
        self.children = []

    def insert_after(self, node):
        node.parent = self.parent
        position = node.parent.index(self)
        node.parent.children.insert(position + 1, node)

    def append_node(self, child):
        child.parent = self
        self.children.append(child)

    def remove_node(self, node):
        self.children.remove(node)

    def index(self, value):
        return self.children.index(value)

    def __len__(self):
        return len(self.children)

    def __getitem__(self, index):
        return self.children[index]

    def __iter__(self):
        for child in self.children:
            yield child


class NodeTree(object):
    def __init__(self):
        self.root = Node(None)
        #self.root.connect('node-appended', self.on_node_appended)
        #self.root.connect('node-inserted', self.on_node_appended)
        #self.root.connect('node-removed', self.on_node_removed)
        self._reset_index()

    def _reset_index(self):
        self._node_to_id_map = {}
        self._id_to_path_map = []
        self._node_to_path_map = {}

    def on_node_inserted(self, *args, **kwargs):
        self._reindex()

    def on_node_appended(self, *args, **kwargs):
        self._reindex()

    def on_node_removed(self, *args, **kwargs):
        self._reindex()

    def _reindex(self):
        self._reset_index()
        for index, node_path, node in [i for i in self._iter_children()]:
            self._node_to_path_map[node] = node_path
            self._id_to_path_map.append(node_path)
            self._node_to_id_map[node] = index

    def _iter_children(self, node=None):
        if node is None:
            node = self.root
            self._counts = [0]
            self._depth = -1
            self._index = 0
        if node != self.root:
            yield self._index, tuple(self._counts[:self._depth + 1]), node
            self._index += 1
        self._depth += 1
        while len(self._counts) < self._depth + 1:
            self._counts.append(0)
        for child in node:
            for child_node in self._iter_children(child):
                yield child_node
            self._counts[self._depth] += 1
        self._depth -= 1
        del self._counts[self._depth + 1:]

    def _get_node(self, parent, node_path):
        if len(node_path) > 1:
            return self._get_node(parent[node_path[0]],
                    node_path[1:])
        else:
            return parent[node_path[0]]

    def __iter__(self):
        for index, node_path, node in self._iter_children():
            yield node_path, node

    def __getitem__(self, key):
        try:
            len(key)
            # The key has a length
            return self._get_node(self.root, key)
        except TypeError:
            return self._get_node(self.root, self._id_to_path_map[key])

    def __len__(self):
        return len(self._id_to_path_map)

    def append_node(self, node):
        if self.root.children:
            sibling_path = (self._node_to_path_map[self[-1]][0], )
            self.insert_after(self[sibling_path], node)
        else:
            self.append_child(self.root, node)
        self.on_node_appended(node)

    def append_child(self, parent, node):
        parent.append_node(node)

    def insert_after(self, sibling, node):
        sibling.insert_after(node)
        sibling_path = self._node_to_path_map[sibling]
        insert_path = sibling_path[:-1] + tuple([sibling_path[-1] + 1])
        self.on_node_inserted(insert_path, node)

    def remove(self, node):
        node_path = self._node_to_path_map[node]
        node.parent.remove_node(node)
        node_tree = NodeTree()
        node_tree.append_child(node_tree.root, node)
        node_tree._reindex()
        self.on_node_removed(node_path, node_tree)
        return node_tree


if __name__ == '__main__':
    node_tree = NodeTree()

    count = 0
    for i in range(2):
        node_tree.append_node(Node(count))
        count += 1
    parent = node_tree[-1]
    for i in range(2):
        node_tree.append_child(parent, Node(count))
        count += 1
    parent = node_tree[-1]
    node_tree.append_child(parent, Node(count))
    count += 1
    for i in range(3):
        node_tree.append_node(Node(count))
        count += 1
    parent = node_tree[-1]
    for i in range(2):
        child = Node(count)
        node_tree.append_child(parent, child)
        count += 1
        for i in range(2):
            node_tree.append_child(child, Node(count))
            count += 1
    node_tree.append_node(Node(count))
    count += 1
    pprint([i for i in node_tree._iter_children()])

    print pickle.dumps(node_tree)
