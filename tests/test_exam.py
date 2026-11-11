import pytest

from app import exam, storage, trees
from app.tree import Node


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "t.db"
    storage.init(path, seed=None)
    storage.import_tree(Node(id="r", label="Course"), path)
    exam.init(path)
    return path


def test_default_sections_are_the_ten_weeks(db):
    labels = [s["label"] for s in exam.sections(db)]
    assert labels == ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6", "Week 7", "Week 10", "Week 11", "Week 12"]
    assert all(s["questions"] == [] for s in exam.sections(db))


def test_init_twice_does_not_duplicate_sections(db):
    exam.init(db)
    assert len(exam.sections(db)) == 10


def test_add_edit_delete_question(db):
    week3 = exam.sections(db)[2]["id"]
    q1 = exam.add_question(db, week3, "  What is **PPV**?  ", "$$TP/(TP+FP)$$")
    q2 = exam.add_question(db, week3, "Second?", "")
    questions = exam.sections(db)[2]["questions"]
    assert [q["id"] for q in questions] == [q1, q2]  # kept in the order they were added
    assert questions[0]["question"] == "What is **PPV**?"
    exam.update_question(db, q1, "What is PPV?", "precision")
    assert exam.get_question(db, q1)["solution"] == "precision"
    exam.delete_question(db, q2)
    assert [q["id"] for q in exam.sections(db)[2]["questions"]] == [q1]


def test_bad_input_is_rejected(db):
    week1 = exam.sections(db)[0]["id"]
    with pytest.raises(ValueError):
        exam.add_question(db, week1, "   ")
    with pytest.raises(KeyError):
        exam.add_question(db, 9999, "Q?")
    with pytest.raises(KeyError):
        exam.update_question(db, 9999, "Q?", "")
    with pytest.raises(KeyError):
        exam.delete_question(db, 9999)


def test_export_then_init_restores_everything(db, tmp_path):
    week10 = exam.sections(db)[7]["id"]
    exam.add_question(db, week10, "Define SVM margin", "The distance…")
    out = tmp_path / "exams" / "t.json"
    exam.export_json(db, out)

    fresh = tmp_path / "fresh.db"
    storage.init(fresh, seed=None)
    exam.init(fresh, out)
    restored = exam.sections(fresh)
    assert [s["label"] for s in restored] == [s["label"] for s in exam.sections(db)]
    assert restored[7]["questions"][0]["question"] == "Define SVM margin"
    assert restored[7]["questions"][0]["solution"] == "The distance…"


def test_trees_create_and_export_include_exam_questions(tmp_path, monkeypatch):
    monkeypatch.setattr(trees, "TREES_DIR", tmp_path)
    slug = trees.create_tree("Course B")
    db = trees.db_path(slug)
    exam.add_question(db, exam.sections(db)[0]["id"], "Q?", "A")
    trees.export_all()
    assert trees.exam_path(slug).exists()
    assert trees.list_slugs() == [slug]  # the exams folder is not mistaken for a tree


def test_exam_page_is_served_next_to_the_others(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(trees, "TREES_DIR", tmp_path)
    trees.create_tree("Course A")
    http = main.create_app().server.test_client()
    page = http.get("/exam/")
    assert page.status_code == 200 and b"/exam/_dash-" in page.data
    assert http.get("/exam").headers["Location"].endswith("/exam/")
    assert "exam-sections" in http.get("/exam/_dash-layout").get_data(as_text=True)
    assert http.get("/study/").status_code == 200 and http.get("/").status_code == 200
