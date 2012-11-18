# -*- coding: utf-8 -*-

import sys
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

package_root = path(__file__).abspath().parent.parent.parent
sys.path.insert(0, package_root)


from node_tree.node_tree import NodeTree, Node, node_tree_to_dot


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
    path('00_original.dot').write_bytes(node_tree_to_dot(node_tree, '''
        labelloc="t";
        label="original";
        '''))
    tree_count = 0
    print '''
************************************************************************
[%2d]   Original tree
************************************************************************
'''.strip() % tree_count
    print node_tree

    tree_count += 1
    sub_tree = node_tree[1].get_tree()
    node_tree.insert_after(node_tree[0], copy.deepcopy(sub_tree)[0])
    path('01_insert_1_after_0.dot').write_bytes(node_tree_to_dot(node_tree, '''
        labelloc="t";
        label="01_insert_1_after_0";
        '''))
    print '''
************************************************************************
[%2d]   Insert 1 after 0
************************************************************************''' % tree_count
    print node_tree

    tree_count += 1
    sub_tree = node_tree[15].get_tree()
    node_tree.insert_after(node_tree[14], sub_tree[0])
    path('02_insert_15_after_14.dot').write_bytes(node_tree_to_dot(node_tree, '''
        labelloc="t";
        label="02_insert_15_after_14";
        '''))
    print '''
************************************************************************
[%2d]   Insert 15 after 14
************************************************************************''' % tree_count
    print node_tree

    tree_count += 1
    node_tree.remove(node_tree[12])
    path('03_remove_12.dot').write_bytes(node_tree_to_dot(node_tree, '''
        labelloc="t";
        label="03_remove_12";
        '''))
    print '''
************************************************************************
[%2d]   Remove 12
************************************************************************''' % tree_count
    print node_tree

    tree_count += 1
    sibling = node_tree[9]
    sub_tree = node_tree.remove(node_tree[5])
    node_tree.insert_after(sibling, sub_tree[0])
    path('04_remove_5_insert_after_9.dot').write_bytes(node_tree_to_dot(node_tree, '''
        labelloc="t";
        label="04_remove_5_insert_after_9";
        '''))
    print '''
************************************************************************
[%2d]   Remove 5 insert after 9
************************************************************************''' % tree_count
    print node_tree

    tree_count += 1
    other_tree = NodeTree([node.copy() for node in [node_tree[1], node_tree[5]]])
    node_tree.insert_before(node_tree[0], other_tree[0])
    path('05_copy_1_5_insert_before_0.dot').write_bytes(node_tree_to_dot(node_tree, '''
        labelloc="t";
        label="05_copy_1_5_insert_before_0";
        '''))
    print '''
************************************************************************
[%2d]   Copy 1 5 insert before 0
************************************************************************''' % tree_count
    print node_tree

    tree_count += 1
    node_tree.group([node_tree[i] for i in [0, 4, 5]])
    path('06_group_0_4_5.dot').write_bytes(node_tree_to_dot(node_tree, '''
        labelloc="t";
        label="06_group_0_4_5";
        '''))
    print '''
************************************************************************
[%2d]   Group 0 4 5
************************************************************************''' % tree_count
    print node_tree

    tree_count += 1
    node_tree.ungroup([node_tree[i] for i in [0]])
    path('07_ungroup_0.dot').write_bytes(node_tree_to_dot(node_tree, '''
        labelloc="t";
        label="07_ungroup_0";
        '''))
    print '''
************************************************************************
[%2d]   Ungroup 0
************************************************************************''' % tree_count
    print node_tree

    tree_count += 1
    node_tree.group([node_tree[i] for i in [0, 1, 2, 4, 5]])
    path('08_group_0_1_2_4_5.dot').write_bytes(node_tree_to_dot(node_tree, '''
        labelloc="t";
        label="08_group_0_1_2_4_5";
        '''))
    print '''
************************************************************************
[%2d]   Group 0 1 2 4 5
************************************************************************''' % tree_count
    print node_tree

    tree_count += 1
    node_tree.ungroup([node_tree[i] for i in [0, 16]])
    path('09_ungroup_0_16.dot').write_bytes(node_tree_to_dot(node_tree, '''
        labelloc="t";
        label="09_ungroup_0_16";
        '''))
    print '''
************************************************************************
[%2d]   Ungroup 0 16
************************************************************************''' % tree_count
    print node_tree
