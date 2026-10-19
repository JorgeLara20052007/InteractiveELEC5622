import pytest
from pydantic import ValidationError

from app import storage, tree
from app.tree import Node


def make_root() -> Node:
    return Node(id="root", label="ELEC5622", children=[Node(id="w1", label="Week 1", definition="d")])


def test_round_trip(tmp_path):
    path = tmp_path / "tree.json"
    storage.save(make_root(), path)
    assert storage.load(path) == make_root()


def test_save_backs_up_previous_version(tmp_path):
    path = tmp_path / "tree.json"
    root = make_root()
    storage.save(root, path)
    assert not (tmp_path / "backups").exists()

    tree.add_child(root, "w1", "A")
    storage.save(root, path)
    backups = list((tmp_path / "backups").iterdir())
    assert len(backups) == 1
    assert storage.load(backups[0]) == make_root()
    assert storage.load(path) == root


def test_backups_are_capped(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MAX_BACKUPS", 3)
    path = tmp_path / "tree.json"
    root = make_root()
    for _ in range(6):
        storage.save(root, path)
    assert len(list((tmp_path / "backups").iterdir())) == 3


def test_save_rejects_duplicate_ids_and_keeps_old_file(tmp_path):
    path = tmp_path / "tree.json"
    storage.save(make_root(), path)
    bad = make_root()
    bad.children.append(Node(id="w1", label="dup"))
    with pytest.raises(ValueError):
        storage.save(bad, path)
    assert storage.load(path) == make_root()
    assert list(tmp_path.glob("*.tmp")) == []


def test_load_rejects_malformed_file(tmp_path):
    path = tmp_path / "tree.json"
    path.write_text('{"id": "root"}', encoding="utf-8")
    with pytest.raises(ValidationError):
        storage.load(path)
