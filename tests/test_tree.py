import pytest

from app import tree
from app.tree import Node


@pytest.fixture
def root() -> Node:
    return Node(
        id="root",
        label="ELEC5622",
        children=[
            Node(
                id="w1",
                label="Week 1",
                children=[Node(id="w1-a", label="A", definition="def A")],
            ),
            Node(id="w2", label="Week 2"),
        ],
    )


def test_find_and_path(root):
    assert tree.find(root, "w1-a").definition == "def A"
    assert tree.find(root, "nope") is None
    assert [n.id for n in tree.find_path(root, "w1-a")] == ["root", "w1", "w1-a"]
    assert tree.find_path(root, "nope") is None


def test_add_child_generates_readable_unique_ids(root):
    first = tree.add_child(root, "w2", "Body Planes!", "three planes")
    second = tree.add_child(root, "w2", "Body planes")
    assert first.id == "w2-body-planes"
    assert second.id == "w2-body-planes-2"
    assert tree.find(root, "w2").children == [first, second]


def test_add_child_rejects_bad_input(root):
    with pytest.raises(KeyError):
        tree.add_child(root, "missing", "X")
    with pytest.raises(ValueError):
        tree.add_child(root, "w1", "X", node_id="w2")
    with pytest.raises(ValueError):
        tree.add_child(root, "w1", "   ")


def test_update(root):
    tree.update(root, "w1-a", label=" New ", definition="new def")
    node = tree.find(root, "w1-a")
    assert (node.label, node.definition) == ("New", "new def")
    with pytest.raises(ValueError):
        tree.update(root, "w1-a", label="")
    with pytest.raises(KeyError):
        tree.update(root, "missing", label="x")


def test_delete_returns_removed_count(root):
    assert tree.delete(root, "w1") == 2
    assert tree.find(root, "w1-a") is None
    assert [c.id for c in root.children] == ["w2"]


def test_delete_root_or_missing_fails(root):
    with pytest.raises(ValueError):
        tree.delete(root, "root")
    with pytest.raises(KeyError):
        tree.delete(root, "missing")


def test_validate_unique_ids(root):
    tree.validate_unique_ids(root)
    root.children[1].id = "w1-a"  # clashes with the grandchild
    with pytest.raises(ValueError):
        tree.validate_unique_ids(root)


def test_to_elements(root):
    elements = tree.to_elements(root)
    nodes = [e["data"] for e in elements if "source" not in e["data"]]
    edges = [(e["data"]["source"], e["data"]["target"]) for e in elements if "source" in e["data"]]
    assert [(n["id"], n["depth"]) for n in nodes] == [("root", 0), ("w1", 1), ("w1-a", 2), ("w2", 1)]
    assert edges == [("root", "w1"), ("w1", "w1-a"), ("root", "w2")]


def test_to_elements_branch_is_the_week_index(root):
    branches = {e["data"]["id"]: e["data"]["branch"] for e in tree.to_elements(root) if "source" not in e["data"]}
    assert branches == {"root": -1, "w1": 0, "w1-a": 0, "w2": 1}


def test_to_elements_edges_take_their_childs_branch(root):
    edges = {
        (e["data"]["source"], e["data"]["target"]): e["data"]["branch"]
        for e in tree.to_elements(root)
        if "source" in e["data"]
    }
    assert edges == {("root", "w1"): 0, ("w1", "w1-a"): 0, ("root", "w2"): 1}


def test_to_elements_collapsed_hides_children_and_counts_them(root):
    tree.add_child(root, "w1-a", "B")
    elements = tree.to_elements(root, collapsed={"w1"})
    nodes = {e["data"]["id"]: e["data"] for e in elements if "source" not in e["data"]}
    assert set(nodes) == {"root", "w1", "w2"}
    assert nodes["w1"]["collapsed"] is True
    assert nodes["w1"]["label"].endswith("▸ 2")
    assert "collapsed" not in nodes["w2"]  # a leaf is never shown as collapsed
    assert "collapsed" not in tree.to_elements(root, collapsed={"w2"})[-1]["data"]


def test_iter_paths(root):
    assert [[n.id for n in p] for p in tree.iter_paths(root)] == [
        ["root"],
        ["root", "w1"],
        ["root", "w1", "w1-a"],
        ["root", "w2"],
    ]
