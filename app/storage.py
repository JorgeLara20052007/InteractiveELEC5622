"""SQLite persistence for the course tree.

The database (data/tree.db) is the live store the UI reads and writes. A JSON snapshot
(data/seed.json) is the git-friendly copy: it seeds an empty database, and
`python -m app.export_json` writes the current database back to it.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from . import tree
from .tree import Node

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_FILE = DATA_DIR / "tree.db"
SEED_FILE = DATA_DIR / "seed.json"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    id         TEXT PRIMARY KEY,
    parent_id  TEXT REFERENCES nodes(id) ON DELETE CASCADE,
    label      TEXT NOT NULL,
    definition TEXT NOT NULL DEFAULT '',
    position   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS nodes_parent ON nodes(parent_id);
"""


def _connect(db: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init(db: Path = DB_FILE, seed: Path | None = SEED_FILE) -> None:
    """Create the schema; if the database is empty, fill it from the seed file."""
    db.parent.mkdir(parents=True, exist_ok=True)
    with closing(_connect(db)) as conn, conn:
        conn.executescript(_SCHEMA)
        empty = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0] == 0
    if empty and seed is not None and seed.exists():
        import_tree(Node.model_validate_json(seed.read_text(encoding="utf-8")), db)


def import_tree(root: Node, db: Path = DB_FILE) -> None:
    """Replace the whole database content with the given tree."""
    tree.validate_unique_ids(root)
    rows: list[tuple] = []

    def collect(node: Node, parent_id: str | None, position: int) -> None:
        rows.append((node.id, parent_id, node.label, node.definition, position))
        for i, child in enumerate(node.children):
            collect(child, node.id, i)

    collect(root, None, 0)
    with closing(_connect(db)) as conn, conn:
        conn.execute("DELETE FROM nodes")
        conn.executemany("INSERT INTO nodes VALUES (?, ?, ?, ?, ?)", rows)


def load(db: Path = DB_FILE) -> Node:
    with closing(_connect(db)) as conn:
        rows = conn.execute("SELECT * FROM nodes ORDER BY position, rowid").fetchall()
    nodes = {r["id"]: Node(id=r["id"], label=r["label"], definition=r["definition"]) for r in rows}
    roots = []
    for r in rows:
        if r["parent_id"] is None:
            roots.append(nodes[r["id"]])
        else:
            nodes[r["parent_id"]].children.append(nodes[r["id"]])
    if len(roots) != 1:
        raise ValueError(f"expected exactly one root node, found {len(roots)}")
    return roots[0]


def add_node(parent_id: str, label: str, definition: str = "", db: Path = DB_FILE) -> Node:
    root = load(db)
    child = tree.add_child(root, parent_id, label, definition)  # validates and picks the id
    position = len(tree.find(root, parent_id).children) - 1
    with closing(_connect(db)) as conn, conn:
        conn.execute(
            "INSERT INTO nodes VALUES (?, ?, ?, ?, ?)",
            (child.id, parent_id, child.label, child.definition, position),
        )
    return child


def update_node(node_id: str, label: str, definition: str, db: Path = DB_FILE) -> Node:
    node = tree.update(load(db), node_id, label=label, definition=definition)
    with closing(_connect(db)) as conn, conn:
        conn.execute(
            "UPDATE nodes SET label = ?, definition = ? WHERE id = ?",
            (node.label, node.definition, node_id),
        )
    return node


def delete_node(node_id: str, db: Path = DB_FILE) -> int:
    """Delete a node and its subtree. Returns how many nodes were removed."""
    removed = tree.delete(load(db), node_id)  # refuses the root, raises if missing
    with closing(_connect(db)) as conn, conn:
        conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))  # children cascade
    return removed


def export_json(out: Path = SEED_FILE, db: Path = DB_FILE) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(load(db).model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
