# Workflow: Interactive ELEC5622 course tree

Goal: a big zoomable tree of the course. Click a node to see its definition. Add new
children (with explanations) from the UI, saved in a database.

**Status:** Steps 1 to 7 are built and working (Week 1 content, viewer, definitions,
`+` to add children, edit, delete, collapse, search, colour per week). Step 8 is optional.

## 1. Stack (and why)

| Piece | Choice | Why |
|---|---|---|
| UI framework | **Dash** | Pure Python, runs a local web app, no JavaScript needed |
| Tree widget | **dash-cytoscape** | Built-in zoom/pan, click events, tree layouts, styling |
| Storage | **SQLite (`data/trees/<name>.db`)** | Built into Python, one file, instant saves and deletes, `ON DELETE CASCADE` removes a whole subtree |
| Git snapshot | **`data/trees/<name>.json`** | Readable copy of each tree: seeds an empty database, refreshed with `python -m app.export_json` |
| Validation | **pydantic** | Catches malformed nodes (blank labels, duplicate ids) before they are saved |
| Tests | **pytest** | Tree logic (add/edit/delete/load/save) is testable without a browser |

Alternatives rejected: `pyvis` (hard to edit interactively), Streamlit (reruns the whole
script on each click, awkward for graph interaction), plain D3 (needs JavaScript).

## 2. Data model

One table, `nodes(id, parent_id, label, definition, position)`; `parent_id` is NULL for
the single root. In memory (and in the JSON file) it is a nested tree. Every node has a
stable id so edits and deletes are safe.

```json
{
  "id": "root",
  "label": "ELEC5622",
  "definition": "Course overview.",
  "children": [
    {
      "id": "w1",
      "label": "Week 1: Introduction",
      "definition": "…",
      "children": [
        { "id": "w1-anat", "label": "Anatomical imaging", "definition": "…", "children": [] }
      ]
    }
  ]
}
```

Rules: `id` unique across the whole tree; `label` short (shown on the node);
`definition` Markdown text with `$math$` support (shown in the side panel); `children`
may be empty.
Optional later: `week`, `tags`, `source` (slide/page reference), `collapsed`.

## 3. Proposed project layout

```
InteractiveELEC5622/
├── app/
│   ├── main.py        # creates the Dash app, runs the server
│   ├── layout.py      # page layout: graph on the left, detail panel on the right
│   ├── callbacks.py   # click, add, edit, delete handlers
│   ├── tree.py        # pure tree logic: find/add/edit/delete node, ids, to-cytoscape
│   ├── storage.py     # SQLite: init/seed, load, add/update/delete node, undo/redo, export
│   ├── images.py      # save/serve/upload pictures for definitions
│   ├── study.py       # flashcard session logic (shuffle, flip, answer, score)
│   ├── study_page.py  # the /study/ page: a second Dash app on the same server
│   ├── trees.py       # the set of trees: list, create, export (one .db + .json each)
│   ├── export_json.py # `python -m app.export_json`: every database -> its JSON file
│   └── styles.py      # cytoscape stylesheet (colour per week, edges, '+' node)
├── assets/
│   ├── app.js         # Ctrl+Z / Ctrl+Y, paste an image, click image to enlarge, panel splitter
│   ├── pdf.js         # floating, draggable PDF viewer windows on the tree page
│   └── style.css      # image and table styling inside definitions
├── data/
│   ├── trees/
│   │   ├── elec5622.json  # snapshot of one tree (committed)
│   │   └── elec5622.db    # its live SQLite database + undo history (not committed)
│   └── images/        # pictures used in definitions, shared by all trees (committed)
├── tests/
│   ├── test_tree.py
│   ├── test_storage.py
│   ├── test_images.py
│   ├── test_trees.py
│   ├── test_study.py
│   └── test_styles.py
├── requirements.txt
├── WORKFLOW.md
└── README.md
```

`tree.py` and `storage.py` have no Dash imports, so they can be tested alone.

## 4. Build steps

Each step ends with something you can run or test. Commit after each one.

**Step 1: Data + logic (no UI)** (DONE: 16 tests pass)
- Define the pydantic `Node` model and write `tree.py`: `find`, `add_child`, `update`,
  `delete`, `generate_id`, `to_elements` (nested tree → cytoscape nodes + edges).
- Write `storage.py` on SQLite: init and seed, load, add/update/delete, JSON export.
- Tests: add/delete/edit, duplicate ids rejected, cascade delete, round-trip.
- Done when: `python -m pytest` passes.

**Step 2: Seed content for Week 1** (DONE: 30 nodes in `data/trees/elec5622.json`, from your LaTeX notes)
- Root, Week 1 "Introduction", its six children (Anatomical imaging, Functional imaging,
  Purpose of medical imaging, DICOM format, Body planes, Efficiency of predictive
  modelling) and their sub-nodes with definitions.

**Step 3: Read-only viewer** (DONE)
- `main.py` + `layout.py`: render the tree with cytoscape, using a top-down (dagre) or
  radial layout. Mouse-wheel zoom, drag to pan, drag nodes.
- Done when: the whole Week 1 tree shows and zooms anywhere.

**Step 4: Click to see the definition** (DONE)
- Callback on `tapNode`: show the node's label, definition, path from root
  (e.g. ELEC5622 › Week 1 › Anatomical imaging) and children list in a side panel.
- Highlight the selected node and its direct neighbours.
- Done when: clicking "Anatomical imaging" shows its definition.

**Step 5: Add children with the `+`** (DONE)
- When a node is selected, show a small `+` ghost node attached to it (a canvas can't
  hold real buttons, so a styled clickable node does the job).
- Clicking `+` opens a form in the side panel: label + definition, then **Add**.
- Callback: `storage.add_node` (writes to SQLite) → refresh elements → select the new node.
- Done when: you can add a child and it is still there after restarting the app.

**Step 6: Edit and delete** (DONE)
- Edit button in the panel to change label/definition. Delete with a confirm dialog
  (warn how many descendants go with it). Root cannot be deleted.

**Step 7: Usability for a big tree** (DONE)
- Collapse/expand a subtree with the Collapse/Expand button in the panel (a collapsed
  node shows `▸ N` for the N hidden nodes), plus Collapse all / Expand all above the graph.
  (Not double-click: dash-cytoscape has no double-click event.)
- Search box above the graph: pick a node and its ancestors expand, it is selected and the
  camera zooms to it.
- Colour per week: each child of the root gets its own hue (8 hues, then they repeat),
  lighter for deeper levels. Fit-to-screen button.
- Still open: layout selector. Add Week 2, 3, … as you go through the course.

**Step 8: Polish (partly done)**
- DONE: Markdown and `$math$` in definitions; images in definitions (paste or upload, live
  preview); undo/redo with Ctrl+Z / Ctrl+Y (history stored in the database); connector
  lines coloured per week, with every sibling's horizontal line at the same height.
- Still open: export to PNG/HTML, import from an outline text file, reordering siblings,
  moving a node to a new parent (drag a node onto another), clean up unused images.

**Step 9: Several trees** (DONE)
- Tree picker and **+ New tree** button in the toolbar. A new tree is a new database plus a
  new JSON file in `data/trees/`, named after the tree (`Signal Processing` ->
  `signal-processing.json`). The chosen tree is remembered in the browser.
- Still open: rename or delete a whole tree, copy a tree as a template.

**Step 10: Study mode** (DONE)
- `/study/` page, opened from the **📚 Study** button in a new window: pick a week, get its
  concepts as shuffled flashcards (title only), flip to see the definition, mark yourself
  right or wrong, see the score at the end and retry the ones you missed.
- Still open: remember scores between sessions and show weak concepts more often
  (spaced repetition).

**Step 11: PDF windows** (DONE)
- **📄 PDF** button (or drop a PDF on the page) opens a local PDF in a floating window that
  can be dragged, resized from any edge or corner, maximised, minimised, popped out and
  closed; several at once. Shown by the
  browser's own PDF viewer from a local object URL, so nothing is uploaded.
- Still open: reopen the same PDFs automatically after a reload, link a PDF page to a node.

**Step 12: Choose which nodes are flashcards** (DONE)
- **🃏 Flashcard: on / 🚫 off** button in the side panel per node (not for the root or the weeks).
  Stored as a `flashcard` column/field (default on; old databases get the column added on
  start), undoable, exported to JSON. Excluded nodes are faded in the tree and skipped in study.

**Step 13: Week colours** (DONE)
- Fixed: weeks after the 8th were grey (style rules only existed for 8 weeks). Colours are now
  computed per node and sent with the graph data, so any number of weeks works.
- Click a week to pick its colour (16 swatches, Automatic, or any `#rrggbb`); stored as a
  `color` column/field, undoable, exported to JSON only when chosen. Text turns dark on light
  colours.

**Step 14: Practice exam questions** (DONE)
- `/exam/` page (third Dash app on the server, **📝 Exam** button). Sections Week 1–7, 10,
  11, 12; open/close per section; questions and solutions in Markdown with live preview;
  solutions behind "Show solution"; edit and delete with confirmation.
- Stored per tree in `exam_sections` / `exam_questions` tables; exported to
  `data/trees/exams/<slug>.json` and re-imported into an empty database.

## 5. Day-to-day content workflow (once the app works)

1. Activate the venv, run `python -m app.main`, open http://127.0.0.1:8050.
2. After a lecture: pick the week node, press `+`, add each concept with a definition.
3. Add sub-concepts under those the same way.
4. Everything saves to the tree's `.db` immediately. To keep a versioned copy, run
   `python -m app.export_json` and then
   `git add data/trees data/images; git commit -m "Add week 2"`.
   (Careful: if a `.db` is deleted, the app re-seeds it from its `.json`, so anything
   not exported is lost.)
5. For another course, press **+ New tree** and repeat from step 2.

## 6. Decisions

- **Top-level shape:** one root `ELEC5622` with a child per week.
- **Layout:** top-down hierarchy.
- **Storage:** one SQLite database per tree, with a JSON snapshot next to it for git.
- **Definition format:** Markdown with `$math$`.
- **Content source:** you supply LaTeX notes and Claude converts them into nodes.

## 7. Environment notes

- Python 3.11.9 in `.venv/`. Installed: dash 4.4.1, dash-cytoscape 1.0.2,
  pydantic 2.14.1, pytest 9.1.1 (pinned in `requirements.txt`).
- Plain `pip install` failed here with `CERTIFICATE_VERIFY_FAILED`; using
  `--use-feature=truststore` fixed it (see README). Don't use `--trusted-host`, which
  turns off certificate checks.
- The project is inside OneDrive, which will try to sync the thousands of files in
  `.venv/`. Consider excluding `.venv` from OneDrive sync, or moving the project out of it.
