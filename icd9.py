import csv
import json
from collections import *
from typing import List, Optional, Any

class Node:
    def __init__(self, depth: int, code: str, descr: Optional[str] = None):
        self.depth: int = depth
        self.descr: str = descr or code
        self.code: str = code
        self.parent: Optional['Node'] = None
        self.children: List['Node'] = []

    def add_child(self, child: 'Node') -> None:
        if child not in self.children:
            self.children.append(child)

    def search(self, code: str) -> List['Node']:
        if code == self.code:
            return [self]
        ret = []
        for child in self.children:
            ret.extend(child.search(code))
        return ret

    def find(self, code: str) -> Optional['Node']:
        nodes = self.search(code)
        if nodes:
            return nodes[0]
        return None

    @property
    def root(self) -> 'Node':
        return self.parents[0]

    @property
    def description(self) -> str:
        return self.descr

    @property
    def codes(self) -> List[str]:
        return [n.code for n in self.leaves]

    @property
    def parents(self) -> List['Node']:
        n = self
        ret = []
        while n:
            ret.append(n)
            n = n.parent
        ret.reverse()
        return ret

    @property
    def leaves(self) -> List['Node']:
        leaves = set()
        if not self.children:
            return [self]
        for child in self.children:
            leaves.update(child.leaves)
        return list(leaves)

    def leaves_at_depth(self, depth: int) -> List['Node']:
        return [n for n in self.leaves if n.depth == depth]

    @property
    def siblings(self) -> List['Node']:
        parent = self.parent
        if not parent:
            return []
        return list(parent.children)

    def __str__(self) -> str:
        return f"{self.depth}\t{self.code}"

    def __hash__(self) -> int:
        return hash(str(self))


class ICD9(Node):
    def __init__(self, codesfname: str):
        self.depth2nodes: dict[int, dict[str, Node]] = defaultdict(dict)
        super().__init__(-1, 'ROOT')
        with open(codesfname, 'r') as f:
            allcodes = json.load(f)
            self.process(allcodes)

    def process(self, allcodes: Any) -> None:
        for hierarchy in allcodes:
            self.add(hierarchy)

    def get_node(self, depth: int, code: str, descr: str) -> Node:
        d = self.depth2nodes[depth]
        if code not in d:
            d[code] = Node(depth, code, descr)
        return d[code]

    def add(self, hierarchy: Any) -> None:
        prev_node = self
        for depth, link in enumerate(hierarchy):
            if not link['code']:
                continue
            code = link['code']
            descr = link['descr'] if 'descr' in link else code
            node = self.get_node(depth, code, descr)
            node.parent = prev_node
            prev_node.add_child(node)
            prev_node = node


if __name__ == '__main__':
    tree = ICD9('codes.json')
    counter = Counter([str(x) for x in tree.leaves])
    import pdb
    pdb.set_trace()
