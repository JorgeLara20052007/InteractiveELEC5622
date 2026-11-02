# InteractiveELEC5622

Interactive, zoomable tree of the ELEC5622 course content. Click a node to read its
definition; use `+` to add new child nodes. See [WORKFLOW.md](WORKFLOW.md) for the plan.

## Setup (Windows, PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --use-feature=truststore --upgrade pip
python -m pip install -r requirements.txt
```

`--use-feature=truststore` makes pip use the Windows certificate store. It was needed on
this machine because plain pip failed with `CERTIFICATE_VERIFY_FAILED` (a network or
antivirus proxy re-signs HTTPS traffic).

## Run

```powershell
python -m app.main
```
Then open http://127.0.0.1:8050. Scroll to zoom, drag to pan, click a node to read its
definition. Select a node and click the yellow `+` next to it (or "+ Add child") to add
a child; use Edit and Delete in the side panel. "Collapse" / "Expand" hide or show the
selected node's subtree (also "Collapse all" / "Expand all" above the graph), the search
box jumps to any node, and each week has its own colour.

- **Resize the side panel:** drag the grey bar between the tree and the panel to give
  the label/definition editor more room (or the tree). The width is remembered; double-click
  the bar to go back to the default. The definition box can also be made taller by dragging
  its bottom-right corner.
- **Undo / redo:** the Undo and Redo buttons (or Ctrl+Z / Ctrl+Y) revert or re-apply adding,
  editing and deleting nodes, including a whole deleted subtree. The history is kept in the
  database (last 200 changes), so it survives restarting the app. In a text box Ctrl+Z
  keeps undoing your typing instead.
- **Images:** while editing a definition, paste a screenshot into the text box, or drop a
  file on the "Add an image" area (PNG, JPEG, GIF or WebP, up to 10 MB). It is inserted as
  Markdown (`![caption](/images/...)`) and shown in a live preview. Click a picture in a
  definition to open it full size. Pictures are stored in `data/images/`.

## Study mode (flashcards)

Press **📚 Study** in the toolbar (or open http://127.0.0.1:8050/study/). It opens in its own
window, so you can keep the tree open next to it.

1. Pick the tree and the week (the weeks are the root's direct children).
2. A random concept from that week appears as a card with just its title.
3. Click the card (or press Space) to see the definition, then mark yourself:
   **✓ I knew it** (→ or Y) or **✗ I didn't know it** (← or N). The next random card follows.
4. After the last card you get your score, the list of concepts you missed, and buttons to
   retry only those or start again.

Tick **Include sub-concepts** to be tested on every level below the week, not just its
direct children. Study mode only reads the tree; it never changes it.

## Several trees (one per course)

The dropdown at the top left switches between trees, and **+ New tree** starts a completely
separate one (type a name, press Create). Every tree has its own database and its own JSON
file in `data/trees/`:

```
data/trees/elec5622.db     live database + undo history (not committed)
data/trees/elec5622.json   snapshot of the tree (committed)
```

Creating a tree writes its `.json` straight away (just the root node). The app remembers
which tree you were looking at. Undo history is kept per tree. Pictures in `data/images/`
are shared by all trees.

## Data

Changes are saved straight into the tree's SQLite database. The JSON snapshots are only
updated when you export, so to save a versioned copy of every tree:

```powershell
python -m app.export_json
git add data/trees data/images
git commit -m "Update course trees"
```

`data/images/` is committed too, because definitions refer to those files. On a fresh
clone the databases are rebuilt from the JSON files the first time the app starts.
