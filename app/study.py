"""Flashcard study sessions over one week of a tree. Pure logic; the page is in study_page.py.

A session is a plain dict (so it fits in a dcc.Store):
    {"tree": slug, "week": week id, "include_all": bool,
     "cards": [node ids in shuffled order], "pos": index of the current card,
     "revealed": whether its definition is showing, "results": [[node id, knew it?], ...]}
Functions return a new dict rather than changing the one they are given.
"""

from __future__ import annotations

import random
from collections.abc import Iterable

from . import tree
from .tree import Node


def concepts(week: Node, include_all: bool = False) -> list[Node]:
    """The week's direct children, or every node below the week when include_all is set."""
    return list(tree.walk(week))[1:] if include_all else list(week.children)


def start(
    slug: str,
    week: Node,
    include_all: bool = False,
    only: Iterable[str] | None = None,
    rng: random.Random | None = None,
) -> dict:
    """A new session over the week's concepts in random order (optionally only the ids in `only`)."""
    ids = [n.id for n in concepts(week, include_all)]
    if only is not None:
        keep = set(only)
        ids = [i for i in ids if i in keep]
    (rng or random).shuffle(ids)
    return {
        "tree": slug,
        "week": week.id,
        "include_all": include_all,
        "cards": ids,
        "pos": 0,
        "revealed": False,
        "results": [],
    }


def finished(session: dict) -> bool:
    return session["pos"] >= len(session["cards"])


def current(session: dict) -> str | None:
    return None if finished(session) else session["cards"][session["pos"]]


def flip(session: dict) -> dict:
    """Show (or hide again) the current card's definition."""
    if finished(session):
        return session
    return {**session, "revealed": not session["revealed"]}


def answer(session: dict, knew_it: bool) -> dict:
    """Record the self-assessment for the current card and move to the next one.

    Ignored unless the definition is showing, so a double click cannot also mark the
    next card before it has been seen.
    """
    if finished(session) or not session["revealed"]:
        return session
    return {
        **session,
        "pos": session["pos"] + 1,
        "revealed": False,
        "results": [*session["results"], [current(session), bool(knew_it)]],
    }


def score(session: dict) -> tuple[int, int]:
    """(cards answered correctly, cards answered)."""
    return sum(1 for _, ok in session["results"] if ok), len(session["results"])


def missed(session: dict) -> list[str]:
    return [node_id for node_id, ok in session["results"] if not ok]
