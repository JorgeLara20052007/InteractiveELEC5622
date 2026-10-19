"""SQLite persistence for the course tree.

Each tree is a SQLite database (data/trees/<name>.db) that the UI reads and writes, with a
JSON snapshot next to it (data/trees/<name>.json): the git-friendly copy that seeds an empty
database, and that `python -m app.export_json` writes the current database back to.

Undo/redo: after every change the whole tree is saved as a snapshot row in `history`,
and `meta.cursor` points at the snapshot that matches the live tree. Undo/redo just move
the cursor and restore that snapshot. A new change drops any redo snapshots.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from . import tree
from .tree import Node

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TREES_DIR = DATA_DIR / "trees"  # one <name>.db and one <name>.json per tree (see trees.py)
DB_FILE = TREES_DIR / "elec5622.db"  # defaults used when no tree is given: the original course
SEED_FILE = TREES_DIR / "elec5622.json"
MAX_HISTORY = 200  # snapshots kept; the oldest are dropped first

_SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    id         TEXT PRIMARY KEY,
    parent_id  TEXT REFERENCES nodes(id) ON DELETE CASCADE,
    label      TEXT NOT NULL,
    definition TEXT NOT NULL DEFAULT '',
    position   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS nodes_parent ON nodes(parent_id);
CREATE TABLE IF NOT EXISTS history (
    seq         INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot    TEXT NOT NULL,
    description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value INTEGER NOT NULL
);
"""


def _connect(db: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# --- helpers that work on an open connection (so several steps share one transaction)

def _load(conn: sqlite3.Connection) -> Node:
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


def _replace_nodes(conn: sqlite3.Connection, root: Node) -> None:
    tree.validate_unique_ids(root)
    rows: list[tuple] = []

    def collect(node: Node, parent_id: str | None, position: int) -> None:
        rows.append((node.id, parent_id, node.label, node.definition, position))
        for i, child in enumerate(node.children):
            collect(child, node.id, i)

    collect(root, None, 0)
    conn.execute("DELETE FROM nodes")
    conn.executemany("INSERT INTO nodes VALUES (?, ?, ?, ?, ?)", rows)


def _cursor(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT value FROM meta WHERE key = 'cursor'").fetchone()
    return row["value"] if row else 0


def _set_cursor(conn: sqlite3.Connection, seq: int) -> None:
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('cursor', ?)", (seq,))


def _record(conn: sqlite3.Connection, description: str) -> None:
    """Snapshot the live tree as the new latest state, dropping any redo states."""
    cursor = _cursor(conn)
    conn.execute("DELETE FROM history WHERE seq > ?", (cursor,))
    seq = conn.execute(
        "INSERT INTO history (snapshot, description) VALUES (?, ?)",
        (_load(conn).model_dump_json(), description),
    ).lastrowid
    _set_cursor(conn, seq)
    conn.execute("DELETE FROM history WHERE seq <= ?", (seq - MAX_HISTORY,))


def _reset_history(conn: sqlite3.Connection, description: str) -> None:
    conn.execute("DELETE FROM history")
    _set_cursor(conn, 0)
    _record(conn, description)


# --- public API

def init(db: Path = DB_FILE, seed: Path | None = SEED_FILE) -> None:
    """Create the schema; if the database is empty, fill it from the seed file."""
    db.parent.mkdir(parents=True, exist_ok=True)
    with closing(_connect(db)) as conn, conn:
        conn.executescript(_SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0] == 0:
            if seed is None or not seed.exists():
                return
            _replace_nodes(conn, Node.model_validate_json(seed.read_text(encoding="utf-8")))
            _reset_history(conn, "Load seed")
        elif conn.execute("SELECT COUNT(*) FROM history").fetchone()[0] == 0:
            _reset_history(conn, "Initial state")  # database from before undo existed


def import_tree(root: Node, db: Path = DB_FILE) -> None:
    """Replace the whole database content with the given tree (also resets undo history)."""
    with closing(_connect(db)) as conn, conn:
        _replace_nodes(conn, root)
        _reset_history(conn, "Import tree")


def load(db: Path = DB_FILE) -> Node:
    with closing(_connect(db)) as conn:
        return _load(conn)


def add_node(parent_id: str, label: str, definition: str = "", db: Path = DB_FILE) -> Node:
    root = load(db)
    child = tree.add_child(root, parent_id, label, definition)  # validates and picks the id
    position = len(tree.find(root, parent_id).children) - 1
    with closing(_connect(db)) as conn, conn:
        conn.execute(
            "INSERT INTO nodes VALUES (?, ?, ?, ?, ?)",
            (child.id, parent_id, child.label, child.definition, position),
        )
        _record(conn, f"Add “{child.label}”")
    return child


def update_node(node_id: str, label: str, definition: str, db: Path = DB_FILE) -> Node:
    root = load(db)
    before = tree.find(root, node_id)
    unchanged = before is not None and (before.label, before.definition) == (label.strip(), definition)
    node = tree.update(root, node_id, label=label, definition=definition)
    with closing(_connect(db)) as conn, conn:
        conn.execute(
            "UPDATE nodes SET label = ?, definition = ? WHERE id = ?",
            (node.label, node.definition, node_id),
        )
        if not unchanged:
            _record(conn, f"Edit “{node.label}”")
    return node


def delete_node(node_id: str, db: Path = DB_FILE) -> int:
    """Delete a node and its subtree. Returns how many nodes were removed."""
    root = load(db)
    node = tree.find(root, node_id)
    label = node.label if node else node_id
    removed = tree.delete(root, node_id)  # refuses the root, raises if missing
    with closing(_connect(db)) as conn, conn:
        conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))  # children cascade
        _record(conn, f"Delete “{label}”" + (f" and {removed - 1} below it" if removed > 1 else ""))
    return removed


def history_state(db: Path = DB_FILE) -> tuple[str | None, str | None]:
    """(description of the change undo would revert, description of the one redo would redo)."""
    with closing(_connect(db)) as conn:
        cursor = _cursor(conn)
        current = conn.execute("SELECT description FROM history WHERE seq = ?", (cursor,)).fetchone()
        has_previous = conn.execute("SELECT 1 FROM history WHERE seq < ?", (cursor,)).fetchone()
        nxt = conn.execute(
            "SELECT description FROM history WHERE seq > ? ORDER BY seq LIMIT 1", (cursor,)
        ).fetchone()
    return (
        current["description"] if current and has_previous else None,
        nxt["description"] if nxt else None,
    )


def _move(db: Path, older: bool) -> str | None:
    with closing(_connect(db)) as conn, conn:
        cursor = _cursor(conn)
        if older:
            target = conn.execute(
                "SELECT seq, snapshot FROM history WHERE seq < ? ORDER BY seq DESC LIMIT 1", (cursor,)
            ).fetchone()
            described = conn.execute("SELECT description FROM history WHERE seq = ?", (cursor,)).fetchone()
        else:
            target = conn.execute(
                "SELECT seq, snapshot, description FROM history WHERE seq > ? ORDER BY seq LIMIT 1", (cursor,)
            ).fetchone()
            described = target
        if target is None:
            return None
        _replace_nodes(conn, Node.model_validate_json(target["snapshot"]))
        _set_cursor(conn, target["seq"])
        return described["description"]


def undo(db: Path = DB_FILE) -> str | None:
    """Revert the latest change. Returns its description, or None if there is nothing to undo."""
    return _move(db, older=True)


def redo(db: Path = DB_FILE) -> str | None:
    """Re-apply the change last undone. Returns its description, or None if there is none."""
    return _move(db, older=False)


def export_json(out: Path = SEED_FILE, db: Path = DB_FILE) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(load(db).model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
