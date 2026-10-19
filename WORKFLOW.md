# Workflow: Interactive ELEC5622 course tree

Goal: a big zoomable tree of the course. Click a node to see its definition. Add new
children (with explanations) from the UI. Nothing is coded yet; this is the plan.

## 1. Stack (and why)

| Piece | Choice | Why |
|---|---|---|
| UI framework | **Dash** | Pure Python, runs a local web app, no JavaScript needed |
| Tree widget | **dash-cytoscape** | Built-in zoom/pan, click events, tree layouts, styling |
| Storage | **`data/tree.json`** | Human-readable, tracked in git, easy to hand-edit or diff |
| Validation | **pydantic** | Catches malformed nodes before they corrupt the file |
| Tests | **pytest** | Tree logic (add/edit/delete/load/save) is testable without a browser |

Alternatives rejected: `pyvis` (hard to edit interactively), Streamlit (reruns the whole
script on each click, awkward for graph interaction), plain D3 (needs JavaScript).

## 2. Data model

One JSON file, a nested tree. Every node has a stable id so edits and deletes are safe.

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
`definition` free text (shown in the side panel); `children` may be empty.
Optional later: `week`, `tags`, `source` (slide/page reference), `collapsed`.

## 3. Proposed project layout

```
InteractiveELEC5622/
├── app/
│   ├── main.py        # creates the Dash app, runs the server
│   ├── layout.py      # page layout: graph on the left, detail panel on the right
│   ├── callbacks.py   # click, add, edit, delete handlers
│   ├── tree.py        # pure tree logic: find/add/edit/delete node, ids, to-cytoscape
│   ├── storage.py     # load/save tree.json, backup before save
│   └── styles.py      # cytoscape stylesheet (colours per depth, sizes)
├── data/
│   └── tree.json      # the course content (committed)
├── tests/
│   ├── test_tree.py
│   └── test_storage.py
├── requirements.txt
├── WORKFLOW.md
└── README.md
```

`tree.py` and `storage.py` have no Dash imports, so they can be tested alone.

## 4. Build steps

Each step ends with something you can run or test. Commit after each one.

**Step 1: Data + logic (no UI)**
- Define the pydantic `Node` model and write `tree.py`: `find`, `add_child`, `update`,
  `delete`, `generate_id`, `flatten_to_elements` (nested JSON → cytoscape nodes + edges).
- Write `storage.py`: load, validate, save atomically (write temp file then rename),
  copy the old file to `data/backups/` first.
- Tests: add/delete/edit, duplicate ids rejected, round-trip load/save.
- Done when: `python -m pytest` passes.

**Step 2: Seed content for Week 1**
- Write `data/tree.json` with the root, Week 1 "Introduction", and its six children:
  Anatomical imaging, Functional imaging, Purpose of medical imaging, DICOM format,
  Body planes, Efficiency of predictive modelling.
- Give each of those their own children and definitions (see section 6).
- Done when: the file validates and loads in a test.

**Step 3: Read-only viewer**
- `main.py` + `layout.py`: render the tree with cytoscape, using a top-down (dagre) or
  radial layout. Mouse-wheel zoom, drag to pan, drag nodes.
- Done when: the whole Week 1 tree shows and zooms anywhere.

**Step 4: Click to see the definition**
- Callback on `tapNodeData`: show the node's label, definition, path from root
  (e.g. ELEC5622 › Week 1 › Anatomical imaging) and children list in a side panel.
- Highlight the selected node and its direct neighbours.
- Done when: clicking "Anatomical imaging" shows its definition.

**Step 5: Add children with the `+`**
- When a node is selected, show a small `+` ghost node attached to it (a canvas can't
  hold real buttons, so a styled clickable node does the job).
- Clicking `+` opens a form in the side panel: label + definition, then **Add**.
- Callback: `tree.add_child` → `storage.save` → refresh elements → select the new node.
- Done when: you can add a child and it is still there after restarting the app.

**Step 6: Edit and delete**
- Edit button in the panel to change label/definition. Delete with a confirm dialog
  (warn how many descendants go with it). Root cannot be deleted.

**Step 7: Usability for a big tree**
- Collapse/expand a subtree (double-click). Search box that zooms to a matching node.
- Fit-to-screen button. Colour per week / depth. Layout selector.
- Add Week 2, 3, … as you go through the course.

**Step 8: Polish (optional)**
- Markdown (and LaTeX) in definitions, image attachments per node, export to PNG/HTML,
  import from an outline text file.

## 5. Day-to-day content workflow (once the app works)

1. Activate the venv, run `python -m app.main`, open http://127.0.0.1:8050.
2. After a lecture: pick the week node, press `+`, add each concept with a definition.
3. Add sub-concepts under those the same way.
4. Commit `data/tree.json` with the week in the message (`git commit -m "Add week 2"`).
   Git history is your undo for content.

## 6. Open questions to decide before coding

- **Top-level shape:** one root `ELEC5622` with a child per week (recommended, one big
  tree), or a separate tree per week with a dropdown to switch?
- **Layout:** top-down hierarchy (easy to read, wide) or radial (compact, good for zoom)?
- **Content source:** do you want to type definitions yourself, or should Claude draft
  them from your lecture slides (put the PDFs in a `source/` folder)?
- **Definition format:** plain text, or Markdown with formulas?

## 7. Environment notes

- Python 3.11.9 in `.venv/`. Installed: dash 4.4.1, dash-cytoscape 1.0.2,
  pydantic 2.14.1, pytest 9.1.1 (pinned in `requirements.txt`).
- Plain `pip install` failed here with `CERTIFICATE_VERIFY_FAILED`; using
  `--use-feature=truststore` fixed it (see README). Don't use `--trusted-host`, which
  turns off certificate checks.
- The project is inside OneDrive, which will try to sync the thousands of files in
  `.venv/`. Consider excluding `.venv` from OneDrive sync, or moving the project out of it.
