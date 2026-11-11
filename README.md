# Course Tree (InteractiveELEC5622)

An interactive, zoomable tree of course notes, built for ELEC5622 and usable for any course.
Each week is a branch, each concept a node with a definition (Markdown, formulas and
pictures), and every node can be studied as a flashcard.

- **[SETUP.md](SETUP.md)**: install and run it on your own computer.
- **[USAGE.md](USAGE.md)**: how to use the app.
- [WORKFLOW.md](WORKFLOW.md): how it was designed and built, step by step.

## What it does

- Zoom and pan around the whole course; click a node to read its definition.
- Add, edit and delete nodes from the page (the yellow **+** adds a child), with a live
  preview, LaTeX formulas, and pictures you can paste in.
- Search, collapse branches, and pick a colour for each week.
- Undo / redo every change (Ctrl+Z / Ctrl+Y), even after a restart.
- **Study mode:** shuffled flashcards per week, self-marking, a score at the end and a retry
  of the ones you missed. Choose which nodes are flashcards.
- **Practice exam questions:** sections per week with questions and hidden solutions, written
  in Markdown.
- Floating, resizable PDF windows to read your slides while taking notes.
- Several trees, one per course.

## Quick start

```bash
git clone https://github.com/<your-account>/InteractiveELEC5622.git
cd InteractiveELEC5622
python -m venv .venv
.venv\Scripts\activate            # macOS / Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m app.main
```

Open **http://127.0.0.1:8050**. Details and troubleshooting are in [SETUP.md](SETUP.md).

## Project layout

```
app/          Python code: tree logic, SQLite storage, Dash pages and callbacks
assets/       browser-side scripts and styles (shortcuts, PDF windows, panel splitter)
data/trees/   one <name>.json per tree (committed) and its <name>.db database (local only)
data/images/  pictures used in definitions
tests/        pytest tests (python -m pytest)
```

Built with [Dash](https://dash.plotly.com/) and
[dash-cytoscape](https://dash.plotly.com/cytoscape).
