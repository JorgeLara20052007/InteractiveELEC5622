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

## Data

Changes are saved straight into the SQLite database `data/tree.db` (created on first run
from `data/seed.json`, not committed). To save a versioned copy:

```powershell
python -m app.export_json
git add data/seed.json
git commit -m "Update course tree"
```

## Test

```powershell
python -m pytest
```
