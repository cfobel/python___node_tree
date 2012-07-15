# -*- coding: utf-8 -*-

import gobject
from pygtkhelpers.utils import gsignal


class Node(gobject.GObject):
    gsignal('created')
    gsignal('child-appended', object)
    gsignal('child-removed', object)

    def __init__(self, item=None):
        super(Node, self).__init__()
        self.parent = None
        self.item = item
        self.children = []

    def on_grandchild_appended(self, parent, child):
        self.emit('child-appended', child)

    def append_child(self, child):
        child.parent = self
        child.connect('child-appended', self.on_grandchild_appended)
        child.connect('child-removed', self.on_grandchild_removed)
        self.children.append(child)
        self.emit('child-appended', child)

    def on_grandchild_removed(self, parent, child):
        self.emit('child-removed', child)

    def remove_child(self, child):
        self.children.remove(child)
        self.emit('child-removed', child)


class NodeTree(object):
    def __init__(self):
        self.root = Node(None)
        self.root.connect('child-appended', self.on_child_appended)
        self.root.connect('child-removed', self.on_child_removed)
        self._reset_index()

    def _reset_index(self):
        self._node_to_id_map = {}
        self._id_to_path_map = []
        self._node_to_path_map = {}

    def on_child_appended(self, *args, **kwargs):
        self._reindex()

    def on_child_removed(self, *args, **kwargs):
        print '[on_child_removed] args=%s kwargs=%s' % (args, kwargs)
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
        for child in node.children:
            for child_node in self._iter_children(child):
                yield child_node
            self._counts[self._depth] += 1
        self._depth -= 1
        del self._counts[self._depth + 1:]

    def _get_node(self, parent, node_path):
        if len(node_path) > 1:
            return self._get_node(parent.children[node_path[0]],
                    node_path[1:])
        else:
            return parent.children[node_path[0]]

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

    def append_child(self, parent, child):
        parent.append_child(child)

    def remove(self, node):
        node.parent.remove_child(node)
        node_tree = NodeTree()
        node_tree.append_child(node_tree.root, node)
        return node_tree


if __name__ == '__main__':
    node_tree = NodeTree()

    node = Node(0)
    node_tree.append_child(node_tree.root, node)
    child = Node(1)
    node.append_child(child)
    child = Node(2)
    node.append_child(child)
    grandchild = Node(3)
    child.append_child(grandchild)

    print [i for i in node_tree._iter_children()]
