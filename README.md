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

- **Undo / redo:** the Undo and Redo buttons (or Ctrl+Z / Ctrl+Y) revert or re-apply adding,
  editing and deleting nodes, including a whole deleted subtree. The history is kept in the
  database (last 200 changes), so it survives restarting the app. In a text box Ctrl+Z
  keeps undoing your typing instead.
- **Images:** while editing a definition, paste a screenshot into the text box, or drop a
  file on the "Add an image" area (PNG, JPEG, GIF or WebP, up to 10 MB). It is inserted as
  Markdown (`![caption](/images/...)`) and shown in a live preview. Click a picture in a
  definition to open it full size. Pictures are stored in `data/images/`.

## Data

Changes are saved straight into the SQLite database `data/tree.db` (created on first run
from `data/seed.json`, not committed). To save a versioned copy:

```powershell
python -m app.export_json
git add data/seed.json data/images
git commit -m "Update course tree"
```

`data/images/` is committed too, because definitions in `seed.json` refer to those files.

## Test

```powershell
python -m pytest
```
