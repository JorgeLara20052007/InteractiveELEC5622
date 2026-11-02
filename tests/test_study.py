import random

import pytest

from app import study
from app.tree import Node


@pytest.fixture
def week() -> Node:
    return Node(
        id="w1",
        label="Week 1",
        children=[
            Node(id="a", label="A", children=[Node(id="a1", label="A1")]),
            Node(id="b", label="B"),
            Node(id="c", label="C"),
        ],
    )


def test_concepts_are_direct_children_unless_all_levels_asked(week):
    assert [n.id for n in study.concepts(week)] == ["a", "b", "c"]
    assert [n.id for n in study.concepts(week, include_all=True)] == ["a", "a1", "b", "c"]


def test_start_shuffles_every_concept_once(week):
    s = study.start("t", week, rng=random.Random(1))
    assert sorted(s["cards"]) == ["a", "b", "c"]
    assert (s["tree"], s["week"], s["pos"], s["revealed"], s["results"]) == ("t", "w1", 0, False, [])
    orders = {tuple(study.start("t", week, rng=random.Random(seed))["cards"]) for seed in range(20)}
    assert len(orders) > 1  # really random order


def test_start_can_be_limited_to_some_cards(week):
    s = study.start("t", week, include_all=True, only=["a1", "c", "not-in-week"])
    assert sorted(s["cards"]) == ["a1", "c"]


def test_a_full_round(week):
    s = study.start("t", week, rng=random.Random(0))
    order = list(s["cards"])
    for knew_it in (True, False, True):
        assert study.current(s) == order[s["pos"]]
        s = study.flip(s)
        assert s["revealed"]
        s = study.answer(s, knew_it)
        assert not s["revealed"]
    assert study.finished(s)
    assert study.current(s) is None
    assert study.score(s) == (2, 3)
    assert study.missed(s) == [order[1]]


def test_answer_is_ignored_until_the_definition_is_shown(week):
    s = study.start("t", week)
    assert study.answer(s, True) == s
    s = study.answer(study.flip(s), True)
    assert study.answer(s, True) == s  # a double click does not mark the next card


def test_flip_toggles_and_does_nothing_when_finished(week):
    s = study.start("t", week)
    assert study.flip(study.flip(s))["revealed"] is False
    for _ in range(3):
        s = study.answer(study.flip(s), True)
    assert study.flip(s) == s


def test_a_week_without_concepts_is_finished_at_once():
    s = study.start("t", Node(id="w", label="Empty week"))
    assert study.finished(s)
    assert study.score(s) == (0, 0)


# --- the page is mounted next to the tree page


@pytest.fixture
def server(tmp_path, monkeypatch):
    from app import main, trees

    monkeypatch.setattr(trees, "TREES_DIR", tmp_path)
    trees.create_tree("Course A")
    return main.create_app().server.test_client()


def test_tree_and_study_pages_are_both_served(server):
    assert server.get("/").status_code == 200
    page = server.get("/study/")
    assert page.status_code == 200
    assert b"/study/_dash-" in page.data  # the study app's own scripts, not the tree page's
    assert server.get("/study").headers["Location"].endswith("/study/")


def test_study_layout_lists_the_trees(server):
    layout = server.get("/study/_dash-layout").get_data(as_text=True)
    assert "study-card" in layout and "Course A" in layout
