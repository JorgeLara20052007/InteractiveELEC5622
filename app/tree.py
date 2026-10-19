"""Pure tree logic for the course tree. No Dash imports, so it is easy to test."""

from __future__ import annotations

import re
from collections.abc import Collection, Iterator

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Node(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: str
    label: str
    definition: str = ""
    children: list[Node] = Field(default_factory=list)

    @field_validator("id", "label")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


def walk(root: Node) -> Iterator[Node]:
    """Yield every node, parents before children."""
    yield root
    for child in root.children:
        yield from walk(child)


def validate_unique_ids(root: Node) -> None:
    seen: set[str] = set()
    for node in walk(root):
        if node.id in seen:
            raise ValueError(f"duplicate node id: {node.id!r}")
        seen.add(node.id)


def find(root: Node, node_id: str) -> Node | None:
    return next((n for n in walk(root) if n.id == node_id), None)


def find_path(root: Node, node_id: str) -> list[Node] | None:
    """Nodes from the root down to node_id (inclusive), or None if missing."""
    if root.id == node_id:
        return [root]
    for child in root.children:
        sub = find_path(child, node_id)
        if sub is not None:
            return [root, *sub]
    return None


def count_descendants(node: Node) -> int:
    return sum(1 for _ in walk(node)) - 1


def generate_id(root: Node, parent_id: str, label: str) -> str:
    """Readable id like 'w1-anatomical-imaging', made unique with a -2, -3 suffix."""
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "node"
    base = f"{parent_id}-{slug}"
    existing = {n.id for n in walk(root)}
    candidate, n = base, 2
    while candidate in existing:
        candidate = f"{base}-{n}"
        n += 1
    return candidate


def add_child(
    root: Node,
    parent_id: str,
    label: str,
    definition: str = "",
    node_id: str | None = None,
) -> Node:
    parent = find(root, parent_id)
    if parent is None:
        raise KeyError(f"no node with id {parent_id!r}")
    if node_id is not None and find(root, node_id) is not None:
        raise ValueError(f"duplicate node id: {node_id!r}")
    child = Node(
        id=node_id or generate_id(root, parent_id, label),
        label=label,
        definition=definition,
    )
    parent.children.append(child)
    return child


def update(
    root: Node,
    node_id: str,
    label: str | None = None,
    definition: str | None = None,
) -> Node:
    node = find(root, node_id)
    if node is None:
        raise KeyError(f"no node with id {node_id!r}")
    if label is not None:
        node.label = label
    if definition is not None:
        node.definition = definition
    return node


def delete(root: Node, node_id: str) -> int:
    """Remove a node and its subtree. Returns how many nodes were removed."""
    if root.id == node_id:
        raise ValueError("the root node cannot be deleted")
    path = find_path(root, node_id)
    if path is None:
        raise KeyError(f"no node with id {node_id!r}")
    parent, target = path[-2], path[-1]
    parent.children.remove(target)
    return 1 + count_descendants(target)


def iter_paths(root: Node) -> Iterator[list[Node]]:
    """Yield the path from the root to every node, parents before children."""
    yield [root]
    for child in root.children:
        for sub in iter_paths(child):
            yield [root, *sub]


def to_elements(root: Node, collapsed: Collection[str] = ()) -> list[dict]:
    """Flatten to Cytoscape elements: one node entry and one edge per parent-child link.

    Each node carries its `depth` and `branch` (index of the root child it sits under,
    -1 for the root itself) so the stylesheet can colour per week. Children of a node
    whose id is in `collapsed` are left out, and the node shows how many it hides.
    """
    elements: list[dict] = []

    def visit(node: Node, depth: int, branch: int) -> None:
        data = {"id": node.id, "label": node.label, "depth": depth, "branch": branch}
        hide_children = node.id in collapsed and bool(node.children)
        if hide_children:
            data["label"] = f"{node.label}  ▸ {count_descendants(node)}"
            data["collapsed"] = True
        elements.append({"data": data})
        if hide_children:
            return
        for i, child in enumerate(node.children):
            elements.append(
                {"data": {"source": node.id, "target": child.id, "id": f"{node.id}->{child.id}"}}
            )
            visit(child, depth + 1, i if depth == 0 else branch)

    visit(root, 0, -1)
    return elements
