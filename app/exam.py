"""Practice exam questions: sections (e.g. "Week 1") holding questions with their solutions.

They live in the same SQLite database as their tree (tables `exam_sections` and
`exam_questions`), and are exported next to the tree as data/trees/exams/<slug>.json so they
travel with git like the tree does. Question and solution text is Markdown.
"""

from __future__ import annotations

import json
from contextlib import closing
from pathlib import Path

from . import storage

DEFAULT_SECTIONS = [f"Week {n}" for n in (1, 2, 3, 4, 5, 6, 7, 10, 11, 12)]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS exam_sections (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    label    TEXT NOT NULL,
    position INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS exam_questions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id INTEGER NOT NULL REFERENCES exam_sections(id) ON DELETE CASCADE,
    position   INTEGER NOT NULL,
    question   TEXT NOT NULL,
    solution   TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS exam_questions_section ON exam_questions(section_id);
"""


def init(db: Path, snapshot: Path | None = None) -> None:
    """Create the tables. The first time, fill them from the JSON snapshot if there is one,
    otherwise create the default sections."""
    with closing(storage._connect(db)) as conn, conn:
        conn.executescript(_SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM exam_sections").fetchone()[0]:
            return
        if snapshot is not None and snapshot.exists():
            data = json.loads(snapshot.read_text(encoding="utf-8"))
        else:
            data = {"sections": [{"label": label, "questions": []} for label in DEFAULT_SECTIONS]}
        for i, section in enumerate(data["sections"]):
            section_id = conn.execute(
                "INSERT INTO exam_sections (label, position) VALUES (?, ?)", (section["label"], i)
            ).lastrowid
            conn.executemany(
                "INSERT INTO exam_questions (section_id, position, question, solution) VALUES (?, ?, ?, ?)",
                [(section_id, j, q["question"], q.get("solution", "")) for j, q in enumerate(section["questions"])],
            )


def sections(db: Path) -> list[dict]:
    """[{"id", "label", "questions": [{"id", "question", "solution"}, ...]}, ...] in order."""
    with closing(storage._connect(db)) as conn:
        rows = conn.execute("SELECT id, label FROM exam_sections ORDER BY position, id").fetchall()
        questions = conn.execute(
            "SELECT id, section_id, question, solution FROM exam_questions ORDER BY position, id"
        ).fetchall()
    out = [{"id": r["id"], "label": r["label"], "questions": []} for r in rows]
    by_id = {s["id"]: s for s in out}
    for q in questions:
        by_id[q["section_id"]]["questions"].append(
            {"id": q["id"], "question": q["question"], "solution": q["solution"]}
        )
    return out


def get_question(db: Path, question_id: int) -> dict | None:
    with closing(storage._connect(db)) as conn:
        row = conn.execute(
            "SELECT id, section_id, question, solution FROM exam_questions WHERE id = ?", (question_id,)
        ).fetchone()
    return dict(row) if row else None


def _check(question: str) -> str:
    question = (question or "").strip()
    if not question:
        raise ValueError("The question cannot be empty.")
    return question


def add_question(db: Path, section_id: int, question: str, solution: str = "") -> int:
    question = _check(question)
    with closing(storage._connect(db)) as conn, conn:
        if not conn.execute("SELECT 1 FROM exam_sections WHERE id = ?", (section_id,)).fetchone():
            raise KeyError(f"no section with id {section_id!r}")
        position = conn.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 FROM exam_questions WHERE section_id = ?", (section_id,)
        ).fetchone()[0]
        return conn.execute(
            "INSERT INTO exam_questions (section_id, position, question, solution) VALUES (?, ?, ?, ?)",
            (section_id, position, question, solution or ""),
        ).lastrowid


def update_question(db: Path, question_id: int, question: str, solution: str) -> None:
    question = _check(question)
    with closing(storage._connect(db)) as conn, conn:
        changed = conn.execute(
            "UPDATE exam_questions SET question = ?, solution = ? WHERE id = ?",
            (question, solution or "", question_id),
        ).rowcount
    if not changed:
        raise KeyError(f"no question with id {question_id!r}")


def delete_question(db: Path, question_id: int) -> None:
    with closing(storage._connect(db)) as conn, conn:
        if not conn.execute("DELETE FROM exam_questions WHERE id = ?", (question_id,)).rowcount:
            raise KeyError(f"no question with id {question_id!r}")


def export_json(db: Path, out: Path) -> None:
    data = {
        "sections": [
            {
                "label": s["label"],
                "questions": [{"question": q["question"], "solution": q["solution"]} for q in s["questions"]],
            }
            for s in sections(db)
        ]
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
