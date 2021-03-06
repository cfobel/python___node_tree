# -*- coding: utf-8 -*-

from pprint import pprint
from contextlib import closing
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import logging
import copy

from jinja2 import Template
from path import path


class NodeTree(object):
    r'''
    An instance of this class represents a flat top-level tree structure.
    e.g.,

        A      B      C     D       Top level can have more than one `Node`
       / \    / \    / \     \
      E   F  G   H  I   J     K
     /          / \
    L          M   N

    Nodes can be inserted into the tree using the following methods:
        append_node(node/node_tree)
            Insert the provided `Node` at the end of the list of top level
            `Node` instances.  Note that this method also accepts a `NodeTree`
            instance that has single top-level `Node`.  This is convenient when
            using other methods that return a `NodeTree`, such as
            `NodeTree.remove()`.

        append_child(parent, node)
            Append the provided `Node` to the end of the list of children for
            `parent`.

        insert_before(sibling, node)
            Insert the provided `Node` as a sibling before `sibling`.

        insert_after(sibling, node)
            Insert the provided `Node` as a sibling after `sibling`.

        insert(node_path, node)
            Insert the provided `Node` before the provided `node_path` tuple.
            If there is currently no node at the path `node_path`, the `Node`
            will be inserted at the last position at the deepest level of the
            `node_path`.


    Nodes can be grouped and ungrouped using the methods with corresponding names.
    '''
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

    def __str__(self):
        with closing(StringIO.StringIO()) as s:
            for i, (path, node) in enumerate(self):
                print >> s, '[%2d]' % i, path, node
            msg = s.getvalue()
        return msg

    def single_root_as_node(self):
        '''
        If this `NodeTree` has exactly one top-level `Node`, return a copy of
        that `Node`.  Otherwise, raise a `ValueError`.
        '''
        if len(self.root.children) != 1:
            raise ValueError, 'NodeTree instances must have exactly one '\
                    'top-level child to be casted to a Node'
        return self.root.children[0].copy()

    def ungroup(self, nodes):
        '''
        Ungroup the specified list of `Node` instances.  This means that all
        `Node` instances in the provided list, except for the first, will be
        removed from the `NodeTree` and re-inserted in order as siblings after
        the first `Node` in the list.
        '''
        if not nodes:
            return
        self._ungroup_in_progress = True
        try:
            root_paths = [self._node_to_path_map[n] for n in nodes]
            for root in nodes:
                # if the parent is not set, then this node was already
                # removed by removing a parent (or grandparent, etc.)
                if root.parent is None:
                    print 'root is None'
                    continue
                removed = [self.remove(c)[0] for c in root[::-1] if c.parent]
                for node in removed:
                    self.insert_after(root, node)
            self._on_ungrouped(root_paths)
        finally:
            self._ungroup_in_progress = False

    def group(self, nodes):
        '''
        Group the specified list of `Node` instances together.  This means that
        the first `Node` in the list becomes the root `Node` for the group, and
        the rest of the `Node` instances are appended as children to the root.
        '''
        if not nodes:
            return
        self._group_in_progress = True
        try:
            node_paths, nodes = zip(*sorted([(self._node_to_path_map[
                    node], node) for node in nodes]))
            root = nodes[0]
            removed = [self.remove(node)[0]
                    for node in nodes[len(nodes) - 1:0:-1]]
            for node in removed[::-1]:
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

    def _reindex(self):
        '''
        The `Node` instances in the tree can be referenced using two different indexes:
            1) path tuple
            2) linear `Node` index (0-index if tree is flattened)

        This method refreshes the two indexes, along with two mappings:
            1) from each `Node` instance to the corresponding path tuple
            1) from each `Node` instance to the corresponding linear index
        '''
        self._reset_index()
        for index, node_path, node in [i for i in self._iter_children()]:
            self._node_to_path_map[node] = node_path
            self._id_to_path_map.append(node_path)
            self._node_to_id_map[node] = index

    def _iter_children(self, node=None):
        '''
        Iterate through the `Node` instances in the tree in depth-first
        pre-visit order, starting at the specified `Node`.  If no `Node` is
        given, start at the first `Node` in the tree.

        Each iteration yields the following tuple:

            (linear index, path tuple [relative to `node`], `Node` reference)

        For example, consider the following `NodeTree`:

        >>> node_tree = NodeTree()
        >>> for letter in 'ABCDE': node_tree.append_node(Node(letter))#doctest: +ELLIPSIS
        <...>
        >>> node_tree.append_child(node_tree[2], Node('C.A'))
        >>> node_tree.append_child(node_tree[2, 0], Node('C.A.A'))
        >>> node_tree.append_child(node_tree[2, 0], Node('C.A.B'))
        >>> node_tree.append_child(node_tree[2], Node('C.B'))
        >>> print node_tree  #doctest: +NORMALIZE_WHITESPACE
        [ 0] (0,) Node(item=A)
        [ 1] (1,) Node(item=B)
        [ 2] (2,) Node(item=C)
        [ 3] (2, 0) Node(item=C.A)
        [ 4] (2, 0, 0) Node(item=C.A.A)
        [ 5] (2, 0, 1) Node(item=C.A.B)
        [ 6] (2, 1) Node(item=C.B)
        [ 7] (3,) Node(item=D)
        [ 8] (4,) Node(item=E)

        Now, let's print the list of tuples returned by the `_iter_children`
        with no `node` specified:

        >>> pprint(list(node_tree._iter_children())) #doctest: +ELLIPSIS
        [(0, (0,), <...Node object at 0x...>),
         (1, (1,), <...Node object at 0x...>),
         (2, (2,), <...Node object at 0x...>),
         (3, (2, 0), <...Node object at 0x...>),
         (4, (2, 0, 0), <...Node object at 0x...>),
         (5, (2, 0, 1), <...Node object at 0x...>),
         (6, (2, 1), <...Node object at 0x...>),
         (7, (3,), <...Node object at 0x...>),
         (8, (4,), <...Node object at 0x...>)]

        Here we see that the `Node` instances are visited in depth-first
        pre-visit order.

        Now, let's print the list of tuples returned by the `_iter_children`
        relative to `node`:

        >>> pprint(list(node_tree._iter_children(node_tree[2, 0]))) #doctest: +ELLIPSIS
        [(9, (), <...Node object at 0x...>),
         (10, (0,), <...Node object at 0x...>),
         (11, (1,), <...Node object at 0x...>)]

        Here we see that the `Node` instances in the sub-tree rooted at `node`
        are visited in depth-first pre-visit order.  Note that although the
        path tuple is relative to `node`, the linear index is relative to the
        root of the main tree.
        '''
        if node is None:
            node = self.root
            self._counts = [0]
            self._depth = -1
            self._index = 0
        if node != self.root:
            # If we're starting somewhere other than the root of the tree,
            # start the traversal with the specified `Node`.  Otherwise, we
            # just carry on with the top-level `Node` instances of the tree.
            yield self._index, tuple(self._counts[:self._depth + 1]), node
            self._index += 1

        # We increase the depth level since we are going to traverse the
        # children of `node`, which are one level deeper.
        self._depth += 1

        # Keep track of the maximum depth reached for fast access later.
        self._max_depth = max(self._max_depth, self._depth)

        # We need to keep track of the path tuple for the current `Node`.  We
        # do this by keeping a running sum of the number of children in the
        # current sub-tree level.  The sum for each level is stored in a list
        # at the index corresponding to the tree level.  This list is called
        # `_counts`.
        # Here, we add a zero to the `_counts` list if this is the first `Node`
        # we're visiting at this sub-tree level.
        while len(self._counts) < self._depth + 1:
            self._counts.append(0)

        # Perform depth-first traversal by calling `_iter_children()`
        # recursively on the children.
        for child in node:
            for child_node in self._iter_children(child):
                yield child_node
            # We need to increment the `Node` count for the current sub-tree
            # level.
            self._counts[self._depth] += 1
        # The depth decreases by one here since we've processed all children of
        # `node`.
        self._depth -= 1
        del self._counts[self._depth + 1:]

    def _get_node(self, parent, node_path):
        '''
        Get `Node` at the path `node_path` relative to the `Node` `parent`.

        For example, consider the following `NodeTree`:

        >>> node_tree = NodeTree()
        >>> for letter in 'ABCDE': node_tree.append_node(Node(letter))#doctest: +ELLIPSIS
        <...>
        >>> node_tree.append_child(node_tree[2], Node('C.A'))
        >>> node_tree.append_child(node_tree[2, 0], Node('C.A.A'))
        >>> node_tree.append_child(node_tree[2, 0], Node('C.A.B'))
        >>> node_tree.append_child(node_tree[2], Node('C.B'))
        >>> print node_tree  #doctest: +NORMALIZE_WHITESPACE
        [ 0] (0,) Node(item=A)
        [ 1] (1,) Node(item=B)
        [ 2] (2,) Node(item=C)
        [ 3] (2, 0) Node(item=C.A)
        [ 4] (2, 0, 0) Node(item=C.A.A)
        [ 5] (2, 0, 1) Node(item=C.A.B)
        [ 6] (2, 1) Node(item=C.B)
        [ 7] (3,) Node(item=D)
        [ 8] (4,) Node(item=E)

        Now, let's consider node `[2, 0]`, with `item='C.A'`.  Using this
        `Node` as a point of reference, let's look up the `Node` at the
        relative path tuple (0, ):

        >>> print node_tree._get_node(node_tree[2, 0], (0, ))
        Node(item=C.A.A)

        Here we can see that the first child of `Node [2, 0]` is returned, as
        expected.

        Now, let's look up the `Node` at relative path (1, ):

        >>> print node_tree._get_node(node_tree[2, 0], (1, ))
        Node(item=C.A.B)

        Here we can see that the second child of `Node [2, 0]` is returned, as
        expected.

        And finally, let's look up the `Node` at relative path that is one
        level deeper, (0, 1, ):

        >>> print node_tree._get_node(node_tree[2], (0, 1, ))
        Node(item=C.A.B)

        Here we can see that the second grandchild of `Node [2, 0]` is returned,
        as expected.
        '''
        if len(node_path) > 1:
            return self._get_node(parent[node_path[0]],
                    node_path[1:])
        else:
            return parent[node_path[0]]

    def __iter__(self):
        '''
        Iterate through each node in the tree in flattened order (i.e.,
        depth-first).

        Each iteration yields the following tuple:
            (path tuple, `Node` reference)
        '''
        for i in range(len(self)):
            yield self._id_to_path_map[i], self[i]

    def __getitem__(self, key):
        '''
        Return an item corresponding to the provided `key`.

        `key` can either be a path tuple, or a linear index (i.e., the index of
        the `Node` as if the tree was flattened).
        '''
        try:
            len(key)
            # The key has a length, so interpret it as a path tuple.
            return self._get_node(self.root, key)
        except TypeError:
            # The key does have a length, so interpret it as a linear index.
            return self._get_node(self.root, self._id_to_path_map[key])

    def __len__(self):
        return len(self._id_to_path_map)

    def on_ungrouped(self, root_paths):
        logging.debug('[on_ungrouped] root_paths=%s' % root_paths)

    def on_grouped(self, parent_path, children_paths):
        logging.debug('[on_grouped] parent_path=%s children_paths=%s' % (
                parent_path, children_paths))

    def on_node_inserted(self, *args, **kwargs):
        logging.debug('[on_node_inserted] args=%s kwargs=%s' % (args, kwargs))

    def on_node_appended(self, *args, **kwargs):
        logging.debug('[on_node_appended] args=%s kwargs=%s group=%s ungroup=%s' % (
                args, kwargs, self._group_in_progress,
                        self._ungroup_in_progress))

    def on_node_removed(self, *args, **kwargs):
        logging.debug('[on_node_removed] args=%s kwargs=%s' % (args, kwargs))

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

    def append_node(self, node):
        '''
        Append `node` to the list of top-level `Node` instances in the tree.
        '''
        if self.root.children:
            sibling_path = (self._node_to_path_map[self[-1]][0], )
            self.insert_after(self[sibling_path], node)
        else:
            self.append_child(self.root, node)
        return node

    def append_child(self, parent, node):
        '''
        Append `node` to the children of `parent`, where `node` is either a
        `Node` instance or a `NodeTree` instance with a single top-level
        `Node`.
        '''
        node = parent.append_node(node)
        self._on_node_appended(node)

    def _insert_relative(self, insert_func, sibling, node):
        '''
        Common code for inserting `node` either before or after `sibling`.
        '''
        position = insert_func(sibling, node)
        sibling_path = self._node_to_path_map[sibling]
        self._on_node_inserted(sibling_path[:-1] + (position, ), node)

    def insert_before(self, sibling, node):
        '''
        Insert `node` before `sibling` `Node`, on same level.
        '''
        self._insert_relative(Node.insert_before, sibling, node)

    def insert_after(self, sibling, node):
        '''
        Insert `node` after `sibling` `Node`, on same level.
        '''
        self._insert_relative(Node.insert_after, sibling, node)

    def insert(self, node_path, node):
        '''
        Insert the provided `Node` before the provided `node_path` tuple.  If
        there is currently no `Node` at the path `node_path`, the `Node` will be
        inserted at the last position at the deepest level of the `node_path`.
        '''
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
        '''
        Remove `node` (along with all descendents) from tree.

        Return `NodeTree` instance with a single top-level `Node`, containing
        the full removed sub-tree.
        '''
        node_path = self._node_to_path_map[node]
        node.parent.remove_node(node)
        node_tree = node.get_tree()
        self._on_node_removed(node_path, node_tree)
        return node_tree

    def copy(self):
        return copy.deepcopy(self)


class Node(object):
    '''
    This class implements the atomic element contained in a NodeTree.  Each
    Node may contain a list of zero or more child nodes.  Child nodes can be
    added using any of the following methods:
        a) insert_before(node)
            Insert the provided node as a sibling before `self` in the list of
            children for `self`.parent
        b) insert_after(node)
            Insert the provided node as a sibling after `self` in the list of
            children for `self`.parent
        c) append_node(child)
            Insert the provided node at the end of the list of children for
            `self`
        d) remove_node(node)
            Remove specified node from the children of `self`.
    '''
    tree_class = NodeTree

    def __init__(self, item=None):
        self.parent = None
        self.item = item
        self.children = []

    def __str__(self):
        return 'Node(item=%s)' % (self.item, )

    def insert_before(self, node):
        '''
        Insert the provided node as a sibling before `self` in the list of
        children for `self`.parent
        '''
        node.parent = self.parent
        position = node.parent.index(self)
        node.parent.children.insert(position, node)
        return position

    def insert_after(self, node):
        '''
        Insert the provided node as a sibling after `self` in the list of
        children for `self`.parent
        '''
        node.parent = self.parent
        position = node.parent.index(self)
        node.parent.children.insert(position + 1, node)
        return position + 1

    def append_node(self, child):
        '''
        Insert the provided node at the end of the list of children for `self`
        '''
        child.parent = self
        self.children.append(child)

    def remove_node(self, node):
        '''
        Remove specified node from the children of `self`.
        '''
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
        '''
        Return a shallow copy of `self` (no children are set).
        '''
        return self.__class__(item=self.item)

    def copy(self):
        '''
        Return a deep copy of `self`, recursively copying all all ancestors of
        `self`.  Note that although all `Node` instances are copied by value
        here, all `Node.item` values are only copied by reference (which makes
        sense, since you might want to reference the same object in multiple
        tree structures).
        '''
        new_node = self._copy_single()
        new_node.children = [child.copy() for child in self.children]
        for child in new_node:
            child.parent = new_node
        return new_node


_node_tree_dot_template_str = '''\
digraph G {
{{ extra }}
    rankdir="LR";
{{ edges }}
}
'''


def node_tree_to_dot(node_tree, extra_dot=''):
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
        return template.render(edges=sio.getvalue(), extra=extra_dot)

