"""The set of trees: one per course (or any other subject).

Every tree is a pair of files in data/trees/: `<slug>.db` (live SQLite database with undo
history, not committed) and `<slug>.json` (snapshot that seeds the database and is committed).
A tree exists if either file does, so a fresh clone that only has the JSON files still works.
"""

from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from pathlib import Path

from . import storage
from .tree import Node

TREES_DIR = storage.TREES_DIR
DEFAULT_SLUG = "elec5622"


def db_path(slug: str) -> Path:
    return TREES_DIR / f"{slug}.db"


def seed_path(slug: str) -> Path:
    return TREES_DIR / f"{slug}.json"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "tree"


def list_slugs() -> list[str]:
    if not TREES_DIR.exists():
        return []
    return sorted({p.stem for p in TREES_DIR.iterdir() if p.suffix in (".db", ".json")})


def display_name(slug: str) -> str:
    """The root node's label, read from the database, else the JSON snapshot, else the slug."""
    db = db_path(slug)
    if db.exists():
        try:
            with closing(sqlite3.connect(db)) as conn:
                row = conn.execute("SELECT label FROM nodes WHERE parent_id IS NULL").fetchone()
            if row:
                return row[0]
        except sqlite3.Error:
            pass
    seed = seed_path(slug)
    if seed.exists():
        try:
            return Node.model_validate_json(seed.read_text(encoding="utf-8")).label
        except ValueError:
            pass
    return slug


def options() -> list[dict]:
    """Dropdown options, one per tree."""
    return [{"label": display_name(s), "value": s} for s in list_slugs()]


def resolve(slug: str | None) -> str:
    """`slug` if that tree exists, otherwise the default tree (or the first one there is)."""
    slugs = list_slugs()
    if slug in slugs:
        return slug
    return DEFAULT_SLUG if DEFAULT_SLUG in slugs or not slugs else slugs[0]


def init_all() -> None:
    """Make sure every tree has a database, seeding it from its JSON snapshot if needed."""
    for slug in list_slugs():
        storage.init(db_path(slug), seed_path(slug))


def create_tree(name: str) -> str:
    """Create a new, empty tree whose root is `name`. Returns its slug."""
    name = name.strip()
    if not name:
        raise ValueError("Give the tree a name.")
    existing = set(list_slugs())
    base = slugify(name)
    slug, n = base, 2
    while slug in existing:
        slug = f"{base}-{n}"
        n += 1
    root = Node(id=slug, label=name, definition="")  # validates the name too
    TREES_DIR.mkdir(parents=True, exist_ok=True)
    seed_path(slug).write_text(root.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
    storage.init(db_path(slug), seed_path(slug))
    return slug


def export_all() -> list[str]:
    """Write every tree's database back to its JSON snapshot. Returns the slugs exported."""
    exported = []
    for slug in list_slugs():
        if db_path(slug).exists():
            storage.export_json(seed_path(slug), db_path(slug))
            exported.append(slug)
    return exported
