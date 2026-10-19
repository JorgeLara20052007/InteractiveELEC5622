"""Load and save the course tree as JSON."""

from __future__ import annotations

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from .tree import Node, validate_unique_ids

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "tree.json"
MAX_BACKUPS = 20


def load(path: Path = DATA_FILE) -> Node:
    root = Node.model_validate_json(path.read_text(encoding="utf-8"))
    validate_unique_ids(root)
    return root


def save(root: Node, path: Path = DATA_FILE) -> None:
    """Validate, back up the existing file, then replace it atomically."""
    validate_unique_ids(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        _backup(path)

    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(root.model_dump_json(indent=2))
            f.write("\n")
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def _backup(path: Path) -> None:
    backup_dir = path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    shutil.copy2(path, backup_dir / f"{path.stem}-{stamp}{path.suffix}")
    for old in sorted(backup_dir.glob(f"{path.stem}-*{path.suffix}"))[:-MAX_BACKUPS]:
        old.unlink(missing_ok=True)
