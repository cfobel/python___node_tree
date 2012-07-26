# -*- coding: utf-8 -*-

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
from contextlib import closing
import copy
from pprint import pprint
import cPickle as pickle

from jinja2 import Template
from path import path


class NodeTree(object):
    def __init__(self, children=None):
        self._ungroup_in_progress = False
        self._group_in_progress = False
        self.root = Node(None)
        self._reset_index()
        if children is not None:
            try:
                iter(children)
                if isinstance(children, Node):
                    children = [children]
            except TypeError:
                children = [children]
            for c in children:
                self.append_node(c)

    def ungroup(self, nodes):
        if not nodes:
            return
        print nodes
        self._ungroup_in_progress = True
        try:
            root_paths = [self._node_to_path_map[n] for n in nodes]
            print 'root_paths:', root_paths
            for root in nodes:
                print len(root)
                removed = [self.remove(c)[0] for c in root[::-1]]
                #removed = [self.remove(c)[0] for c in root.children]
                print len(removed)
                print [r.item for r in removed]
                for node in removed:
                    self.insert_after(root, node)
            self._on_ungrouped(root_paths)
        finally:
            self._ungroup_in_progress = False

    def group(self, nodes):
        if not nodes:
            return
        self._group_in_progress = True
        try:
            node_paths, nodes = zip(*sorted([(self._node_to_path_map[
                    node], node) for node in nodes]))
            root = nodes[0]
            removed = [self.remove(node)[0] for node in nodes[1:]]
            for node in removed:
                self.append_child(root, node)
            self._on_grouped(node_paths[0], node_paths[1:])
        finally:
            self._group_in_progress = False

    @property
    def max_depth(self):
        return self._max_depth

    def _reset_index(self):
        self._max_depth = 0
        self._node_to_id_map = {}
        self._id_to_path_map = []
        self._node_to_path_map = {}

    def on_ungrouped(self, root_paths):
        pass

    def on_grouped(self, parent_path, children_paths):
        pass

    def on_node_inserted(self, *args, **kwargs):
        pass

    def on_node_appended(self, *args, **kwargs):
        pass

    def on_node_removed(self, *args, **kwargs):
        pass

    def _on_ungrouped(self, root_paths):
        self._reindex()
        self.on_ungrouped(root_paths)

    def _on_grouped(self, parent_path, children_paths):
        self._reindex()
        self.on_grouped(parent_path, children_paths)

    def _on_node_inserted(self, *args, **kwargs):
        self._reindex()
        if not self._ungroup_in_progress and not self._group_in_progress:
            self.on_node_inserted(*args, **kwargs)

    def _on_node_appended(self, *args, **kwargs):
        self._reindex()
        if not self._ungroup_in_progress and not self._group_in_progress:
            self.on_node_appended(*args, **kwargs)

    def _on_node_removed(self, *args, **kwargs):
        self._reindex()
        if not self._ungroup_in_progress and not self._group_in_progress:
            self.on_node_removed(*args, **kwargs)

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
        self._max_depth = max(self._max_depth, self._depth)
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
        for i in range(len(self)):
            yield self._id_to_path_map[i], self[i]

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

    def append_child(self, parent, node):
        parent.append_node(node)
        self._on_node_appended(node)

    def _insert_relative(self, insert_func, sibling, node):
        position = insert_func(sibling, node)
        sibling_path = self._node_to_path_map[sibling]
        print '[_insert_relative] sibling_path=%s position=%s' % (sibling_path, position)
        self._on_node_inserted(sibling_path[:-1] + (position, ), node)

    def insert_before(self, sibling, node):
        self._insert_relative(Node.insert_before, sibling, node)

    def insert_after(self, sibling, node):
        self._insert_relative(Node.insert_after, sibling, node)

    def insert(self, node_path, node):
        try:
            sibling = self[node_path]
            self.insert_before(sibling, node)
        except IndexError:
            try:
                parent_path = node_path[:-1]
            except TypeError:
                parent_path = None
            if parent_path:
                parent = self[parent_path]
            else:
                parent = self.root
            try:
                sibling_path = node_path[:-1] + (node_path[-1] - 1, )
                sibling = self[sibling_path]
                self.insert_after(sibling, node)
            except IndexError:
                self.append_child(parent, node)

    def remove(self, node):
        node_path = self._node_to_path_map[node]
        node.parent.remove_node(node)
        node_tree = node.get_tree()
        self._on_node_removed(node_path, node_tree)
        return node_tree

    def copy(self):
        return copy.deepcopy(self)


class Node(object):
    tree_class = NodeTree

    def __init__(self, item=None):
        self.parent = None
        self.item = item
        self.children = []

    def insert_before(self, node):
        node.parent = self.parent
        position = node.parent.index(self)
        node.parent.children.insert(position, node)
        return position

    def insert_after(self, node):
        node.parent = self.parent
        position = node.parent.index(self)
        node.parent.children.insert(position + 1, node)
        return position + 1

    def append_node(self, child):
        child.parent = self
        self.children.append(child)

    def remove_node(self, node):
        self.children.remove(node)
        node.parent = None

    def index(self, value):
        return self.children.index(value)

    def __len__(self):
        return len(self.children)

    def __getitem__(self, index):
        return self.children[index]

    def __iter__(self):
        for child in self.children:
            yield child

    def get_tree(self):
        return self.tree_class(self.copy())

    def _copy_single(self):
        return self.__class__(item=self.item)

    def copy(self):
        new_node = self._copy_single()
        new_node.children = [child.copy() for child in self.children]
        for child in new_node:
            child.parent = new_node
        return new_node


_node_tree_dot_template_str = '''\
digraph G {
    rankdir="LR";
{{ edges }}
}
'''


def node_tree_to_dot(node_tree):
    template = Template(_node_tree_dot_template_str)
    with closing(StringIO.StringIO()) as sio:
        for node_path, node in node_tree:
                print >> sio, '%s [ label=<<table border="0"><tr><td><b>[%s]</b>:</td><td><i>%s</i></td></tr></table>> ];' % (
                        node_tree._node_to_id_map[node],
                                node_tree._node_to_id_map[node], node.item)
                print >> sio, '    ' * (len(node_path) - 1),
                try:
                    if node.parent is not node_tree.root:
                        print >> sio, '%s->%s;' % (node_tree._node_to_id_map[
                                node.parent], node_tree._node_to_id_map[node])
                except KeyError:
                    print node.item, node.parent.item
        return template.render(edges=sio.getvalue())


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
    path('00_original.dot').write_bytes(node_tree_to_dot(node_tree))

    sub_tree = node_tree[1].get_tree()
    node_tree.insert_after(node_tree[0], copy.deepcopy(sub_tree)[0])
    path('01_insert_1_after_0.dot').write_bytes(node_tree_to_dot(node_tree))

    sub_tree = node_tree[15].get_tree()
    node_tree.insert_after(node_tree[14], sub_tree[0])
    path('02_insert_15_after_14.dot').write_bytes(node_tree_to_dot(node_tree))

    node_tree.remove(node_tree[12])
    path('03_remove_12.dot').write_bytes(node_tree_to_dot(node_tree))

    sibling = node_tree[9]
    sub_tree = node_tree.remove(node_tree[5])
    node_tree.insert_after(sibling, sub_tree[0])
    path('04_remove_5_insert_after_9.dot').write_bytes(node_tree_to_dot(node_tree))

    other_tree = NodeTree([node.copy() for node in [node_tree[1], node_tree[5]]])
    node_tree.insert_before(node_tree[0], other_tree[0])
    path('05_copy_1_5_insert_before_0.dot').write_bytes(node_tree_to_dot(node_tree))

    node_tree.group([node_tree[i] for i in [0, 4, 5]])
    path('06_group_0_4_5.dot').write_bytes(node_tree_to_dot(node_tree))

    node_tree.ungroup([node_tree[i] for i in [0]])
    path('07_ungroup_0.dot').write_bytes(node_tree_to_dot(node_tree))

    node_tree.group([node_tree[i] for i in [0, 1, 2, 4, 5]])
    path('08_group_0_1_2_4_5.dot').write_bytes(node_tree_to_dot(node_tree))

    node_tree.ungroup([node_tree[i] for i in [0, 16]])
    path('09_ungroup_0_16.dot').write_bytes(node_tree_to_dot(node_tree))
