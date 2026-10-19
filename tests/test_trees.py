import pytest

from app import storage, trees
from app.tree import Node


@pytest.fixture(autouse=True)
def trees_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(trees, "TREES_DIR", tmp_path)
    return tmp_path


@pytest.mark.parametrize(
    "name, slug",
    [("ELEC5622", "elec5622"), ("Signal Processing 101", "signal-processing-101"), (" ¡¡ ", "tree")],
)
def test_slugify(name, slug):
    assert trees.slugify(name) == slug


def test_create_tree_writes_json_and_database(trees_dir):
    slug = trees.create_tree("  COMP2017 Systems  ")
    assert slug == "comp2017-systems"
    assert (trees_dir / "comp2017-systems.json").exists()
    assert (trees_dir / "comp2017-systems.db").exists()
    root = storage.load(trees.db_path(slug))
    assert (root.id, root.label, root.children) == ("comp2017-systems", "COMP2017 Systems", [])
    assert Node.model_validate_json(trees.seed_path(slug).read_text(encoding="utf-8")) == root


def test_create_tree_makes_names_unique_and_rejects_blank():
    assert trees.create_tree("Maths") == "maths"
    assert trees.create_tree("Maths") == "maths-2"
    with pytest.raises(ValueError):
        trees.create_tree("   ")


def test_trees_are_independent():
    a, b = trees.create_tree("A"), trees.create_tree("B")
    storage.add_node(a, "only in A", db=trees.db_path(a))
    assert storage.load(trees.db_path(b)).children == []
    assert [c.label for c in storage.load(trees.db_path(a)).children] == ["only in A"]


def test_a_tree_exists_if_it_has_either_file(trees_dir):
    trees.create_tree("Both")
    (trees_dir / "json-only.json").write_text(Node(id="json-only", label="JSON only").model_dump_json())
    storage.init(trees_dir / "db-only.db", seed=None)
    storage.import_tree(Node(id="db-only", label="DB only"), trees_dir / "db-only.db")
    assert trees.list_slugs() == ["both", "db-only", "json-only"]
    assert [o["label"] for o in trees.options()] == ["Both", "DB only", "JSON only"]


def test_init_all_builds_missing_databases_from_json(trees_dir):
    (trees_dir / "fresh.json").write_text(Node(id="fresh", label="Fresh").model_dump_json())
    assert not (trees_dir / "fresh.db").exists()
    trees.init_all()
    assert storage.load(trees.db_path("fresh")).label == "Fresh"


def test_resolve_falls_back_to_something_that_exists():
    assert trees.resolve("nope") == trees.DEFAULT_SLUG  # nothing exists yet
    trees.create_tree("Maths")
    assert trees.resolve("maths") == "maths"
    assert trees.resolve("nope") == "maths"  # no default tree here, so the first one
    trees.create_tree("ELEC5622")
    assert trees.resolve(None) == "elec5622"


def test_export_all_updates_each_json(trees_dir):
    slug = trees.create_tree("Maths")
    storage.add_node(slug, "Algebra", db=trees.db_path(slug))
    assert trees.export_all() == [slug]
    exported = Node.model_validate_json(trees.seed_path(slug).read_text(encoding="utf-8"))
    assert [c.label for c in exported.children] == ["Algebra"]
