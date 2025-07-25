import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from scraper.icd9 import Node, ICD9
from collections import defaultdict

# Sample hierarchy for testing
# For scraper.icd9.ICD9, hierarchy is a list of codes, not dicts
test_hierarchy = [
    [None, '001-139', '001-009', '001', '001.0'],
    [None, '001-139', '001-009', '002', '002.0']
]

class DummyICD9(ICD9):
    def __init__(self, allcodes):
        self.depth2nodes = defaultdict(dict)
        Node.__init__(self, -1, 'ROOT')
        self.process(allcodes)

def test_node_add_child():
    n1 = Node(0, 'A')
    n2 = Node(1, 'B')
    n1.add_child(n2)
    assert n2 in n1.children
    assert n1.children[0] == n2

def test_node_search_and_find():
    n1 = Node(0, 'A')
    n2 = Node(1, 'B')
    n1.add_child(n2)
    assert n1.search('B')[0] == n2
    assert n1.find('B') == n2
    assert n1.find('C') is None

def test_node_properties():
    n1 = Node(0, 'A')
    n2 = Node(1, 'B')
    n1.add_child(n2)
    n2.parent = n1
    assert n2.parents == [n1, n2]
    assert n1.leaves == [n2]
    assert n2.siblings == [n1.children[0]]
    assert str(n2) == '1\tB'

def test_icd9_tree():
    icd = DummyICD9(test_hierarchy)
    # Test root
    assert icd.code == 'ROOT'
    # Test search/find
    cholera = icd.find('001.0')
    assert cholera is not None
    typhoid = icd.find('002.0')
    assert typhoid is not None
    # Test parents
    assert cholera.parents[0].code == 'ROOT'
    assert cholera.parents[-1].code == '001.0'
    # Test leaves
    leaves = icd.leaves
    codes = [n.code for n in leaves]
    assert '001.0' in codes and '002.0' in codes 