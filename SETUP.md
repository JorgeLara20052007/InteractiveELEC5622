# Setting up Course Tree on your own computer

This gets the app running on a new computer. It takes about five minutes. For how to use the
app once it is running, see [USAGE.md](USAGE.md).

## 1. What you need

- **Python 3.10 or newer** (tested with 3.11). Check with `python --version`.
  Windows: install from [python.org](https://www.python.org/downloads/) and tick
  "Add python.exe to PATH" in the installer.
- **Git**, to download the project and keep it up to date. Check with `git --version`.
  Windows: [git-scm.com](https://git-scm.com/download/win).
- A web browser (Chrome or Edge recommended, since the PDF windows use the browser's own
  PDF viewer).

## 2. Download the project

```bash
git clone https://github.com/<your-account>/InteractiveELEC5622.git
cd InteractiveELEC5622
```

Replace `<your-account>` with the GitHub account the repository lives in. If the
repository is private, Git will ask you to sign in to GitHub the first time.

> **Tip:** avoid putting the project inside a OneDrive, iCloud or Dropbox folder. Those
> services can move the many small files of the Python environment back to the cloud, which
> makes the app load slowly or show a page stuck on "Loading...".

## 3. Create the Python environment and install the packages

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell refuses to run `Activate.ps1`, run this once and try again:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

**macOS / Linux (Terminal):**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The packages are Dash (the web app), dash-cytoscape (the tree drawing), pydantic (data
checks) and pytest (tests).

### If pip fails with `CERTIFICATE_VERIFY_FAILED`

Some university networks and antivirus programs re-sign secure web traffic, so pip cannot
verify PyPI. Tell pip to trust your computer's own certificate store instead:

```powershell
python -m pip install --use-feature=truststore --upgrade pip
python -m pip install --use-feature=truststore -r requirements.txt
```

Do **not** use `--trusted-host`; that switches certificate checking off completely.

## 4. Start the app

With the environment active (you see `(.venv)` at the start of the prompt):

```bash
python -m app.main
```

Then open **http://127.0.0.1:8050** in your browser. Stop the app with `Ctrl+C` in the
terminal.

Next time you only need to open a terminal in the project folder, activate the environment
(`.\.venv\Scripts\Activate.ps1` or `source .venv/bin/activate`) and run `python -m app.main`.

**First start:** the trees in `data/trees/*.json` are copied into local databases
(`data/trees/*.db`). From then on the app reads and writes those databases.

**Port already in use?** Another program (or a second copy of the app) is on port 8050.
Close it, or start the app on another port:

```powershell
$env:PORT = "8060"; python -m app.main      # Windows PowerShell
PORT=8060 python -m app.main                # macOS / Linux
```

## 5. Check everything works (optional)

```bash
python -m pytest
```

All tests should pass.

## 6. Moving your notes between computers

Your edits are saved in the local database files (`data/trees/*.db`), which are **not**
uploaded to GitHub. The `.json` files next to them are the shareable copy. To carry your
notes to another computer:

**On the computer where you made the changes:**

```bash
python -m app.export_json          # writes every tree's database into its .json file
git add data/trees data/images
git commit -m "Update course notes"
git push
```

**On the other computer:**

```bash
git pull
```

Then, because a database that already exists is never overwritten automatically, delete the
local database of each tree you want to refresh **while the app is stopped**, and start the
app again. It rebuilds the database from the new `.json`:

```powershell
Remove-Item data\trees\elec5622.db      # Windows PowerShell
rm data/trees/elec5622.db               # macOS / Linux
```

Only do this if that computer has no unexported changes of its own: deleting the database
discards them and its undo history.

## Troubleshooting

| Problem | What to do |
|---|---|
| `python` is not recognised | Reinstall Python with "Add to PATH" ticked, or use `py` instead of `python` on Windows. |
| The page stays on "Loading..." or a definition is blank | Reload the page. If it keeps happening, move the project out of OneDrive, or add an exception for `localhost` in your antivirus's web protection. |
| `ModuleNotFoundError: No module named 'dash'` | The environment is not active. Run the activate command from step 3 first. |
| I deleted something by mistake | Press Ctrl+Z (or Undo) in the app. The last 200 changes per tree can be undone, even after a restart. |
