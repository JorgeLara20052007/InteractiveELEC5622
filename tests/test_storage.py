import sqlite3

import pytest

from app import storage
from app.tree import Node


def make_root() -> Node:
    return Node(
        id="root",
        label="ELEC5622",
        children=[
            Node(id="w1", label="Week 1", definition="d", children=[Node(id="w1-a", label="A")]),
            Node(id="w2", label="Week 2"),
        ],
    )


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "tree.db"
    storage.init(path, seed=None)
    storage.import_tree(make_root(), path)
    return path


def test_import_then_load_round_trip(db):
    assert storage.load(db) == make_root()


def test_init_seeds_empty_db_only_once(tmp_path):
    seed = tmp_path / "seed.json"
    seed.write_text(make_root().model_dump_json(), encoding="utf-8")
    path = tmp_path / "tree.db"
    storage.init(path, seed)
    storage.add_node("w2", "Extra", db=path)
    storage.init(path, seed)  # must not overwrite the user's additions
    assert storage.load(path).children[1].children[0].label == "Extra"


def test_add_node_persists_with_order(db):
    first = storage.add_node("w2", "Body planes", "three planes", db)
    second = storage.add_node("w2", "Body planes", db=db)
    assert (first.id, second.id) == ("w2-body-planes", "w2-body-planes-2")
    w2 = storage.load(db).children[1]
    assert [c.label for c in w2.children] == ["Body planes", "Body planes"]
    assert w2.children[0].definition == "three planes"


def test_add_node_rejects_bad_input(db):
    with pytest.raises(KeyError):
        storage.add_node("missing", "X", db=db)
    with pytest.raises(ValueError):
        storage.add_node("w1", "   ", db=db)


def test_update_node(db):
    storage.update_node("w1-a", "New", "new def", db)
    node = storage.load(db).children[0].children[0]
    assert (node.label, node.definition) == ("New", "new def")
    with pytest.raises(ValueError):
        storage.update_node("w1-a", "", "x", db)


def test_delete_node_removes_subtree(db):
    assert storage.delete_node("w1", db) == 2
    assert [c.id for c in storage.load(db).children] == ["w2"]
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0] == 2


def test_delete_root_or_missing_fails(db):
    with pytest.raises(ValueError):
        storage.delete_node("root", db)
    with pytest.raises(KeyError):
        storage.delete_node("missing", db)
    assert storage.load(db) == make_root()


def test_export_json_round_trip(db, tmp_path):
    storage.add_node("w2", "Added", db=db)
    out = tmp_path / "snap.json"
    storage.export_json(out, db)
    assert Node.model_validate_json(out.read_text(encoding="utf-8")) == storage.load(db)
